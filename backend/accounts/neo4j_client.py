"""
KSP Insight AI — Neo4j connection client
Location: accounts/neo4j_client.py

Separate from PostgreSQL entirely — Django's ORM never touches this.
Any code that needs the graph database (seed scripts, LangChain tools,
API views for criminal network analysis) should import get_driver()
from here rather than creating its own connection.
"""

import os
from neo4j import GraphDatabase

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


def run_query(query, parameters=None):
    """Convenience helper: run a single Cypher query, return list of records as dicts."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]