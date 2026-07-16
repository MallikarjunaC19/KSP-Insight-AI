from django.shortcuts import render
"""
KSP Insight AI — DRF Views
App: investigations

station_field on each ViewSet mirrors the exact dotted path you already
use in admin.py for that model — same scoping rule, reused rather than
reinvented, all resolved through the shared StationScopedPermission.

None of these models have a direct police_station FK, so scope on
create is checked by walking up to the FIR through whatever parent
object was submitted (fir / case / investigation / chargesheet),
rather than reading a police_station field straight off validated_data.
"""

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from investigations.models import (
    InvestigationCase, Investigation, InvestigationStep,
    Arrest, Chargesheet, CourtCase,
)
from investigations.serializers import (
    InvestigationCaseSerializer, InvestigationSerializer, InvestigationStepSerializer,
    ArrestSerializer, ChargesheetSerializer, CourtCaseSerializer,
)
from accounts.api_permissions import StationScopedPermission, get_officer
from accounts.permissions import filter_by_station_field, is_within_scope


class InvestigationCaseViewSet(viewsets.ModelViewSet):
    station_field = "fir__police_station"
    serializer_class = InvestigationCaseSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = InvestigationCase.objects.select_related("fir", "fir__police_station", "lead_officer")
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
                raise PermissionDenied("Cannot open a case for an FIR outside your scope.")
        serializer.save()


class InvestigationViewSet(viewsets.ModelViewSet):
    station_field = "case__fir__police_station"
    serializer_class = InvestigationSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = Investigation.objects.select_related("case", "case__fir", "case__fir__police_station", "officer")
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
                raise PermissionDenied("Cannot open an investigation phase outside your scope.")
        serializer.save()


class InvestigationStepViewSet(viewsets.ModelViewSet):
    station_field = "investigation__case__fir__police_station"
    serializer_class = InvestigationStepSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = InvestigationStep.objects.select_related(
            "investigation", "investigation__case", "investigation__case__fir",
            "investigation__case__fir__police_station", "performed_by",
        )
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        return filter_by_station_field(qs, officer, station_field=self.station_field)

    def perform_create(self, serializer):
        officer = get_officer(self.request)
        investigation = serializer.validated_data.get("investigation")
        if not self.request.user.is_superuser and officer is not None and investigation is not None:
            if not is_within_scope(officer, investigation.case.fir.police_station):
                raise PermissionDenied("Cannot add a case-diary entry outside your scope.")
        serializer.save()


class ArrestViewSet(viewsets.ModelViewSet):
    station_field = "case__fir__police_station"
    serializer_class = ArrestSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = Arrest.objects.select_related("case", "case__fir", "case__fir__police_station", "arresting_officer")
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
                raise PermissionDenied("Cannot record an arrest outside your scope.")
        serializer.save()


class ChargesheetViewSet(viewsets.ModelViewSet):
    station_field = "case__fir__police_station"
    serializer_class = ChargesheetSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = Chargesheet.objects.select_related("case", "case__fir", "case__fir__police_station", "filed_by")
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
                raise PermissionDenied("Cannot file a chargesheet outside your scope.")
        serializer.save()


class CourtCaseViewSet(viewsets.ModelViewSet):
    station_field = "chargesheet__case__fir__police_station"
    serializer_class = CourtCaseSerializer
    permission_classes = [StationScopedPermission]

    def get_queryset(self):
        qs = CourtCase.objects.select_related(
            "chargesheet", "chargesheet__case", "chargesheet__case__fir",
            "chargesheet__case__fir__police_station",
        )
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        return filter_by_station_field(qs, officer, station_field=self.station_field)

    def perform_create(self, serializer):
        officer = get_officer(self.request)
        chargesheet = serializer.validated_data.get("chargesheet")
        if not self.request.user.is_superuser and officer is not None and chargesheet is not None:
            if not is_within_scope(officer, chargesheet.case.fir.police_station):
                raise PermissionDenied("Cannot open a court case outside your scope.")
        serializer.save()