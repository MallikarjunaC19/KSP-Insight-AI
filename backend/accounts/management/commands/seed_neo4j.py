"""
KSP Insight AI — Seed the Neo4j graph from PostgreSQL data
Location: accounts/management/commands/seed_neo4j.py

Usage:
    python manage.py seed_neo4j

Run this AFTER `python manage.py seed_data` — it reads Person, Vehicle,
InvestigationCase, VehicleOwnership, and PersonCaseRole from PostgreSQL
and mirrors the relevant entities/relationships into Neo4j.

Nodes created:
    Person(id, name)
    Vehicle(id, registration_number)
    InvestigationCase(id, case_number)

Relationships created:
    (Person)-[:OWNS]->(Vehicle)              from VehicleOwnership
    (Person)-[:SUSPECT_IN]->(Case)           from PersonCaseRole role=SUSPECT
    (Person)-[:VICTIM_IN]->(Case)            from PersonCaseRole role=VICTIM
    (Person)-[:WITNESS_IN]->(Case)           from PersonCaseRole role=WITNESS
    (Person)-[:COMPLAINANT_IN]->(Case)       from PersonCaseRole role=COMPLAINANT
    (Person)-[:ASSOCIATED_WITH]->(Person)    derived: people linked to the same case

Note: Postgres UUIDs are stored as the Neo4j node's `pg_id` property,
so you can always join back to the source-of-truth record in Postgres
by that ID — Neo4j only stores what's needed for graph traversal
(names, labels, relationship types), not full record details.

Idempotent: uses MERGE (Cypher's get-or-create) throughout, safe to
re-run after adding more Postgres data.
"""

from django.core.management.base import BaseCommand
from accounts.neo4j_client import get_driver

from persons.models import Person, PersonCaseRole
from assets.models import VehicleOwnership
from investigations.models import InvestigationCase


ROLE_TO_RELATIONSHIP = {
    PersonCaseRole.Role.SUSPECT: "SUSPECT_IN",
    PersonCaseRole.Role.VICTIM: "VICTIM_IN",
    PersonCaseRole.Role.WITNESS: "WITNESS_IN",
    PersonCaseRole.Role.ACCUSED: "ACCUSED_IN",
    PersonCaseRole.Role.COMPLAINANT: "COMPLAINANT_IN",
}


class Command(BaseCommand):
    help = "Seed the Neo4j graph database from existing PostgreSQL data"

    def handle(self, *args, **options):
        driver = get_driver()
        with driver.session() as session:
            self.stdout.write("Creating Person nodes...")
            self.seed_person_nodes(session)

            self.stdout.write("Creating Vehicle nodes...")
            self.seed_vehicle_nodes(session)

            self.stdout.write("Creating InvestigationCase nodes...")
            self.seed_case_nodes(session)

            self.stdout.write("Creating OWNS relationships...")
            self.seed_ownership_relationships(session)

            self.stdout.write("Creating case-role relationships...")
            self.seed_case_role_relationships(session)

            self.stdout.write("Deriving ASSOCIATED_WITH relationships...")
            self.seed_associated_with(session)

        self.stdout.write(self.style.SUCCESS("Neo4j graph seeded successfully."))

    def seed_person_nodes(self, session):
        for person in Person.objects.all():
            session.run(
                """
                MERGE (p:Person {pg_id: $pg_id})
                SET p.name = $name
                """,
                pg_id=str(person.id),
                name=f"{person.first_name} {person.last_name}".strip(),
            )

    def seed_vehicle_nodes(self, session):
        for vehicle in VehicleOwnership.objects.select_related("vehicle").values(
            "vehicle__id", "vehicle__registration_number"
        ).distinct():
            session.run(
                """
                MERGE (v:Vehicle {pg_id: $pg_id})
                SET v.registration_number = $reg
                """,
                pg_id=str(vehicle["vehicle__id"]),
                reg=vehicle["vehicle__registration_number"],
            )

    def seed_case_nodes(self, session):
        for case in InvestigationCase.objects.select_related("fir__police_station"):
            session.run(
                """
                MERGE (c:InvestigationCase {pg_id: $pg_id})
                SET c.case_number = $case_number,
                    c.status = $status,
                    c.station_code = $station_code,
                    c.district = $district
                """,
                pg_id=str(case.id),
                case_number=case.case_number,
                status=case.status,
                station_code=case.fir.police_station.code,
                district=case.fir.police_station.district,
            )

    def seed_ownership_relationships(self, session):
        for ownership in VehicleOwnership.objects.select_related("owner", "vehicle"):
            session.run(
                """
                MATCH (p:Person {pg_id: $owner_id})
                MATCH (v:Vehicle {pg_id: $vehicle_id})
                MERGE (p)-[:OWNS]->(v)
                """,
                owner_id=str(ownership.owner_id),
                vehicle_id=str(ownership.vehicle_id),
            )

    def seed_case_role_relationships(self, session):
        for role_entry in PersonCaseRole.objects.select_related("person", "case"):
            rel_type = ROLE_TO_RELATIONSHIP.get(role_entry.role)
            if not rel_type:
                continue
            session.run(
                f"""
                MATCH (p:Person {{pg_id: $person_id}})
                MATCH (c:InvestigationCase {{pg_id: $case_id}})
                MERGE (p)-[:{rel_type}]->(c)
                """,
                person_id=str(role_entry.person_id),
                case_id=str(role_entry.case_id),
            )

    def seed_associated_with(self, session):
        """
        Two people sharing the same InvestigationCase are considered
        associated. Each relationship carries the case that created it
        (case_pg_id, station_code, district) — this is what lets
        graph_lookup templates filter out associations derived from a
        case outside the asking officer's scope, rather than exposing
        a bare "these two people are connected" fact with no way to
        check whether the officer is allowed to know why.

        MERGE keys on (person1, person2, case_pg_id) so two people who
        share multiple cases get one relationship per case, not a
        single relationship that collapses/loses the scope of either.
        """
        for case in InvestigationCase.objects.select_related("fir__police_station"):
            session.run(
                """
                MATCH (c:InvestigationCase {pg_id: $case_pg_id})<-[]-(p1:Person)
                MATCH (c)<-[]-(p2:Person)
                WHERE p1.pg_id < p2.pg_id
                MERGE (p1)-[r:ASSOCIATED_WITH {case_pg_id: $case_pg_id}]->(p2)
                SET r.station_code = $station_code, r.district = $district
                """,
                case_pg_id=str(case.id),
                station_code=case.fir.police_station.code,
                district=case.fir.police_station.district,
            )