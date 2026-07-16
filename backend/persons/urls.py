"""
KSP Insight AI — DRF URLs
App: persons

Include in your project-level urls.py:

    path("api/", include("persons.urls")),

Gives you:
    /api/persons/
    /api/person-case-roles/
    /api/phones/
    /api/emails/
    /api/addresses/
"""

from rest_framework.routers import DefaultRouter
from persons.views import (
    PersonViewSet, PersonCaseRoleViewSet, PhoneViewSet, EmailViewSet, AddressViewSet,
)

router = DefaultRouter()
router.register("persons", PersonViewSet, basename="person")
router.register("person-case-roles", PersonCaseRoleViewSet, basename="person-case-role")
router.register("phones", PhoneViewSet, basename="phone")
router.register("emails", EmailViewSet, basename="email")
router.register("addresses", AddressViewSet, basename="address")

urlpatterns = router.urls