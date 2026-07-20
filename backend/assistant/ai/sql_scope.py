"""
KSP Insight AI (KAVACH AI) — SQL Scope Injection
App: assistant / ai

This is the security-critical piece referenced in tools.py's docstring:
Vanna generates a SQL string from natural language, but that string is
UNTRUSTED — it must never run against Postgres as-is. This module:

  1. Validates the generated SQL is read-only, single-statement.
  2. Walks every table reference in the query (including inside
     subqueries, handled per-Select so nested scopes aren't
     double-injected) and, for any table that's RBAC-scoped in your
     Django models, ANDs in a correlated EXISTS(...) clause tying that
     row back to the officer's station/district — using the exact same
     scope semantics as accounts/permissions.py, just expressed as SQL
     instead of a Django queryset filter.
  3. Refuses to execute (rather than running unfiltered) if it can't
     confidently validate the query.

Mirrors the FK chains from your models exactly:
  crime, fir, officer      -> direct police_station_id column
  investigation_case       -> fir_id -> fir.police_station_id
  investigation            -> case_id -> investigation_case -> fir -> ps
  investigation_step       -> investigation_id -> ... (one level deeper)
  arrest, chargesheet,
  person_case_role         -> case_id -> investigation_case -> fir -> ps
  court_case               -> chargesheet_id -> chargesheet -> case_id -> ... -> ps

person/phone/email/address/vehicle/vehicle_ownership/property/weapon
are intentionally NOT in SCOPE_TABLES — they're unscoped in your DRF
layer too (persons app, assets app), so no injection happens for them.
conversation/chat_message/audit_log/prediction_history/generated_report
are own-record (officer-scoped), not station-scoped — out of scope for
this module; if sql_lookup ever needs to touch those, handle separately.

Known limitation: alias collision if the same scoped table appears
twice in one query (e.g. a self-join) — the injected EXISTS subqueries
use fixed inner aliases, so a repeated outer table would need distinct
inner aliases too. Not handled here; flagged rather than silently
producing a wrong (or wrongly-permissive) query — see validate_and_scope().
"""

import re
from dataclasses import dataclass
from typing import Optional

import sqlglot
from sqlglot import exp

from accounts.permissions import is_state_scoped, is_district_scoped, is_station_scoped


class UnsafeQueryError(Exception):
    """Raised when a generated query can't be safely executed —
    caller should show a friendly refusal, never fall back to running
    the query unfiltered."""


# Each template is an EXISTS(...) SQL fragment. {alias} is the outer
# query's alias for that table; {cond} is the station/district
# condition from build_station_condition(), referencing the innermost
# `ps` alias (police_station).
SCOPE_TABLE_TEMPLATES = {
    "officer": "EXISTS (SELECT 1 FROM police_station ps WHERE ps.id = {alias}.police_station_id AND {cond})",
    "crime": "EXISTS (SELECT 1 FROM police_station ps WHERE ps.id = {alias}.police_station_id AND {cond})",
    "fir": "EXISTS (SELECT 1 FROM police_station ps WHERE ps.id = {alias}.police_station_id AND {cond})",
    "investigation_case": (
        "EXISTS (SELECT 1 FROM fir f_sc JOIN police_station ps ON ps.id = f_sc.police_station_id "
        "WHERE f_sc.id = {alias}.fir_id AND {cond})"
    ),
    "investigation": (
        "EXISTS (SELECT 1 FROM investigation_case ic_sc JOIN fir f_sc ON f_sc.id = ic_sc.fir_id "
        "JOIN police_station ps ON ps.id = f_sc.police_station_id "
        "WHERE ic_sc.id = {alias}.case_id AND {cond})"
    ),
    "investigation_step": (
        "EXISTS (SELECT 1 FROM investigation inv_sc "
        "JOIN investigation_case ic_sc ON ic_sc.id = inv_sc.case_id "
        "JOIN fir f_sc ON f_sc.id = ic_sc.fir_id "
        "JOIN police_station ps ON ps.id = f_sc.police_station_id "
        "WHERE inv_sc.id = {alias}.investigation_id AND {cond})"
    ),
    "arrest": (
        "EXISTS (SELECT 1 FROM investigation_case ic_sc JOIN fir f_sc ON f_sc.id = ic_sc.fir_id "
        "JOIN police_station ps ON ps.id = f_sc.police_station_id "
        "WHERE ic_sc.id = {alias}.case_id AND {cond})"
    ),
    "chargesheet": (
        "EXISTS (SELECT 1 FROM investigation_case ic_sc JOIN fir f_sc ON f_sc.id = ic_sc.fir_id "
        "JOIN police_station ps ON ps.id = f_sc.police_station_id "
        "WHERE ic_sc.id = {alias}.case_id AND {cond})"
    ),
    "person_case_role": (
        "EXISTS (SELECT 1 FROM investigation_case ic_sc JOIN fir f_sc ON f_sc.id = ic_sc.fir_id "
        "JOIN police_station ps ON ps.id = f_sc.police_station_id "
        "WHERE ic_sc.id = {alias}.case_id AND {cond})"
    ),
    "court_case": (
        "EXISTS (SELECT 1 FROM chargesheet cs_sc "
        "JOIN investigation_case ic_sc ON ic_sc.id = cs_sc.case_id "
        "JOIN fir f_sc ON f_sc.id = ic_sc.fir_id "
        "JOIN police_station ps ON ps.id = f_sc.police_station_id "
        "WHERE cs_sc.id = {alias}.chargesheet_id AND {cond})"
    ),
}

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|ATTACH|COPY|EXECUTE|CALL|MERGE)\b",
    re.IGNORECASE,
)


