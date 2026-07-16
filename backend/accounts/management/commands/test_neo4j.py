"""
KSP Insight AI — Test Neo4j connectivity

"""

from django.core.management.base import BaseCommand
from accounts.neo4j_client import run_query


class Command(BaseCommand):
    help = "Verify the Neo4j connection is working"

    def handle(self, *args, **options):
        try:
            result = run_query("RETURN 'Connection successful' AS message")
            self.stdout.write(self.style.SUCCESS(result[0]["message"]))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Neo4j connection failed: {e}"))