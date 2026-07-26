"""
KSP Insight AI — DRF URLs
App: accounts

Include this in your project-level urls.py, e.g.:

    # ksp_insight_ai/urls.py
    from django.urls import path, include

    urlpatterns = [
        ...
        path("api/", include("accounts.urls")),
    ]

This gives you:
    /api/roles/
    /api/departments/
    /api/ranks/
    /api/police-stations/
    /api/officers/
(plus /{id}/ detail routes for each, courtesy of DefaultRouter)

    /api/auth/token/
    /api/auth/token/refresh/
    /api/officers/me/
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from accounts.views import (
    RoleViewSet, DepartmentViewSet, RankViewSet,
    PoliceStationViewSet, OfficerViewSet,
)

from .views import CookieTokenObtainPairView, CookieTokenRefreshView, OfficerMeView

router = DefaultRouter()
router.register("roles", RoleViewSet, basename="role")
router.register("departments", DepartmentViewSet, basename="department")
router.register("ranks", RankViewSet, basename="rank")
router.register("police-stations", PoliceStationViewSet, basename="police-station")
router.register("officers", OfficerViewSet, basename="officer")

urlpatterns = [
    path("auth/token/", CookieTokenObtainPairView.as_view()),
    path("auth/token/refresh/", CookieTokenRefreshView.as_view()),
    path("officers/me/", OfficerMeView.as_view()),
] + router.urls


