"""
KSP Insight AI — DRF URLs
App: investigations

Include in your project-level urls.py:

    path("api/", include("investigations.urls")),

Gives you:
    /api/investigation-cases/
    /api/investigations/
    /api/investigation-steps/
    /api/arrests/
    /api/chargesheets/
    /api/court-cases/
"""

from rest_framework.routers import DefaultRouter
from investigations.views import (
    InvestigationCaseViewSet, InvestigationViewSet, InvestigationStepViewSet,
    ArrestViewSet, ChargesheetViewSet, CourtCaseViewSet,
)

router = DefaultRouter()
router.register("investigation-cases", InvestigationCaseViewSet, basename="investigation-case")
router.register("investigations", InvestigationViewSet, basename="investigation")
router.register("investigation-steps", InvestigationStepViewSet, basename="investigation-step")
router.register("arrests", ArrestViewSet, basename="arrest")
router.register("chargesheets", ChargesheetViewSet, basename="chargesheet")
router.register("court-cases", CourtCaseViewSet, basename="court-case")

urlpatterns = router.urls