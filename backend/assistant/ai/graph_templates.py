"""
KSP Insight AI — Cypher query templates for graph_lookup
Location: assistant/ai/graph_templates.py (new file)

Deliberately NOT free-form: the LLM never writes Cypher. It only picks
which of these templates fits the officer's question and extracts the
entity name/case number. This sidesteps the lack of a mature Cypher
AST validator (the sql_lookup equivalent of sqlglot doesn't really
exist for Cypher) by never running arbitrary generated Cypher at all.

Every template that touches InvestigationCase-derived data applies
build_case_scope_clause() from accounts/graph_permissions.py.
"""

from accounts.graph_permissions import build_case_scope_clause
from accounts.neo4j_client import run_query


def find_associates_of_person(officer, person_pg_id: str):
    """Who is this person associated with, and via which case(s)?"""
    clause, params = build_case_scope_clause(officer, alias="r")
    query = f"""
        MATCH (p:Person {{pg_id: $person_pg_id}})-[r:ASSOCIATED_WITH]-(other:Person)
        WHERE 1=1 {clause}
        RETURN DISTINCT other.name AS associate_name, r.case_pg_id AS case_pg_id
    """
    params["person_pg_id"] = person_pg_id
    return run_query(query, params)


def find_vehicles_owned_by_person(officer, person_pg_id: str):
    """
    What vehicles does this person own? Not case-scoped by design —
    matches assets app's DRF permission (IsAuthenticatedAndCanWrite,
    unscoped by station), so no scope clause here.
    """
    query = """
        MATCH (p:Person {pg_id: $person_pg_id})-[:OWNS]->(v:Vehicle)
        RETURN v.registration_number AS registration_number
    """
    return run_query(query, {"person_pg_id": person_pg_id})


def find_people_in_case(officer, case_pg_id: str):
    """Who are the suspects/victims/witnesses/accused/complainants in this case?"""
    clause, params = build_case_scope_clause(officer, alias="c")
    query = f"""
        MATCH (c:InvestigationCase {{pg_id: $case_pg_id}})
        WHERE 1=1 {clause}
        MATCH (p:Person)-[r]->(c)
        RETURN p.name AS person_name, type(r) AS role
    """
    params["case_pg_id"] = case_pg_id
    return run_query(query, params)


def find_other_cases_for_person(officer, person_pg_id: str):
    """
    Is this person connected to any other case? Scoped so an officer
    only learns about cases within their own visibility — the person
    node itself is unscoped, but the cases they're linked to are not.
    """
    clause, params = build_case_scope_clause(officer, alias="c")
    query = f"""
        MATCH (p:Person {{pg_id: $person_pg_id}})-[r]->(c:InvestigationCase)
        WHERE 1=1 {clause}
        RETURN DISTINCT c.case_number AS case_number, type(r) AS role, c.status AS status
    """
    params["person_pg_id"] = person_pg_id
    return run_query(query, params)


def find_case_network(officer, case_pg_id: str):
    """Full picture around a case: people involved, and any vehicles they own."""
    clause, params = build_case_scope_clause(officer, alias="c")
    query = f"""
        MATCH (c:InvestigationCase {{pg_id: $case_pg_id}})
        WHERE 1=1 {clause}
        MATCH (p:Person)-[r]->(c)
        OPTIONAL MATCH (p)-[:OWNS]->(v:Vehicle)
        RETURN p.name AS person_name, type(r) AS role,
               collect(DISTINCT v.registration_number) AS vehicles
    """
    params["case_pg_id"] = case_pg_id
    return run_query(query, params)


# Template registry — used by the LLM-based intent classifier in tools.py
# to map a recognized intent string to the actual function to call.
TEMPLATES = {
    "associates_of_person": find_associates_of_person,
    "vehicles_of_person": find_vehicles_owned_by_person,
    "people_in_case": find_people_in_case,
    "other_cases_for_person": find_other_cases_for_person,
    "case_network": find_case_network,
}