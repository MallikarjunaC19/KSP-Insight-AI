from django.shortcuts import render

"""
KSP Insight AI — DRF Views
App: persons

Person/Phone/Email/Address: unscoped by station, same as PersonAdmin/
PhoneAdmin/EmailAdmin/AddressAdmin — a person can span multiple
stations, so any authenticated officer can read; write is gated by
role only (IsAuthenticatedAndCanWrite), no station check.

PersonCaseRole: station-scoped via case__fir__police_station, same as
PersonCaseRoleAdmin.
"""

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from persons.models import Person, PersonCaseRole, Phone, Email, Address
from persons.serializers import (
    PersonSerializer, PersonCaseRoleSerializer, PhoneSerializer, EmailSerializer, AddressSerializer,
)
from accounts.api_permissions import (
    IsAuthenticatedAndCanWrite, StationScopedPermission, get_officer,
)
from accounts.permissions import filter_by_station_field, is_within_scope


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.prefetch_related("phones", "emails", "addresses")
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticatedAndCanWrite]


class PhoneViewSet(viewsets.ModelViewSet):
    queryset = Phone.objects.select_related("person")
    serializer_class = PhoneSerializer
    permission_classes = [IsAuthenticatedAndCanWrite]


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.select_related("person")
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticatedAndCanWrite]


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.select_related("person")
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticatedAndCanWrite]


class PersonCaseRoleViewSet(viewsets.ModelViewSet):
    station_field = "case__fir__police_station"
    serializer_class = PersonCaseRoleSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = PersonCaseRole.objects.select_related(
            "person", "case", "case__fir", "case__fir__police_station", "added_by"
        )
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        return filter_by_station_field(qs, officer, station_field=self.station_field)

    def perform_create(self, serializer):
        officer = get_officer(self.request)
        case = serializer.validated_data.get("case")
        if not self.request.user.is_superuser and officer is not None and case is not None:
            if not is_within_scope(officer, case.fir.police_station):
                raise PermissionDenied("Cannot assign a person's role on a case outside your scope.")
        serializer.save()
