"""
KSP Insight AI — Reusable Admin RBAC Mixin
App: accounts

Instead of repeating get_queryset()/has_change_permission() in every
ModelAdmin, subclass this mixin and set ONE attribute: station_field.

Usage:
    from accounts.admin_mixins import ScopedAdminMixin

    @admin.register(Crime)
    class CrimeAdmin(ScopedAdminMixin, admin.ModelAdmin):
        station_field = "police_station"          # direct FK
        list_display = (...)

    @admin.register(FIR)
    class FIRAdmin(ScopedAdminMixin, admin.ModelAdmin):
        station_field = "police_station"

    @admin.register(InvestigationCase)
    class InvestigationCaseAdmin(ScopedAdminMixin, admin.ModelAdmin):
        station_field = "fir__police_station"      # traverse FK chain

    @admin.register(Person)
    class PersonAdmin(ScopedAdminMixin, admin.ModelAdmin):
        # Person has no direct station — scope via their case roles instead
        station_field = "case_roles__case__fir__police_station"

If a model has no sensible station path (e.g. it's global/reference
data), just don't use this mixin — plain admin.ModelAdmin is correct.
"""

from accounts.permissions import filter_by_station_field, can_write_record


class ScopedAdminMixin:
    """Mix into any ModelAdmin to apply role/station/district-based access control."""

    station_field = None  # subclasses MUST set this, e.g. "police_station" or "fir__police_station"

    def _get_officer(self, request):
        return getattr(request.user, "officer_profile", None)

    def _get_station_value(self, obj):
        """Walks the dotted station_field path (e.g. 'fir__police_station') to get the actual PoliceStation instance."""
        value = obj
        for part in self.station_field.split("__"):
            value = getattr(value, part)
        return value

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        officer = self._get_officer(request)
        if officer is None:
            return qs.none()
        if self.station_field is None:
            raise NotImplementedError(f"{self.__class__.__name__} must set station_field")
        return filter_by_station_field(qs, officer, station_field=self.station_field)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        officer = self._get_officer(request)
        if officer is None:
            return False
        if obj is None:
            return True  # let them reach the change list; row-level check applies per-object
        return can_write_record(officer, self._get_station_value(obj))

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)