"""
KSP Insight AI — DRF URLs
App: assistant

Include in your project-level urls.py:

    path("api/", include("assistant.urls")),

Gives you:
    /api/conversations/
    /api/chat-messages/
    /api/audit-logs/         (read-only)
    /api/predictions/
    /api/reports/
"""

from rest_framework.routers import DefaultRouter
from assistant.views import (
    ConversationViewSet, ChatMessageViewSet, AuditLogViewSet,
    PredictionHistoryViewSet, GeneratedReportViewSet,
)

router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversation")
router.register("chat-messages", ChatMessageViewSet, basename="chat-message")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("predictions", PredictionHistoryViewSet, basename="prediction")
router.register("reports", GeneratedReportViewSet, basename="report")

urlpatterns = router.urls