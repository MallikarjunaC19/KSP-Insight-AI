"""
assistant/management/commands/test_bhashini.py

Usage:
    python manage.py test_bhashini

Runs a real end-to-end test of the KavachAssistant agent with a
Kannada-language question, and prints diagnostics at every step so
failures are easy to localize.
"""

from django.core.management.base import BaseCommand
from accounts.models import Officer
from assistant.models import Conversation
from assistant.ai.orchestrator import KavachAssistant


class Command(BaseCommand):
    help = "End-to-end test: Kannada question -> KavachAssistant -> answer"

    def handle(self, *args, **options):
        self.stdout.write("=== Step 1: Find a test officer ===")
        officer = Officer.objects.filter(role__name="CONSTABLE").select_related("police_station").first()
        if officer is None:
            self.stderr.write(self.style.ERROR(
                "No officers found. Run `python manage.py seed_data` first."
            ))
            return
        self.stdout.write(self.style.SUCCESS(
            f"Testing as: {officer.first_name} {officer.last_name}, "
            f"badge {officer.badge_number}, station: {officer.police_station.name}"
        ))

        self.stdout.write("\n=== Step 2: Build the agent ===")
        try:
            conversation = Conversation.objects.create(officer=officer)
            assistant = KavachAssistant(officer)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"KavachAssistant init failed: {exc}"))
            raise

        self.stdout.write("Tools loaded:")
        for t in assistant.tools:
            name = getattr(t, "name", "NO .name ATTRIBUTE — BROKEN TOOL")
            self.stdout.write(f"  - {type(t).__name__}: {name}")

        self.stdout.write("\n=== Step 3: Ask the Kannada question ===")
        question = "ನನ್ನ ಠಾಣೆಯಲ್ಲಿ ಎಷ್ಟು ಪ್ರಕರಣಗಳಿವೆ?"  # "how many cases at my station"
        self.stdout.write(f"Question: {question}")

        try:
            ai_message = assistant.handle_message(conversation, question)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"handle_message failed: {exc}"))
            raise

        self.stdout.write("\n=== Step 4: Results ===")
        self.stdout.write(self.style.SUCCESS(f"ANSWER:\n{ai_message.content}"))
        self.stdout.write(f"\nTOOLS USED: {ai_message.metadata.get('tools_used')}")
        self.stdout.write(f"ELAPSED MS: {ai_message.metadata.get('elapsed_ms')}")

        sql_trace = ai_message.metadata.get("sql_trace")
        if sql_trace:
            self.stdout.write(f"\nSQL TRACE: {sql_trace}")
        else:
            self.stdout.write(self.style.WARNING(
                "\nNo sql_trace found — sql_lookup may not have been called, "
                "or the question didn't route through it."
            ))

        self.stdout.write("\n=== Step 5: Sanity checks ===")
        tools_used = ai_message.metadata.get("tools_used", [])
        if "bhashini" not in tools_used:
            self.stdout.write(self.style.WARNING(
                "bhashini was NOT called — the agent may not have recognized "
                "the Kannada script, or translated it silently without using "
                "the tool. Check the system prompt's Kannada-detection guidance."
            ))
        if "sql_lookup" not in tools_used:
            self.stdout.write(self.style.WARNING(
                "sql_lookup was NOT called — the agent may have answered "
                "without querying real data. Treat the answer as unverified."
            ))
        if "bhashini" in tools_used and "sql_lookup" in tools_used:
            self.stdout.write(self.style.SUCCESS(
                "Both bhashini and sql_lookup fired — routing looks correct."
            ))