def _escape(value: str) -> str:
    return value.replace("'", "''")


def build_station_condition(officer, ps_alias: str = "ps") -> str:
    """Officer must NOT be state-scoped when this is called (state-scoped
    officers should skip injection entirely — see validate_and_scope)."""
    if is_district_scoped(officer):
        return f"{ps_alias}.district = '{_escape(officer.jurisdiction_district)}'"
    if is_station_scoped(officer):
        return f"{ps_alias}.id = '{officer.police_station_id}'"
    # Unknown/unassigned role — fail closed, matches
    # filter_by_station_field()'s queryset.none() behavior.
    return "FALSE"


def _reject_if_unsafe(sql: str, parsed) -> None:
    if len(list(sqlglot.parse(sql))) != 1:
        raise UnsafeQueryError("Only a single SQL statement is allowed.")
    if not isinstance(parsed, exp.Select):
        raise UnsafeQueryError("Only SELECT statements are allowed.")
    if FORBIDDEN_KEYWORDS.search(sql):
        raise UnsafeQueryError("Query contains a disallowed keyword.")


def _inject_into_select(select_node: exp.Select, officer, condition: str) -> None:
    """Adds one EXISTS(...) clause per scoped table referenced directly
    in this Select's FROM/JOIN (not recursing into nested subqueries —
    those get handled by the caller iterating over ALL Select nodes)."""
    tables = []
    from_clause = select_node.args.get("from")
    if from_clause is not None:
        tables.append(from_clause.this)
    for join in select_node.args.get("joins", []) or []:
        tables.append(join.this)

    seen_aliases = set()
    for t in tables:
        if not isinstance(t, exp.Table):
            continue  # skip joined subqueries/CTEs here — they're Select nodes handled separately
        table_name = t.name.lower()
        alias = t.alias_or_name
        if table_name not in SCOPE_TABLE_TEMPLATES:
            continue
        if alias in seen_aliases:
            raise UnsafeQueryError(
                f"Table '{table_name}' referenced more than once with ambiguous aliasing — refusing to guess scope."
            )
        seen_aliases.add(alias)
        exists_clause = SCOPE_TABLE_TEMPLATES[table_name].format(alias=alias, cond=condition)
        select_node.where(exists_clause, copy=False)


def validate_and_scope(sql: str, officer) -> str:
    """
    Main entry point. Returns a safe SQL string to execute, or raises
    UnsafeQueryError if the query can't be confidently validated/scoped.
    """
    parsed = sqlglot.parse_one(sql, read="postgres")
    _reject_if_unsafe(sql, parsed)

    if is_state_scoped(officer):
        return parsed.sql(dialect="postgres")  # DGP / SCRB Analyst — no injection needed

    condition = build_station_condition(officer)
    for select_node in parsed.find_all(exp.Select):
        _inject_into_select(select_node, officer, condition)

    return parsed.sql(dialect="postgres")