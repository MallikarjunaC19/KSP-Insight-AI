from django.shortcuts import render
"""
KSP Insight AI — DRF Views
App: accounts
 
Officer is the only viewset that touches RBAC scope filtering, using
the same filter_by_station_field() the admin mixin uses. Master data
viewsets are plain ReadOnlyModelViewSet + write-gated permission.
"""
 
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
 
from accounts.models import Role, Department, Rank, PoliceStation, Officer
from accounts.serializers import (
    RoleSerializer, DepartmentSerializer, RankSerializer,
    PoliceStationSerializer, OfficerSerializer,
)
from accounts.api_permissions import (
    IsAuthenticatedOfficer, OfficerObjectPermission, get_officer,
)
from accounts.permissions import (
    filter_by_station_field, is_state_scoped, is_district_scoped, is_station_scoped,
)
 
 
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticatedOfficer]
 
 
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticatedOfficer]
 
 
class RankViewSet(viewsets.ModelViewSet):
    queryset = Rank.objects.all()
    serializer_class = RankSerializer
    permission_classes = [IsAuthenticatedOfficer]
 
 
class PoliceStationViewSet(viewsets.ModelViewSet):
    queryset = PoliceStation.objects.all()
    serializer_class = PoliceStationSerializer
    permission_classes = [IsAuthenticatedOfficer]
 
 
class OfficerViewSet(viewsets.ModelViewSet):
    """
    List/retrieve are scoped to the requesting officer's visibility
    (own station / own district / statewide), same rule as the admin.
    Create/update/delete are additionally checked against can_write /
    can_write_record so read-only roles (Constable, SCRB Analyst)
    can never mutate, and scoped roles can't write outside their scope.
    """
    serializer_class = OfficerSerializer
    permission_classes = [OfficerObjectPermission]
 
    def get_queryset(self):
        qs = Officer.objects.select_related(
              "police_station__department",
                "police_station",
                "rank",
                "role",
                "user",
        )
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        return filter_by_station_field(qs, officer, station_field="police_station")
 
    def perform_create(self, serializer):
        requester = get_officer(self.request)
        target_station = serializer.validated_data.get("police_station")
 
        if self.request.user.is_superuser or requester is None:
            serializer.save()
            return
 
        # A scoped officer can only create new officers inside their own
        # visibility: same station (station-scoped) or same district
        # (district-scoped). State-scoped roles (DGP) can create anywhere.
        if is_state_scoped(requester):
            serializer.save()
            return
 
        if is_district_scoped(requester):
            if target_station.district != requester.jurisdiction_district:
                raise PermissionDenied(
                    "Cannot create an officer outside your district."
                )
            serializer.save()
            return
 
        if is_station_scoped(requester):
            if target_station.id != requester.police_station_id:
                raise PermissionDenied(
                    "Cannot create an officer outside your own station."
                )
            serializer.save()
            return
 
        raise PermissionDenied("Your role is not permitted to create officers.")
 
    def perform_update(self, serializer):
        # Object-level permission (OfficerObjectPermission.has_object_permission)
        # already confirmed the requester can write to this specific
        # officer's current station/district before we get here. We only
        # need to re-check if the update is trying to MOVE the officer
        # to a different station outside the requester's scope.
        requester = get_officer(self.request)
        new_station = serializer.validated_data.get("police_station")
 
        if new_station and requester and not self.request.user.is_superuser:
            if is_district_scoped(requester) and new_station.district != requester.jurisdiction_district:
                raise PermissionDenied("Cannot move an officer outside your district.")
            if is_station_scoped(requester) and new_station.id != requester.police_station_id:
                raise PermissionDenied("Cannot move an officer outside your own station.")
 
        serializer.save()
 
