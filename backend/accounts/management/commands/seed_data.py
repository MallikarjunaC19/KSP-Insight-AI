"""
KSP Insight AI — Full demo data seed script (expanded)   
"""

import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from accounts.models import Role, Department, Rank, PoliceStation, Officer
from crimes.models import CrimeCategory, Crime, FIR, FIRCrime
from investigations.models import (
    InvestigationCase, Investigation, InvestigationStep, Arrest, Chargesheet, CourtCase
)
from persons.models import Person, PersonCaseRole, Phone, Email, Address
from assets.models import Vehicle, VehicleOwnership, Property, Weapon
from assistant.models import Conversation, ChatMessage, AuditLog, PredictionHistory, GeneratedReport


class Command(BaseCommand):
    help = "Seed realistic demo data across all 6 modules for KSP Insight AI"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding accounts...")
        roles = self.seed_roles()
        departments = self.seed_departments()
        ranks = self.seed_ranks()
        stations = self.seed_stations()
        officers = self.seed_officers(roles, departments, ranks, stations)

        self.stdout.write("Seeding crimes...")
        categories = self.seed_crime_categories()
        crimes = self.seed_crimes(categories, stations, officers)
        firs = self.seed_firs(stations, officers)
        self.seed_fir_crimes(firs, crimes)

        self.stdout.write("Seeding investigations...")
        cases = self.seed_cases(firs, officers)
        investigations = self.seed_investigation_phases(cases, officers)
        self.seed_investigation_steps(investigations, officers)
        self.seed_arrests(cases, officers)
        chargesheets = self.seed_chargesheets(cases, officers)
        self.seed_court_cases(chargesheets)

        self.stdout.write("Seeding persons...")
        people = self.seed_persons()
        self.seed_person_case_roles(people, cases, officers)
        self.seed_contact_details(people)

        self.stdout.write("Seeding assets...")
        self.seed_assets(people, cases)

        self.stdout.write("Seeding assistant (AI)...")
        self.seed_assistant_data(officers, cases)

        self.print_summary(officers)

    # ------------------------------------------------------------------
    # accounts
    # ------------------------------------------------------------------
    def seed_roles(self):
        data = [
            (Role.RoleCode.CONSTABLE, "Frontline officer, station-level access only"),
            (Role.RoleCode.STATION_OFFICER, "In-charge of a police station, full CRUD within it"),
            (Role.RoleCode.SP_DIG, "District-level oversight, full CRUD within district"),
            (Role.RoleCode.DGP, "State-wide access, full CRUD"),
            (Role.RoleCode.SCRB_ANALYST, "State-wide read-only access for analytics"),
        ]
        roles = {}
        for code, desc in data:
            role, _ = Role.objects.get_or_create(name=code, defaults={"description": desc})
            roles[code] = role
        return roles

    def seed_departments(self):
        data = [
            ("Crime Branch", "CRB"),
            ("Cyber Cell", "CYB"),
            ("Traffic Police", "TRF"),
            ("Law & Order", "L&O"),
            ("Narcotics Control", "NCB"),
        ]
        depts = {}
        for name, code in data:
            dept, _ = Department.objects.get_or_create(code=code, defaults={"name": name})
            depts[code] = dept
        return depts

    def seed_ranks(self):
        data = [
            ("Constable", 10), ("Head Constable", 9), ("Assistant Sub-Inspector", 8),
            ("Sub-Inspector", 7), ("Inspector", 6), ("Deputy Superintendent of Police", 5),
            ("Superintendent of Police", 4), ("Deputy Inspector General", 3),
            ("Inspector General", 2), ("Director General of Police", 1),
        ]
        ranks = {}
        for name, level in data:
            rank, _ = Rank.objects.get_or_create(name=name, defaults={"hierarchy_level": level})
            ranks[name] = rank
        return ranks

    def seed_stations(self):
        data = [
            ("Cubbon Park PS", "CUB01", "Bengaluru Urban", 12.976, 77.592),
            ("Whitefield PS", "WHF01", "Bengaluru Urban", 12.969, 77.749),
            ("Koramangala PS", "KOR01", "Bengaluru Urban", 12.935, 77.624),
            ("Mysuru City PS", "MYS01", "Mysuru", 12.295, 76.639),
            ("Mysuru Devaraja PS", "MYS02", "Mysuru", 12.307, 76.655),
            ("Mangaluru North PS", "MNG01", "Dakshina Kannada", 12.914, 74.856),
            ("Hubballi PS", "HUB01", "Dharwad", 15.364, 75.124),
            ("Belagavi PS", "BEL01", "Belagavi", 15.852, 74.499),
        ]
        stations = {}
        for name, code, district, lat, lng in data:
            station, _ = PoliceStation.objects.get_or_create(
                code=code,
                defaults={"name": name, "district": district, "latitude": lat, "longitude": lng},
            )
            stations[code] = station
        return stations

    def seed_officers(self, roles, departments, ranks, stations):
        data = [
            ("constable_ravi", "KSP-1001", "Ravi", "Kumar", "Constable", "L&O", "CUB01",
             Role.RoleCode.CONSTABLE, "", "Pass@1234"),
            ("constable_deepa", "KSP-1006", "Deepa", "Naik", "Head Constable", "L&O", "KOR01",
             Role.RoleCode.CONSTABLE, "", "Pass@1234"),
            ("constable_manju", "KSP-1007", "Manjunath", "Gowda", "Constable", "L&O", "MYS01",
             Role.RoleCode.CONSTABLE, "", "Pass@1234"),
            ("so_meena", "KSP-1002", "Meena", "Shetty", "Inspector", "L&O", "CUB01",
             Role.RoleCode.STATION_OFFICER, "", "Pass@1234"),
            ("so_kiran", "KSP-1008", "Kiran", "Poojary", "Inspector", "L&O", "WHF01",
             Role.RoleCode.STATION_OFFICER, "", "Pass@1234"),
            ("so_anitha", "KSP-1009", "Anitha", "Hegde", "Sub-Inspector", "L&O", "MNG01",
             Role.RoleCode.STATION_OFFICER, "", "Pass@1234"),
            ("spdig_arjun", "KSP-1003", "Arjun", "Rao", "Superintendent of Police", "CRB", "CUB01",
             Role.RoleCode.SP_DIG, "Bengaluru Urban", "Pass@1234"),
            ("spdig_farhan", "KSP-1010", "Farhan", "Khan", "Deputy Inspector General", "CRB", "MYS01",
             Role.RoleCode.SP_DIG, "Mysuru", "Pass@1234"),
            ("dgp_lakshmi", "KSP-1004", "Lakshmi", "Nair", "Director General of Police", "L&O", "MYS01",
             Role.RoleCode.DGP, "", "Pass@1234"),
            ("analyst_suresh", "KSP-1005", "Suresh", "Bhat", "Inspector", "CRB", "MNG01",
             Role.RoleCode.SCRB_ANALYST, "", "Pass@1234"),
        ]
        officers = {}
        officers_by_username = {}
        for username, badge, first, last, rank_name, dept_code, station_code, role_code, district, pwd in data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@ksp.gov.in", "is_staff": True},
            )
            if created:
                user.set_password(pwd)
                user.save()
            officer, _ = Officer.objects.get_or_create(
                badge_number=badge,
                defaults={
                    "user": user,
                    "first_name": first,
                    "last_name": last,
                    "rank": ranks[rank_name],
                    "department": departments[dept_code],
                    "police_station": stations[station_code],
                    "role": roles[role_code],
                    "jurisdiction_district": district,
                    "phone": "9876543210",
                    "email": f"{username}@ksp.gov.in",
                    "date_of_joining": datetime.date(2020, 1, 1),
                },
            )
            officers_by_username[username] = officer
            officers.setdefault(role_code, officer)
        officers["_by_username"] = officers_by_username
        return officers

    # ------------------------------------------------------------------
    # crimes
    # ------------------------------------------------------------------
    def seed_crime_categories(self):
        data = [
            ("Theft", "BNS", "Section 303", CrimeCategory.Severity.MODERATE),
            ("Cyber Fraud", "IT_ACT", "Section 66D", CrimeCategory.Severity.SEVERE),
            ("Assault", "BNS", "Section 115", CrimeCategory.Severity.MODERATE),
            ("Robbery", "BNS", "Section 309", CrimeCategory.Severity.SEVERE),
            ("Cheating", "BNS", "Section 318", CrimeCategory.Severity.MINOR),
            ("Kidnapping", "BNS", "Section 137", CrimeCategory.Severity.HEINOUS),
            ("Drug Offence", "OTHER", "NDPS Section 20", CrimeCategory.Severity.SEVERE),
            ("Domestic Violence", "BNS", "Section 85", CrimeCategory.Severity.MODERATE),
            ("Extortion", "BNS", "Section 308", CrimeCategory.Severity.SEVERE),
            ("House Burglary", "BNS", "Section 305", CrimeCategory.Severity.MODERATE),
        ]
        cats = {}
        for name, code_type, section, severity in data:
            cat, _ = CrimeCategory.objects.get_or_create(
                name=name,
                defaults={"code_type": code_type, "section_code": section, "severity": severity},
            )
            cats[name] = cat
        return cats

    def seed_crimes(self, categories, stations, officers):
        by_user = officers["_by_username"]
        data = [
            ("Theft", "CUB01", by_user["constable_ravi"],
             "Mobile phone stolen near MG Road metro station", datetime.date(2026, 6, 1)),
            ("Cyber Fraud", "CUB01", by_user["so_meena"],
             "Victim lost money via fake investment app", datetime.date(2026, 6, 10)),
            ("Assault", "WHF01", by_user["so_kiran"],
             "Altercation outside a bar led to injuries", datetime.date(2026, 6, 15)),
            ("Robbery", "KOR01", by_user["constable_deepa"],
             "Armed robbery at a jewelry shop", datetime.date(2026, 6, 18)),
            ("Cheating", "MYS01", by_user["constable_manju"],
             "Fake job offer scam targeting job seekers", datetime.date(2026, 6, 20)),
            ("House Burglary", "MYS02", by_user["constable_manju"],
             "Burglary reported while family was on vacation", datetime.date(2026, 6, 22)),
            ("Drug Offence", "MNG01", by_user["so_anitha"],
             "Narcotics seized during a routine vehicle check", datetime.date(2026, 6, 25)),
            ("Domestic Violence", "HUB01", by_user["so_kiran"],
             "Neighbor reported ongoing domestic disturbance", datetime.date(2026, 6, 27)),
            ("Extortion", "BEL01", by_user["so_meena"],
             "Shop owner reports repeated extortion demands", datetime.date(2026, 6, 29)),
            ("Kidnapping", "CUB01", by_user["spdig_arjun"],
             "Child reported missing, suspected abduction", datetime.date(2026, 7, 1)),
        ]
        crimes = []
        for cat_name, station_code, officer, desc, date in data:
            crime, _ = Crime.objects.get_or_create(
                description=desc,
                defaults={
                    "category": categories[cat_name],
                    "police_station": stations[station_code],
                    "reported_by": officer,
                    "date_of_occurrence": date,
                    "status": Crime.Status.UNDER_INVESTIGATION,
                },
            )
            crimes.append(crime)
        return crimes

    def seed_firs(self, stations, officers):
        by_user = officers["_by_username"]
        data = [
            ("CUB/2026/0101", "CUB01", by_user["so_meena"], "Rekha Iyer", "9845012345",
             datetime.date(2026, 6, 1), "Near MG Road Metro Station",
             "Complainant reports mobile phone stolen from her bag while boarding the metro."),
            ("CUB/2026/0102", "CUB01", by_user["so_meena"], "Prakash Menon", "9845098765",
             datetime.date(2026, 6, 10), "Online",
             "Complainant transferred Rs. 2,50,000 to a fraudulent investment scheme."),
            ("WHF/2026/0201", "WHF01", by_user["so_kiran"], "Sunil Verma", "9845011122",
             datetime.date(2026, 6, 15), "Whitefield Main Road",
             "Complainant sustained injuries in an altercation outside a bar."),
            ("KOR/2026/0301", "KOR01", by_user["constable_deepa"], "Ganesh Jewellers", "9845033445",
             datetime.date(2026, 6, 18), "Koramangala 5th Block",
             "Armed robbery at jewelry shop, gold ornaments worth Rs. 15 lakhs stolen."),
            ("MYS/2026/0401", "MYS01", by_user["constable_manju"], "Deepak Rao", "9845055667",
             datetime.date(2026, 6, 20), "Mysuru city center",
             "Complainant lost Rs. 50,000 in a fake job placement scam."),
            ("CUB/2026/0103", "CUB01", by_user["spdig_arjun"], "Anita Reddy", "9845077889",
             datetime.date(2026, 7, 1), "Cubbon Park area",
             "Complainant's child went missing, suspected abduction."),
        ]
        firs = []
        for fir_number, station_code, officer, name, phone, incident_date, location, summary in data:
            fir, _ = FIR.objects.get_or_create(
                fir_number=fir_number,
                defaults={
                    "police_station": stations[station_code],
                    "registered_by": officer,
                    "complainant_name": name,
                    "complainant_phone": phone,
                    "incident_date": incident_date,
                    "incident_location": location,
                    "summary": summary,
                    "status": FIR.Status.UNDER_INVESTIGATION,
                },
            )
            firs.append(fir)
        return firs

    def seed_fir_crimes(self, firs, crimes):
        pairs = [
            (0, 0, True), (1, 1, True), (2, 2, True),
            (3, 3, True), (4, 4, True), (5, 9, True),
        ]
        for fir_idx, crime_idx, is_primary in pairs:
            FIRCrime.objects.get_or_create(
                fir=firs[fir_idx], crime=crimes[crime_idx],
                defaults={"is_primary_offense": is_primary},
            )

    # ------------------------------------------------------------------
    # investigations
    # ------------------------------------------------------------------
    def seed_cases(self, firs, officers):
        by_user = officers["_by_username"]
        data = [
            ("CR-2026-00101", firs[0], by_user["so_meena"],
             InvestigationCase.Status.UNDER_INVESTIGATION, InvestigationCase.Priority.MEDIUM),
            ("CR-2026-00102", firs[1], by_user["so_meena"],
             InvestigationCase.Status.UNDER_INVESTIGATION, InvestigationCase.Priority.HIGH),
            ("CR-2026-00103", firs[2], by_user["so_kiran"],
             InvestigationCase.Status.OPEN, InvestigationCase.Priority.LOW),
            ("CR-2026-00104", firs[3], by_user["constable_deepa"],
             InvestigationCase.Status.UNDER_INVESTIGATION, InvestigationCase.Priority.CRITICAL),
            ("CR-2026-00105", firs[4], by_user["constable_manju"],
             InvestigationCase.Status.OPEN, InvestigationCase.Priority.MEDIUM),
            ("CR-2026-00106", firs[5], by_user["spdig_arjun"],
             InvestigationCase.Status.UNDER_INVESTIGATION, InvestigationCase.Priority.CRITICAL),
        ]
        cases = []
        for case_number, fir, lead, status, priority in data:
            case, _ = InvestigationCase.objects.get_or_create(
                case_number=case_number,
                defaults={"fir": fir, "lead_officer": lead, "status": status, "priority": priority},
            )
            cases.append(case)
        return cases

    def seed_investigation_phases(self, cases, officers):
        by_user = officers["_by_username"]
        leads = [by_user["so_meena"], by_user["so_meena"], by_user["so_kiran"],
                 by_user["constable_deepa"], by_user["constable_manju"], by_user["spdig_arjun"]]
        investigations = []
        for case, lead in zip(cases, leads):
            inv, _ = Investigation.objects.get_or_create(
                case=case, officer=lead,
                defaults={"status": Investigation.Status.ACTIVE, "findings": "Initial inquiry underway."},
            )
            investigations.append(inv)
        return investigations

    def seed_investigation_steps(self, investigations, officers):
        by_user = officers["_by_username"]
        constable = by_user["constable_ravi"]
        for i, inv in enumerate(investigations):
            InvestigationStep.objects.get_or_create(
                investigation=inv,
                description="Recorded statement from complainant.",
                performed_by=constable,
                step_date=datetime.datetime(2026, 6, 2 + i, 10, 0),
            )
            InvestigationStep.objects.get_or_create(
                investigation=inv,
                description="Reviewed CCTV footage from nearby cameras.",
                performed_by=constable,
                step_date=datetime.datetime(2026, 6, 3 + i, 15, 0),
            )

    def seed_arrests(self, cases, officers):
        by_user = officers["_by_username"]
        data = [
            (cases[0], "Unknown Suspect (CCTV match pending)", by_user["so_meena"],
             datetime.datetime(2026, 6, 5, 14, 0), "MG Road area"),
            (cases[3], "Rajesh Kumar", by_user["constable_deepa"],
             datetime.datetime(2026, 6, 19, 9, 0), "Koramangala"),
        ]
        for case, name, officer, arrest_date, location in data:
            Arrest.objects.get_or_create(
                case=case, arrested_person_name=name,
                defaults={
                    "arresting_officer": officer,
                    "arrest_date": arrest_date,
                    "arrest_location": location,
                    "remarks": "Detained based on investigation findings.",
                },
            )

    def seed_chargesheets(self, cases, officers):
        by_user = officers["_by_username"]
        data = [
            (cases[0], by_user["so_meena"], "BNS Section 303 - Theft", Chargesheet.Status.FILED),
            (cases[3], by_user["constable_deepa"], "BNS Section 309 - Robbery", Chargesheet.Status.FILED),
        ]
        sheets = []
        for case, officer, summary, status in data:
            cs, _ = Chargesheet.objects.get_or_create(
                case=case,
                defaults={
                    "filed_by": officer,
                    "filing_date": datetime.date(2026, 6, 20),
                    "sections_summary": summary,
                    "status": status,
                },
            )
            sheets.append(cs)
        return sheets

    def seed_court_cases(self, chargesheets):
        data = [
            ("CC-2026-5501", "Bengaluru City Civil & Sessions Court"),
            ("CC-2026-5502", "Bengaluru City Civil & Sessions Court"),
        ]
        for cs, (number, court_name) in zip(chargesheets, data):
            CourtCase.objects.get_or_create(
                chargesheet=cs,
                defaults={
                    "court_case_number": number,
                    "court_name": court_name,
                    "filing_date": datetime.date(2026, 6, 25),
                    "status": CourtCase.Status.PENDING,
                },
            )

    # ------------------------------------------------------------------
    # persons
    # ------------------------------------------------------------------
    def seed_persons(self):
        data = [
            ("Rekha", "Iyer", Person.Gender.FEMALE, datetime.date(1990, 3, 14)),
            ("Prakash", "Menon", Person.Gender.MALE, datetime.date(1985, 7, 22)),
            ("Unknown", "Suspect", Person.Gender.UNKNOWN, None),
            ("Sunil", "Verma", Person.Gender.MALE, datetime.date(1992, 11, 5)),
            ("Ganesh", "Kumar", Person.Gender.MALE, datetime.date(1978, 2, 18)),
            ("Rajesh", "Kumar", Person.Gender.MALE, datetime.date(1995, 9, 30)),
            ("Deepak", "Rao", Person.Gender.MALE, datetime.date(1988, 5, 12)),
            ("Anita", "Reddy", Person.Gender.FEMALE, datetime.date(1983, 1, 25)),
        ]
        people = []
        for first, last, gender, dob in data:
            person, _ = Person.objects.get_or_create(
                first_name=first, last_name=last,
                defaults={"gender": gender, "date_of_birth": dob},
            )
            people.append(person)
        return people

    def seed_person_case_roles(self, people, cases, officers):
        by_user = officers["_by_username"]
        so = by_user["so_meena"]
        data = [
            (people[0], cases[0], PersonCaseRole.Role.COMPLAINANT),
            (people[2], cases[0], PersonCaseRole.Role.SUSPECT),
            (people[1], cases[1], PersonCaseRole.Role.COMPLAINANT),
            (people[3], cases[2], PersonCaseRole.Role.VICTIM),
            (people[4], cases[3], PersonCaseRole.Role.COMPLAINANT),
            (people[5], cases[3], PersonCaseRole.Role.ACCUSED),
            (people[6], cases[4], PersonCaseRole.Role.COMPLAINANT),
            (people[7], cases[5], PersonCaseRole.Role.COMPLAINANT),
        ]
        for person, case, role in data:
            PersonCaseRole.objects.get_or_create(
                person=person, case=case, role=role, defaults={"added_by": so},
            )

    def seed_contact_details(self, people):
        contact_data = [
            (people[0], "9845012345", "rekha.iyer@example.com", "12 MG Road", "Bengaluru", "Bengaluru Urban", "560001"),
            (people[1], "9845098765", "prakash.menon@example.com", "45 Indiranagar", "Bengaluru", "Bengaluru Urban", "560038"),
            (people[3], "9845011122", "sunil.verma@example.com", "9 Whitefield Main Rd", "Bengaluru", "Bengaluru Urban", "560066"),
            (people[6], "9845055667", "deepak.rao@example.com", "22 Sayyaji Rao Rd", "Mysuru", "Mysuru", "570001"),
            (people[7], "9845077889", "anita.reddy@example.com", "5 Cubbon Park Rd", "Bengaluru", "Bengaluru Urban", "560001"),
        ]
        for person, phone, email, address, city, district, pincode in contact_data:
            Phone.objects.get_or_create(person=person, phone_number=phone, defaults={"is_primary": True})
            Email.objects.get_or_create(person=person, email=email, defaults={"is_primary": True})
            Address.objects.get_or_create(
                person=person, address_line=address, city=city,
                defaults={"district": district, "pincode": pincode, "is_primary": True},
            )

    # ------------------------------------------------------------------
    # assets
    # ------------------------------------------------------------------
    def seed_assets(self, people, cases):
        vehicles_data = [
            ("KA-01-AB-1234", Vehicle.VehicleType.BIKE, "Honda", "Activa", people[1]),
            ("KA-03-CD-5678", Vehicle.VehicleType.CAR, "Maruti Suzuki", "Swift", people[5]),
            ("KA-09-EF-4321", Vehicle.VehicleType.CAR, "Hyundai", "Creta", people[7]),
        ]
        for reg, vtype, make, model, owner in vehicles_data:
            vehicle, _ = Vehicle.objects.get_or_create(
                registration_number=reg,
                defaults={"vehicle_type": vtype, "make": make, "model": model},
            )
            VehicleOwnership.objects.get_or_create(
                vehicle=vehicle, owner=owner,
                defaults={"ownership_type": VehicleOwnership.OwnershipType.CURRENT,
                          "start_date": datetime.date(2022, 1, 1)},
            )

        properties_data = [
            (Property.PropertyType.ELECTRONICS, "Samsung Galaxy phone, stolen from complainant",
             people[0], cases[0], 25000, Property.Status.REPORTED_STOLEN),
            (Property.PropertyType.JEWELRY, "Gold ornaments stolen from jewelry shop",
             people[4], cases[3], 1500000, Property.Status.REPORTED_STOLEN),
            (Property.PropertyType.CASH, "Cash recovered during raid",
             None, cases[3], 80000, Property.Status.SEIZED),
        ]
        for ptype, desc, owner, case, value, status in properties_data:
            Property.objects.get_or_create(
                property_type=ptype, description=desc,
                defaults={"owner": owner, "case": case, "estimated_value": value, "status": status},
            )

        weapons_data = [
            (Weapon.WeaponType.KNIFE, "", None, cases[0], Weapon.Status.SEIZED, "Seized during investigation"),
            (Weapon.WeaponType.FIREARM, "", None, cases[3], Weapon.Status.ILLEGAL, "Country-made pistol recovered from suspect"),
        ]
        for wtype, serial, owner, case, status, desc in weapons_data:
            Weapon.objects.get_or_create(
                weapon_type=wtype, description=desc,
                defaults={"serial_number": serial, "owner": owner, "case": case, "status": status},
            )

    # ------------------------------------------------------------------
    # assistant (AI)
    # ------------------------------------------------------------------
    def seed_assistant_data(self, officers, cases):
        by_user = officers["_by_username"]
        so = by_user["so_meena"]
        spdig = by_user["spdig_arjun"]

        convo1, _ = Conversation.objects.get_or_create(
            officer=so, title="Theft trends in Cubbon Park area", defaults={"case": cases[0]},
        )
        ChatMessage.objects.get_or_create(
            conversation=convo1, sender=ChatMessage.Sender.USER,
            content="Show me theft cases reported near MG Road in the last month.",
        )
        ChatMessage.objects.get_or_create(
            conversation=convo1, sender=ChatMessage.Sender.AI,
            content="Found 3 theft cases near MG Road in the last 30 days, mostly mobile phone thefts.",
            defaults={"metadata": {"tool": "vanna_sql", "generated_sql": "SELECT * FROM crime WHERE ..."}},
        )

        convo2, _ = Conversation.objects.get_or_create(
            officer=spdig, title="District-wide robbery pattern check", defaults={"case": cases[3]},
        )
        ChatMessage.objects.get_or_create(
            conversation=convo2, sender=ChatMessage.Sender.USER,
            content="Are there similar armed robberies in Bengaluru Urban this month?",
        )
        ChatMessage.objects.get_or_create(
            conversation=convo2, sender=ChatMessage.Sender.AI,
            content="Found 1 other robbery case with a similar pattern in Koramangala this month.",
            defaults={"metadata": {"tool": "neo4j_cypher", "query": "MATCH (c:Crime)-[:SIMILAR_TO]->(c2) ..."}},
        )

        for officer, convo, action_desc in [
            (so, convo1, "Queried theft trends via AI assistant"),
            (spdig, convo2, "Queried robbery pattern analysis via AI assistant"),
        ]:
            AuditLog.objects.get_or_create(
                officer=officer, action_type=AuditLog.ActionType.QUERY,
                description=action_desc, defaults={"related_conversation": convo},
            )

        PredictionHistory.objects.get_or_create(
            officer=so, prediction_type=PredictionHistory.PredictionType.CRIME_HOTSPOT,
            defaults={
                "case": cases[0],
                "input_parameters": {"district": "Bengaluru Urban", "crime_type": "Theft"},
                "output_result": {"hotspot": "MG Road", "risk_level": "high"},
                "confidence_score": 0.87,
            },
        )
        PredictionHistory.objects.get_or_create(
            officer=spdig, prediction_type=PredictionHistory.PredictionType.CRIME_TREND,
            defaults={
                "case": cases[3],
                "input_parameters": {"district": "Bengaluru Urban", "crime_type": "Robbery", "period": "monthly"},
                "output_result": {"trend": "increasing", "change_pct": 18},
                "confidence_score": 0.79,
            },
        )

        GeneratedReport.objects.get_or_create(
            officer=so, report_type=GeneratedReport.ReportType.CASE_REPORT,
            title="Case Summary - CR-2026-00101",
            defaults={"case": cases[0], "content_summary": "Auto-generated summary of theft case."},
        )
        GeneratedReport.objects.get_or_create(
            officer=spdig, report_type=GeneratedReport.ReportType.ANALYTICS,
            title="Bengaluru Urban Robbery Trend Report",
            defaults={"case": cases[3], "content_summary": "District-wide robbery trend analysis for June 2026."},
        )

    # ------------------------------------------------------------------
    def print_summary(self, officers):
        self.stdout.write(self.style.SUCCESS("\nSeed complete. Test login credentials (all password: Pass@1234):\n"))
        for username, officer in officers["_by_username"].items():
            self.stdout.write(f"  {officer.role.name:16s} -> username: {username}  (station: {officer.police_station.code})")
        self.stdout.write(self.style.WARNING(
            "\nLog in at /admin/ with any of these to test RBAC scoping — "
            "e.g. constable_ravi should only see Cubbon Park data, "
            "spdig_arjun should see all Bengaluru Urban stations (Cubbon Park + Whitefield + Koramangala)."
        ))