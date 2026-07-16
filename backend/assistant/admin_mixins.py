"""
KSP Insight AI — Reusable Admin RBAC Mixin
App: accounts

Instead of repeating get_queryset()/has_change_permission() in every
ModelAdmin, subclass this mixin and set ONE attribute: station_field.

"""

from accounts.permissions import filter_by_station_field, can_write_record, is_state_scoped


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

class OwnRecordAdminMixin:
    """
    Mix into a ModelAdmin for records that belong to an individual officer
    (e.g. their own AI conversations, predictions, generated reports) —
    as opposed to ScopedAdminMixin, which is for station-based case data.

    Rule: an officer sees only their own records. DGP and SCRB Analyst
    (state-wide oversight roles) see everyone's records, since audit
    trails and analytics are exactly what those two roles exist for.

    Usage:
        @admin.register(Conversation)
        class ConversationAdmin(OwnRecordAdminMixin, admin.ModelAdmin):
            officer_field = "officer"   # the FK field pointing to Officer
    """

    officer_field = None  # subclasses MUST set this, e.g. "officer"

    def _get_officer(self, request):
        return getattr(request.user, "officer_profile", None)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        officer = self._get_officer(request)
        if officer is None:
            return qs.none()
        if self.officer_field is None:
            raise NotImplementedError(f"{self.__class__.__name__} must set officer_field")
        if is_state_scoped(officer):  # DGP / SCRB Analyst see everyone's records
            return qs
        return qs.filter(**{self.officer_field: officer})

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        officer = self._get_officer(request)
        if officer is None:
            return False
        if officer.role.name == "SCRB_ANALYST":
            return False  # read-only role, even for their own generated reports
        if obj is None:
            return True
        if is_state_scoped(officer):
            return True
        owner = getattr(obj, self.officer_field)
        return owner == officer

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)