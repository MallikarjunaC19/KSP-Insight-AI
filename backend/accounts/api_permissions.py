"""
KSP Insight AI — DRF Permission Classes
App: accounts

Thin adapters around accounts/permissions.py — all the actual RBAC
logic (scope checks, write checks) lives there and is reused by both
Django Admin and these DRF views. Nothing here should re-implement
scope logic; it should only call into is_state_scoped/is_district_scoped/
is_station_scoped/can_write/can_write_record.

Save this file as accounts/api_permissions.py (kept separate from your
existing accounts/permissions.py so nothing there gets overwritten).
"""
from accounts.permissions import is_state_scoped
from accounts.models import Role
from rest_framework import permissions
from accounts.permissions import can_write, can_write_record


def get_officer(request):
    """Every authenticated user in this system should have an Officer
    profile (Officer.user is OneToOne to auth User). Returns None for
    superusers without one, or unauthenticated requests."""
    return getattr(request.user, "officer_profile", None)


class IsAuthenticatedOfficer(permissions.BasePermission):
    """
    Base permission for master/reference data (Role, Department, Rank,
    PoliceStation): any authenticated officer can read; only DGP or a
    Django superuser can write. Adjust here if master-data write rules
    change later — this is the one place that decides it.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        officer = get_officer(request)
        if officer is None:
            return False
        from accounts.models import Role
        return officer.role.name == Role.RoleCode.DGP


class OfficerObjectPermission(permissions.BasePermission):
    """
    Permission for the Officer resource itself.

    - List/create: gated at has_permission — must be an authenticated
      officer who is allowed to write (for POST), scope filtering for
      GET happens in the view's get_queryset(), not here.
    - Retrieve/update/delete: gated at has_object_permission using
      can_write_record(), same function the admin mixin uses.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        officer = get_officer(request)
        if officer is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True  # queryset scoping in the view handles visibility
        return can_write(officer)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        officer = get_officer(request)
        if officer is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            # obj already came from a scoped queryset, but double-check
            # defensively in case get_object() bypassed filtering.
            from accounts.permissions import is_state_scoped, is_district_scoped, is_station_scoped
            if is_state_scoped(officer):
                return True
            if is_district_scoped(officer):
                return obj.police_station.district == officer.jurisdiction_district
            if is_station_scoped(officer):
                return obj.police_station_id == officer.police_station_id
            return False
        return can_write_record(officer, obj.police_station)


class StationScopedPermission(permissions.BasePermission):
 
    def _get_station_field(self, view):
        station_field = getattr(view, "station_field", None)
        if station_field is None:
            raise NotImplementedError(
                f"{view.__class__.__name__} must set station_field to use StationScopedPermission"
            )
        return station_field
 
    def _get_station(self, view, obj):
        """Walks the dotted station_field path to the actual PoliceStation instance."""
        value = obj
        for part in self._get_station_field(view).split("__"):
            value = getattr(value, part)
        return value
 
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        officer = get_officer(request)
        if officer is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True  # queryset scoping (filter_by_station_field) handles visibility
        return can_write(officer)
 
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        officer = get_officer(request)
        if officer is None:
            return False
        station = self._get_station(view, obj)
        if request.method in permissions.SAFE_METHODS:
            from accounts.permissions import is_state_scoped, is_district_scoped, is_station_scoped
            if is_state_scoped(officer):
                return True
            if is_district_scoped(officer):
                return station.district == officer.jurisdiction_district
            if is_station_scoped(officer):
                return station.id == officer.police_station_id
            return False
        return can_write_record(officer, station)

class IsAuthenticatedAndCanWrite(permissions.BasePermission):
 
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        officer = get_officer(request)
        if officer is None:
            return False
        return can_write(officer)


class OwnRecordPermission(permissions.BasePermission):
 
    def _officer_field(self, view):
        field = getattr(view, "officer_field", None)
        if field is None:
            raise NotImplementedError(
                f"{view.__class__.__name__} must set officer_field to use OwnRecordPermission"
            )
        return field
 
    def _get_owner(self, view, obj):
        value = obj
        for part in self._officer_field(view).split("__"):
            value = getattr(value, part)
        return value
 
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        officer = get_officer(request)
        if officer is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True  # queryset scoping (own record vs state-wide) handles visibility
        # SCRB Analyst is read-only even on their own records, same as OwnRecordAdminMixin
        return officer.role.name != Role.RoleCode.SCRB_ANALYST
 
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        officer = get_officer(request)
        if officer is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            if is_state_scoped(officer):
                return True
            return self._get_owner(view, obj) == officer
        if officer.role.name == Role.RoleCode.SCRB_ANALYST:
            return False
        if is_state_scoped(officer):
            return True
        return self._get_owner(view, obj) == officer