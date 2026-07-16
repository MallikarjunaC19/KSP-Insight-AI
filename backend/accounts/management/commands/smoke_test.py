"""
KSP Insight AI — API Smoke Test
App: accounts (management command)

Run with:
    python manage.py smoke_test_api

What it does, per RBAC role represented in your seeded data:
  1. Logs in as a real seeded officer (username pulled from the DB,
     password is the known seed password for all test officers).
  2. Hits GET on each scoped endpoint and compares the returned IDs
     against what filter_by_station_field()/is_state_scoped() say
     THAT OFFICER should see — i.e. it checks your actual business
     logic, not a hardcoded expected count.
  3. Spot-checks write permissions: a couple of "this role should be
     blocked" and "this role should be allowed" POSTs, matching
     can_write() / SCRB Analyst read-only / AuditLog fully-read-only
     rules from accounts/permissions.py and the assistant admin mixins.

Doesn't touch your real data destructively — write checks that expect
success create exactly one throwaway row per check (a Crime, a
Conversation), left in place; delete them afterward if you don't want
seed data to include them, or wrap in a transaction if you'd rather
this be a true no-op. Nothing here modifies existing rows.

Requires seed_data + setup_rbac_groups to have already been run.
"""

from django.core.management.base import BaseCommand
from rest_framework.test import APIClient

from accounts.models import Officer, Role
from accounts.permissions import (
    filter_by_station_field, is_state_scoped, is_district_scoped, is_station_scoped,
)
from crimes.models import Crime, FIR, CrimeCategory
from investigations.models import InvestigationCase
from assistant.models import Conversation, AuditLog

SEED_PASSWORD = "Pass@1234"


class Cmd:
    """Small result-tracking helper so the command output stays readable."""
    def __init__(self, stdout):
        self.stdout = stdout
        self.passed = 0
        self.failed = 0

    def ok(self, label):
        self.passed += 1
        self.stdout.write(f"  \033[92mPASS\033[0m  {label}")

    def fail(self, label, detail=""):
        self.failed += 1
        self.stdout.write(f"  \033[91mFAIL\033[0m  {label}" + (f"  -- {detail}" if detail else ""))

    def section(self, title):
        self.stdout.write(f"\n=== {title} ===")


def response_items(response):
    """Handles both plain-list and paginated ({'results': [...]}) response shapes."""
    data = response.data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


def login_as(officer):
    client = APIClient()
    ok = client.login(username=officer.user.username, password=SEED_PASSWORD)
    return client if ok else None


