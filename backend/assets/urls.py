"""
KSP Insight AI — DRF URLs
App: assets

Include in your project-level urls.py:

    path("api/", include("assets.urls")),

Gives you:
    /api/vehicles/
    /api/vehicle-ownerships/
    /api/properties/
    /api/weapons/
"""

from rest_framework.routers import DefaultRouter
from assets.views import (
    VehicleViewSet, VehicleOwnershipViewSet, PropertyViewSet, WeaponViewSet,
)

router = DefaultRouter()
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("vehicle-ownerships", VehicleOwnershipViewSet, basename="vehicle-ownership")
router.register("properties", PropertyViewSet, basename="property")
router.register("weapons", WeaponViewSet, basename="weapon")

urlpatterns = router.urls