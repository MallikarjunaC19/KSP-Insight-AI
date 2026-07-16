from django.shortcuts import render

"""
KSP Insight AI — DRF Views
App: assistant

Conversation / PredictionHistory / GeneratedReport: own-record CRUD,
officer_field="officer" — mirrors OwnRecordAdminMixin exactly.

ChatMessage: scoped to the parent conversation's owner
(officer_field="conversation__officer") — see note in chat about this
deviating from the (unscoped) admin, for a reason that doesn't carry
over to a direct API.

AuditLog: read-only ViewSet, no create/update/delete exposed at all —
matches has_add_permission=False and the unconditional
has_delete_permission=False on AuditLogAdmin. Entries are written by
the system itself elsewhere in the codebase, never through this API.
"""

from rest_framework import viewsets, permissions

from assistant.models import (
    Conversation, ChatMessage, AuditLog, PredictionHistory, GeneratedReport,
)
from assistant.serializers import (
    ConversationSerializer, ChatMessageSerializer, AuditLogSerializer,
    PredictionHistorySerializer, GeneratedReportSerializer,
)
from accounts.api_permissions import OwnRecordPermission, get_officer
from accounts.permissions import is_state_scoped


class ConversationViewSet(viewsets.ModelViewSet):
    officer_field = "officer"
    serializer_class = ConversationSerializer
    permission_classes = [OwnRecordPermission]

    def get_queryset(self):
        qs = Conversation.objects.select_related("officer", "case").prefetch_related("messages")
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        if is_state_scoped(officer):
            return qs
        return qs.filter(officer=officer)

    def perform_create(self, serializer):
        serializer.save(
            officer=get_officer(self.request)
        )


class ChatMessageViewSet(viewsets.ModelViewSet):
    officer_field = "conversation__officer"
    serializer_class = ChatMessageSerializer
    permission_classes = [OwnRecordPermission]

    def get_queryset(self):
        qs = ChatMessage.objects.select_related("conversation", "conversation__officer")
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        if is_state_scoped(officer):
            return qs
        return qs.filter(conversation__officer=officer)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only: system writes audit entries directly, never via this API."""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("officer", "related_conversation")
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        if is_state_scoped(officer):
            return qs
        return qs.filter(officer=officer)


class PredictionHistoryViewSet(viewsets.ModelViewSet):
    officer_field = "officer"
    serializer_class = PredictionHistorySerializer
    permission_classes = [OwnRecordPermission]

    def get_queryset(self):
        qs = PredictionHistory.objects.select_related("officer", "case")
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        if is_state_scoped(officer):
            return qs
        return qs.filter(officer=officer)


class GeneratedReportViewSet(viewsets.ModelViewSet):
    officer_field = "officer"
    serializer_class = GeneratedReportSerializer
    permission_classes = [OwnRecordPermission]

    def get_queryset(self):
        qs = GeneratedReport.objects.select_related("officer", "case")
        if self.request.user.is_superuser:
            return qs
        officer = get_officer(self.request)
        if officer is None:
            return qs.none()
        if is_state_scoped(officer):
            return qs
        return qs.filter(officer=officer)
