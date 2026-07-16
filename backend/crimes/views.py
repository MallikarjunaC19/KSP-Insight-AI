from django.shortcuts import render
"""
KSP Insight AI — DRF Views
App: crimes

Crime and FIR both have a direct police_station FK, so station_field
is just "police_station" — same value you used in CrimeAdmin/FIRAdmin.

FIRCrime has no direct station field (your admin doesn't scope it
either), but rather than leaving it fully open at the API layer, this
scopes it via the FK traversal "fir__police_station" — same dotted-path
convention as ScopedAdminMixin, just applied here since the junction
table didn't get a ScopedAdminMixin in the admin. Drop the station_field
line (and use IsAuthenticatedOfficer-style permission instead) if you'd
rather keep it deliberately unscoped like the admin.
"""

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from crimes.models import CrimeCategory, Crime, FIR, FIRCrime
from crimes.serializers import (
    CrimeCategorySerializer, CrimeSerializer, FIRSerializer, FIRCrimeSerializer,
)
from accounts.api_permissions import (
    IsAuthenticatedOfficer, StationScopedPermission, get_officer,
)
from accounts.permissions import filter_by_station_field, is_within_scope


class CrimeCategoryViewSet(viewsets.ModelViewSet):
    """Master data — read for any authenticated officer, write for DGP/superuser only."""
    queryset = CrimeCategory.objects.all()
    serializer_class = CrimeCategorySerializer
    permission_classes = [IsAuthenticatedOfficer]


class CrimeViewSet(viewsets.ModelViewSet):
    station_field = "police_station"
    serializer_class = CrimeSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = Crime.objects.select_related("category", "police_station", "reported_by")
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        return filter_by_station_field(qs, officer, station_field=self.station_field)

    def perform_create(self, serializer):
        officer = get_officer(self.request)
        target_station = serializer.validated_data.get("police_station")

        if not self.request.user.is_superuser and officer is not None:
            if not is_within_scope(officer, target_station):
                raise PermissionDenied(
                    "Cannot file a crime at a station outside your scope."
                )

        serializer.save(reported_by=officer)

    def perform_update(self, serializer):
        officer = get_officer(self.request)
        new_station = serializer.validated_data.get("police_station")
        if new_station and officer is not None and not self.request.user.is_superuser:
            if not is_within_scope(officer, new_station):
                raise PermissionDenied("Cannot move this crime to a station outside your scope.")
        serializer.save()


class FIRViewSet(viewsets.ModelViewSet):
    station_field = "police_station"
    serializer_class = FIRSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = FIR.objects.select_related("police_station", "registered_by")
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        return filter_by_station_field(qs, officer, station_field=self.station_field)

    def perform_create(self, serializer):
        officer = get_officer(self.request)
        target_station = serializer.validated_data.get("police_station")
        if not self.request.user.is_superuser and officer is not None:
            if not is_within_scope(officer, target_station):
                raise PermissionDenied("Cannot register an FIR at a station outside your scope.")
        serializer.save()

    def perform_update(self, serializer):
        officer = get_officer(self.request)
        new_station = serializer.validated_data.get("police_station")
        if new_station and officer is not None and not self.request.user.is_superuser:
            if not is_within_scope(officer, new_station):
                raise PermissionDenied("Cannot move this FIR to a station outside your scope.")
        serializer.save()


class FIRCrimeViewSet(viewsets.ModelViewSet):
    station_field = "fir__police_station"
    serializer_class = FIRCrimeSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = FIRCrime.objects.select_related("fir", "crime", "crime__category")
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        return filter_by_station_field(qs, officer, station_field=self.station_field)

    def perform_create(self, serializer):
        officer = get_officer(self.request)
        fir = serializer.validated_data.get("fir")
        if not self.request.user.is_superuser and officer is not None and fir is not None:
            if not is_within_scope(officer, fir.police_station):
                raise PermissionDenied("Cannot link a crime to an FIR outside your scope.")
        serializer.save()