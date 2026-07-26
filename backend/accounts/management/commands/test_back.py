"""
assistant/management/commands/test_all_backend.py

Usage:
    python manage.py test_all_backend

Runs a full sweep of every KavachAssistant path in one go: SQL, QuickML,
Graph, Bhashini (Kannada), and general_answer — plus PDF export. Prints
a clear PASS/FAIL/WARN summary at the end so you can see backend health
at a glance instead of testing each piece separately.
"""

from django.core.management.base import BaseCommand
from accounts.models import Officer
from assistant.models import Conversation
from assistant.ai.orchestrator import KavachAssistant
from assistant.ai.report_generator import generate_conversation_pdf


class Command(BaseCommand):
    help = "Full backend sweep: SQL, QuickML, Graph, Bhashini, general_answer, PDF export"

    def handle(self, *args, **options):
        results = []  # (label, "PASS"/"FAIL"/"WARN", detail)

        officer = Officer.objects.select_related("police_station").first()
        if officer is None:
            self.stderr.write(self.style.ERROR(
                "No officers found. Run `python manage.py seed_data` first."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Testing as: {officer.first_name} {officer.last_name}, "
            f"badge {officer.badge_number}, station: {officer.police_station.name}\n"
        ))

        try:
            assistant = KavachAssistant(officer)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"KavachAssistant init failed: {exc}"))
            return

        broken_tools = [
            getattr(t, "name", None) is None for t in assistant.tools
        ]
        if any(broken_tools):
            results.append(("Tool registration", "FAIL", "One or more tools missing .name"))
        else:
            results.append(("Tool registration", "PASS", f"{len(assistant.tools)} tools loaded"))

        # ---- Test cases: (label, question, expected_tool) ----
        test_cases = [
            ("SQL path", "How many open cases are at my station?", "sql_lookup"),
            ("QuickML path", "How severe is a robbery with a weapon and 2 victims at 11pm?", "quickml"),
            ("Graph path", "Who is Rajesh Kumar connected to?", "graph_lookup"),
            ("Bhashini path (Kannada)", "ನನ್ನ ಠಾಣೆಯಲ್ಲಿ ಎಷ್ಟು ಪ್ರಕರಣಗಳಿವೆ?", "bhashini"),
            ("General answer path", "What does IPC section 392 mean?", "general_answer"),
        ]

        for label, question, expected_tool in test_cases:
            self.stdout.write(f"\n--- {label} ---")
            self.stdout.write(f"Q: {question}")
            try:
                conversation = Conversation.objects.create(officer=officer)
                ai_message = assistant.handle_message(conversation, question)
                tools_used = ai_message.metadata.get("tools_used", [])
                self.stdout.write(f"Answer: {ai_message.content[:200]}")
                self.stdout.write(f"Tools used: {tools_used}")

                if expected_tool in tools_used:
                    results.append((label, "PASS", f"tools_used={tools_used}"))
                elif tools_used:
                    results.append((label, "WARN", f"expected {expected_tool}, got {tools_used}"))
                else:
                    results.append((label, "FAIL", "no tools called"))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  ERROR: {exc}"))
                results.append((label, "FAIL", str(exc)[:200]))

        # ---- PDF export ----
        self.stdout.write("\n--- PDF export ---")
        try:
            pdf_conversation = Conversation.objects.create(officer=officer)
            assistant.handle_message(pdf_conversation, "How many open cases are at my station?")
            report = generate_conversation_pdf(pdf_conversation)
            self.stdout.write(f"Generated: {report.file_reference}")
            results.append(("PDF export", "PASS", str(report.file_reference)))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  ERROR: {exc}"))
            results.append(("PDF export", "FAIL", str(exc)[:200]))

        # ---- Summary ----
        self.stdout.write("\n\n=== SUMMARY ===")
        for label, status, detail in results:
            style = {
                "PASS": self.style.SUCCESS,
                "WARN": self.style.WARNING,
                "FAIL": self.style.ERROR,
            }[status]
            self.stdout.write(style(f"[{status}] {label} — {detail}"))