class Command(BaseCommand):
    help = "Smoke-tests the DRF API's RBAC scoping across all 6 apps against real seeded data."

    def handle(self, *args, **options):
        r = Cmd(self.stdout)

        officers_by_role = {
            code: list(Officer.objects.filter(role__name=code).select_related(
                "role", "police_station"
            )[:2])
            for code in Role.RoleCode.values
        }

        # ------------------------------------------------------------------
        # 1. Auth sanity check — every seeded officer can actually log in.
        # ------------------------------------------------------------------
        r.section("Authentication")
        for role_code, officers in officers_by_role.items():
            for officer in officers:
                client = login_as(officer)
                if client:
                    r.ok(f"{role_code}: {officer.user.username} logged in")
                else:
                    r.fail(f"{role_code}: {officer.user.username} login", "credentials rejected")

        # ------------------------------------------------------------------
        # 2. GET scoping — compare API results to filter_by_station_field()
        # ------------------------------------------------------------------
        r.section("GET scoping: /api/officers/ (station_field='police_station')")
        self._check_scope(r, officers_by_role, "/api/officers/", Officer, "police_station")

        r.section("GET scoping: /api/crimes/ (station_field='police_station')")
        self._check_scope(r, officers_by_role, "/api/crimes/", Crime, "police_station")

        r.section("GET scoping: /api/firs/ (station_field='police_station')")
        self._check_scope(r, officers_by_role, "/api/firs/", FIR, "police_station")

        r.section("GET scoping: /api/investigation-cases/ (station_field='fir__police_station')")
        self._check_scope(r, officers_by_role, "/api/investigation-cases/", InvestigationCase, "fir__police_station")

        # ------------------------------------------------------------------
        # 3. Unscoped resources — anyone authenticated should see everything
        # ------------------------------------------------------------------
        r.section("Unscoped: /api/persons/ (should be visible to every role)")
        for role_code, officers in officers_by_role.items():
            if not officers:
                continue
            officer = officers[0]
            client = login_as(officer)
            if not client:
                continue
            resp = client.get("/api/persons/")
            if resp.status_code == 200:
                r.ok(f"{role_code} can read /api/persons/")
            else:
                r.fail(f"{role_code} can read /api/persons/", f"status {resp.status_code}")

        # ------------------------------------------------------------------
        # 4. Own-record scoping: /api/conversations/
        # ------------------------------------------------------------------
        r.section("Own-record scoping: /api/conversations/")
        for role_code, officers in officers_by_role.items():
            for officer in officers:
                client = login_as(officer)
                if not client:
                    continue
                resp = client.get("/api/conversations/")
                if resp.status_code != 200:
                    r.fail(f"{role_code} GET /api/conversations/", f"status {resp.status_code}")
                    continue
                got_ids = {str(item["id"]) for item in response_items(resp)}
                if is_state_scoped(officer):
                    expected_ids = set(str(pk) for pk in Conversation.objects.values_list("id", flat=True))
                else:
                    expected_ids = set(str(pk) for pk in Conversation.objects.filter(officer=officer).values_list("id", flat=True))
                if got_ids == expected_ids:
                    r.ok(f"{role_code} ({officer.user.username}) sees exactly their expected conversations ({len(got_ids)})")
                else:
                    r.fail(
                        f"{role_code} ({officer.user.username}) conversation scope mismatch",
                        f"got {len(got_ids)} expected {len(expected_ids)}",
                    )

        # ------------------------------------------------------------------
        # 5. AuditLog must be fully read-only — no create/update/delete route
        # ------------------------------------------------------------------
        r.section("AuditLog is read-only (system-written only)")
        dgp = (officers_by_role.get(Role.RoleCode.DGP) or [None])[0]
        if dgp:
            client = login_as(dgp)
            resp = client.post("/api/audit-logs/", {"action_type": "OTHER", "description": "test"})
            if resp.status_code == 405:
                r.ok("POST /api/audit-logs/ correctly returns 405 (no create action registered)")
            else:
                r.fail("POST /api/audit-logs/ should be 405", f"got {resp.status_code}")

        # ------------------------------------------------------------------
        # 6. Write-permission spot checks
        # ------------------------------------------------------------------
        r.section("Write permission: master data (DGP-only)")
        category = CrimeCategory.objects.first()
        constable = (officers_by_role.get(Role.RoleCode.CONSTABLE) or [None])[0]
        if constable:
            client = login_as(constable)
            resp = client.post("/api/crime-categories/", {
                "name": "Smoke Test Category", "section_code": "TEST-1",
            })
            if resp.status_code == 403:
                r.ok("Constable blocked from creating CrimeCategory (403)")
            else:
                r.fail("Constable should be blocked from creating CrimeCategory", f"got {resp.status_code}")

        r.section("Write permission: Crime create (Constable blocked, Station Officer allowed)")
        station_officer = (officers_by_role.get(Role.RoleCode.STATION_OFFICER) or [None])[0]
        if constable and category and constable.police_station:
            client = login_as(constable)
            resp = client.post("/api/crimes/", {
                "category": str(category.id),
                "police_station": str(constable.police_station.id),
                "description": "Smoke test — Constable should be blocked",
                "date_of_occurrence": "2026-01-01",
            })
            if resp.status_code == 403:
                r.ok("Constable blocked from creating Crime (403)")
            else:
                r.fail("Constable should be blocked from creating Crime", f"got {resp.status_code}")

        if station_officer and category and station_officer.police_station:
            client = login_as(station_officer)
            resp = client.post("/api/crimes/", {
                "category": str(category.id),
                "police_station": str(station_officer.police_station.id),
                "description": "Smoke test — Station Officer should succeed",
                "date_of_occurrence": "2026-01-01",
            })
            if resp.status_code == 201:
                r.ok("Station Officer can create Crime at own station (201)")
            else:
                r.fail("Station Officer should be able to create Crime", f"got {resp.status_code}: {resp.data}")

        r.section("Write permission: Conversation (SCRB Analyst blocked, others allowed)")
        scrb = (officers_by_role.get(Role.RoleCode.SCRB_ANALYST) or [None])[0]
        if scrb:
            client = login_as(scrb)
            resp = client.post("/api/conversations/", {"title": "Smoke test — should be blocked"})
            if resp.status_code == 403:
                r.ok("SCRB Analyst blocked from creating own Conversation (403)")
            else:
                r.fail("SCRB Analyst should be blocked from creating Conversation", f"got {resp.status_code}")

        if constable:
            client = login_as(constable)
            resp = client.post("/api/conversations/", {"title": "Smoke test — should succeed"})
            if resp.status_code == 201:
                r.ok("Constable can create own Conversation (201)")
            else:
                r.fail("Constable should be able to create own Conversation", f"got {resp.status_code}: {resp.data}")

        # ------------------------------------------------------------------
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"RESULT: {r.passed} passed, {r.failed} failed")
        self.stdout.write(f"{'='*50}\n")

    def _check_scope(self, r, officers_by_role, url, model, station_field):
        for role_code, officers in officers_by_role.items():
            for officer in officers:
                client = login_as(officer)
                if not client:
                    continue
                resp = client.get(url)
                if resp.status_code != 200:
                    r.fail(f"{role_code} ({officer.user.username}) GET {url}", f"status {resp.status_code}")
                    continue
                got_ids = {str(item["id"]) for item in response_items(resp)}
                expected_qs = filter_by_station_field(model.objects.all(), officer, station_field=station_field)
                expected_ids = set(str(pk) for pk in expected_qs.values_list("id", flat=True))
                if got_ids == expected_ids:
                    r.ok(f"{role_code} ({officer.user.username}) sees exactly the expected {len(got_ids)} row(s)")
                else:
                    extra = got_ids - expected_ids
                    missing = expected_ids - got_ids
                    detail = f"got {len(got_ids)} expected {len(expected_ids)}"
                    if extra:
                        detail += f", {len(extra)} unexpected row(s) leaked"
                    if missing:
                        detail += f", {len(missing)} expected row(s) missing"
                    r.fail(f"{role_code} ({officer.user.username}) scope mismatch on {url}", detail)