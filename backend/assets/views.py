from django.shortcuts import render

"""
KSP Insight AI — DRF Views
App: assets

Deliberately unscoped, matching admin.py (plain ModelAdmin for all
four models — the nullable `case` FK on Property/Weapon breaks the
station-traversal mixin, same reason your admin skipped it). Any
authenticated officer can read; write is gated by role only via
IsAuthenticatedAndCanWrite (Constable/SCRB Analyst stay read-only).
"""

from rest_framework import viewsets

from assets.models import Vehicle, VehicleOwnership, Property, Weapon
from assets.serializers import (
    VehicleSerializer, VehicleOwnershipSerializer, PropertySerializer, WeaponSerializer,
)
from accounts.api_permissions import IsAuthenticatedAndCanWrite


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.prefetch_related("ownerships")
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticatedAndCanWrite]


class VehicleOwnershipViewSet(viewsets.ModelViewSet):
    queryset = VehicleOwnership.objects.select_related("vehicle", "owner")
    serializer_class = VehicleOwnershipSerializer
    permission_classes = [IsAuthenticatedAndCanWrite]


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.select_related("owner", "case")
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticatedAndCanWrite]


class WeaponViewSet(viewsets.ModelViewSet):
    queryset = Weapon.objects.select_related("owner", "case")
    serializer_class = WeaponSerializer
    permission_classes = [IsAuthenticatedAndCanWrite]
