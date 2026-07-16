"""
KSP Insight AI — DRF URLs
App: crimes

Include in your project-level urls.py:

    path("api/", include("crimes.urls")),

Gives you:
    /api/crime-categories/
    /api/crimes/
    /api/firs/
    /api/fir-crimes/
"""

from rest_framework.routers import DefaultRouter
from crimes.views import (
    CrimeCategoryViewSet, CrimeViewSet, FIRViewSet, FIRCrimeViewSet,
)

router = DefaultRouter()
router.register("crime-categories", CrimeCategoryViewSet, basename="crime-category")
router.register("crimes", CrimeViewSet, basename="crime")
router.register("firs", FIRViewSet, basename="fir")
router.register("fir-crimes", FIRCrimeViewSet, basename="fir-crime")

urlpatterns = router.urls