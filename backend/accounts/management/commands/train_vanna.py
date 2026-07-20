"""
KSP Insight AI (KAVACH AI) — Train Vanna
App: accounts (management command)

Run ONCE (and again any time the schema changes meaningfully):

    python manage.py train_vanna

Feeds Vanna the DDL for every table sql_lookup is allowed to query,
plus documentation strings about business rules, plus a handful of
example question -> SQL pairs to bootstrap generation quality. This
trains the ChromaDB collection at VANNA_CHROMA_PATH — same path
get_vanna() reads from — so training persists across restarts and
doesn't need to be redone on every server start.

DDL below is simplified (column names/types for context, not a byte-
exact schema dump) — good enough for Vanna's embedding/retrieval
purposes. If you add/rename columns, update here too or generated SQL
quality will drift.
"""

from django.core.management.base import BaseCommand
from assistant.ai.vanna_client import get_vanna


DDL_STATEMENTS = [
    """CREATE TABLE police_station (
        id UUID PRIMARY KEY, name VARCHAR(150), code VARCHAR(20),
        department_id UUID, district VARCHAR(100), state VARCHAR(100)
    )""",
    """CREATE TABLE officer (
        id UUID PRIMARY KEY, badge_number VARCHAR(30), first_name VARCHAR(100),
        last_name VARCHAR(100), rank_id UUID, police_station_id UUID, role_id UUID,
        jurisdiction_district VARCHAR(100), is_active BOOLEAN
    )""",
    """CREATE TABLE crime_category (
        id UUID PRIMARY KEY, name VARCHAR(150), code_type VARCHAR(10),
        section_code VARCHAR(20), severity VARCHAR(10)
    )""",
    """CREATE TABLE crime (
        id UUID PRIMARY KEY, category_id UUID, police_station_id UUID, reported_by_id UUID,
        description TEXT, date_of_occurrence DATE, status VARCHAR(25)
    )""",
    """CREATE TABLE fir (
        id UUID PRIMARY KEY, fir_number VARCHAR(50), police_station_id UUID,
        registered_by_id UUID, complainant_name VARCHAR(150), date_filed TIMESTAMP,
        incident_date DATE, status VARCHAR(25)
    )""",
    """CREATE TABLE investigation_case (
        id UUID PRIMARY KEY, case_number VARCHAR(50), fir_id UUID, lead_officer_id UUID,
        status VARCHAR(25), priority VARCHAR(10), opened_date DATE, closed_date DATE
    )""",
    """CREATE TABLE investigation (
        id UUID PRIMARY KEY, case_id UUID, officer_id UUID, start_date DATE,
        end_date DATE, status VARCHAR(15)
    )""",
    """CREATE TABLE investigation_step (
        id UUID PRIMARY KEY, investigation_id UUID, description TEXT,
        performed_by_id UUID, step_date TIMESTAMP
    )""",
    """CREATE TABLE arrest (
        id UUID PRIMARY KEY, case_id UUID, arresting_officer_id UUID,
        arrested_person_name VARCHAR(150), arrest_date TIMESTAMP
    )""",
    """CREATE TABLE chargesheet (
        id UUID PRIMARY KEY, case_id UUID, filed_by_id UUID, filing_date DATE,
        status VARCHAR(10)
    )""",
    """CREATE TABLE court_case (
        id UUID PRIMARY KEY, chargesheet_id UUID, court_case_number VARCHAR(50),
        status VARCHAR(20), next_hearing_date DATE
    )""",
    """CREATE TABLE person_case_role (
        id UUID PRIMARY KEY, person_id UUID, case_id UUID, role VARCHAR(15), added_by_id UUID
    )""",
]

DOCUMENTATION = [
    "Every table with a police_station_id (or a chain leading to one via "
    "fir_id/case_id/investigation_id/chargesheet_id) is access-controlled by "
    "officer role and station/district. Generated SQL for this system will "
    "be automatically re-scoped after generation — you do not need to add "
    "your own WHERE clauses for station/district filtering.",
    "status columns use specific enum-like string values, e.g. crime.status "
    "is one of REPORTED, UNDER_INVESTIGATION, CHARGESHEET_FILED, CLOSED. "
    "investigation_case.status is one of OPEN, UNDER_INVESTIGATION, "
    "CHARGESHEET_FILED, IN_COURT, CLOSED, DROPPED.",
    "case_number on investigation_case looks like 'CR-2026-00123'. "
    "fir_number on fir looks like '0123/2026'.",
]

EXAMPLE_QUESTION_SQL_PAIRS = [
    (
        "How many FIRs were filed this month?",
        "SELECT COUNT(*) FROM fir WHERE date_filed >= date_trunc('month', CURRENT_DATE)",
    ),
    (
        "List all open investigation cases",
        "SELECT case_number, status, priority, opened_date FROM investigation_case WHERE status IN ('OPEN', 'UNDER_INVESTIGATION') ORDER BY opened_date DESC",
    ),
    (
        "How many crimes were reported by category this year?",
        "SELECT cc.name, COUNT(*) FROM crime c JOIN crime_category cc ON cc.id = c.category_id "
        "WHERE c.date_of_occurrence >= date_trunc('year', CURRENT_DATE) GROUP BY cc.name ORDER BY COUNT(*) DESC",
    ),
]


class Command(BaseCommand):
    help = "Trains Vanna's ChromaDB collection on the schema + business documentation (run once)."

    def handle(self, *args, **options):
        vn = get_vanna()

        for ddl in DDL_STATEMENTS:
            vn.train(ddl=ddl)
        self.stdout.write(f"Trained {len(DDL_STATEMENTS)} DDL statements.")

        for doc in DOCUMENTATION:
            vn.train(documentation=doc)
        self.stdout.write(f"Trained {len(DOCUMENTATION)} documentation strings.")

        for question, sql in EXAMPLE_QUESTION_SQL_PAIRS:
            vn.train(question=question, sql=sql)
        self.stdout.write(f"Trained {len(EXAMPLE_QUESTION_SQL_PAIRS)} example question/SQL pairs.")

        self.stdout.write(self.style.SUCCESS("Vanna training complete."))