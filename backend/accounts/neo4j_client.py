"""
KSP Insight AI — Neo4j connection client

Separate from PostgreSQL entirely — Django's ORM never touches this.
Any code that needs the graph database (seed scripts, LangChain tools,
API views for criminal network analysis) should import get_driver()
from here rather than creating its own connection.
"""

import os
import time
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired

_driver = None


def get_driver():
    """Returns a singleton Neo4j driver, created on first use."""
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        if not all([uri, user, password]):
            raise RuntimeError(
                "Missing NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD in .env — "
                "add them before using the graph database."
            )
        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def run_query(query, parameters=None, max_attempts=2):
    """Convenience helper: run a single Cypher query, return list of records as dicts.

    Retries once on transient connection failures — AuraDB free-tier
    instances auto-pause when idle, and the first query after a pause
    can hit a connection reset while the instance wakes up. A short
    retry absorbs that without surfacing a hard error to the officer.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            driver = get_driver()
            with driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except (ServiceUnavailable, SessionExpired, ConnectionError) as e:
            last_error = e
            if attempt < max_attempts:
                # Force a fresh driver/connection on retry — the singleton
                # may be holding a dead connection from before the pause.
                close_driver()
                time.sleep(2)
            else:
                raise
    raise last_error  # unreachable, but keeps linters happy