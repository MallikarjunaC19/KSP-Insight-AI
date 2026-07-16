"""
KSP Insight AI — Role-Based Access Control (RBAC)
App: accounts

This module is the single source of truth for "who can see/edit what."
Both the Django Admin (via ModelAdmin.get_queryset overrides) and the
future DRF API views (via permission_classes) should call into these
same functions — write the access logic once, reuse everywhere.

Access model:
    CONSTABLE         -> own police station only, read-only on cases
    STATION_OFFICER    -> own police station only, full CRUD
    SP_DIG              -> own district (all stations in it), full CRUD
    DGP                  -> entire state, full CRUD
    SCRB_ANALYST        -> entire state, read-only (analytics use only)
"""

from accounts.models import Role


# ---------------------------------------------------------------------
# Scope checks — "what data can this officer see?"
# ---------------------------------------------------------------------

def is_station_scoped(officer) -> bool:
    """True if this officer's visibility is limited to their own station."""
    return officer.role.name in (Role.RoleCode.CONSTABLE, Role.RoleCode.STATION_OFFICER)


def is_district_scoped(officer) -> bool:
    """True if this officer's visibility is limited to their own district."""
    return officer.role.name == Role.RoleCode.SP_DIG


def is_state_scoped(officer) -> bool:
    """True if this officer can see data across the entire state."""
    return officer.role.name in (Role.RoleCode.DGP, Role.RoleCode.SCRB_ANALYST)


def filter_by_station_field(queryset, officer, station_field: str = "police_station"):
    """
    Restricts a queryset to the officer's visible scope, based on a
    given FK path to PoliceStation (e.g. "police_station",
    "fir__police_station", "case__fir__police_station").

    Usage example (in a ModelAdmin or DRF view):
        qs = filter_by_station_field(InvestigationCase.objects.all(), officer,
                                       station_field="fir__police_station")
    """
    if is_state_scoped(officer):
        return queryset  # DGP / SCRB Analyst see everything

    if is_district_scoped(officer):
        district_field = f"{station_field}__district"
        return queryset.filter(**{district_field: officer.jurisdiction_district})

    if is_station_scoped(officer):
        return queryset.filter(**{station_field: officer.police_station})

    return queryset.none()  # unknown/unassigned role -> no access, fail closed


# ---------------------------------------------------------------------
# Write checks — "can this officer edit/delete this record?"
# ---------------------------------------------------------------------

def can_write(officer) -> bool:
    """
    SCRB Analyst is read-only everywhere. Constable is read-only on
    case-level records (they can still be recorded as reporting officers
    on a Crime, but shouldn't edit case status/chargesheets/etc via admin).
    """
    return officer.role.name not in (Role.RoleCode.SCRB_ANALYST, Role.RoleCode.CONSTABLE)


def can_write_record(officer, station_field_value) -> bool:
    """
    Combines can_write() with scope: e.g. a Station Officer can only edit
    records within their own station even though can_write() is True.
    station_field_value should be the actual PoliceStation instance on
    the record being checked (e.g. investigation_case.fir.police_station).
    """
    if not can_write(officer):
        return False
    if is_state_scoped(officer):
        return True
    if is_district_scoped(officer):
        return station_field_value.district == officer.jurisdiction_district
    if is_station_scoped(officer):
        return station_field_value_id_matches(officer, station_field_value)
    return False


def station_field_value_id_matches(officer, station_field_value) -> bool:
    return officer.police_station_id == station_field_value.id


def is_within_scope(officer, station) -> bool:
    """
    True if `station` (a PoliceStation instance) falls within the
    officer's visibility/write scope. Same branching as can_write_record,
    factored out so viewsets can use it directly when validating a
    target station on create/update (e.g. "can this Station Officer
    file a Crime at this particular station?").
    """
    if is_state_scoped(officer):
        return True
    if is_district_scoped(officer):
        return station.district == officer.jurisdiction_district
    if is_station_scoped(officer):
        return station.id == officer.police_station_id
    return False

