"""
KSP Insight AI — Graph RBAC scope clause builder
Location: accounts/graph_permissions.py (new file)

Mirrors the same officer.role scoping used throughout permissions.py
and sql_scope.py, but produces a Cypher WHERE fragment + parameters
instead of a SQL EXISTS() clause — since case-scope data in Neo4j is
tagged directly on nodes/relationships (station_code, district) rather
than requiring a join, this is actually simpler than the SQL version.

Usage in a Cypher template:
    clause, params = build_case_scope_clause(officer, alias="c")
    query = f"MATCH (c:InvestigationCase {{case_number: $case_number}}) "
            f"WHERE 1=1 {clause} RETURN c"
    params["case_number"] = case_number
    run_query(query, params)
"""

from accounts.permissions import is_state_scoped, is_district_scoped, is_station_scoped


def build_case_scope_clause(officer, alias: str = "c") -> tuple[str, dict]:
    """
    Returns (cypher_where_fragment, params_dict) restricting any node
    bound to `alias` (must be an InvestigationCase node, or a
    relationship carrying station_code/district properties) to the
    officer's visible scope.

    The fragment starts with "AND" so it can be appended after a
    "WHERE 1=1" placeholder in the calling template — keeps templates
    readable without needing to conditionally omit the WHERE keyword.
    """
    if is_state_scoped(officer):
        return "", {}  # DGP / SCRB Analyst — no restriction

    if is_district_scoped(officer):
        return f"AND {alias}.district = $scope_district", {
            "scope_district": officer.jurisdiction_district
        }

    if is_station_scoped(officer):
        return f"AND {alias}.station_code = $scope_station", {
            "scope_station": officer.police_station.code
        }

    # Unknown/unassigned role -> fail closed, no visibility
    return f"AND {alias}.station_code = $scope_station", {"scope_station": "__NONE__"}