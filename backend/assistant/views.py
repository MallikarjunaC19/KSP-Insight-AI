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

import os
import tempfile

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from assistant.ai.report_generator import generate_conversation_pdf
from assistant.ai.orchestrator import KavachAssistant
from assistant.ai.sarvam_client import transcribe_speech_to_english
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

    @action(detail=True, methods=["post"], url_path="export-pdf")
    def export_pdf(self, request, pk=None):
        """
        POST /api/conversations/{id}/export-pdf/

        Generates a PDF transcript of this conversation and returns a
        download URL. RBAC-scoped via get_object() — an officer can only
        export their own conversations; DGP/SCRB Analyst can export any
        (same scope as viewing them at all).
        """
        conversation = self.get_object()
        if not conversation.messages.exists():
            return Response(
                {"detail": "This conversation has no messages to export."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            report = generate_conversation_pdf(conversation)
        except Exception as exc:
            return Response(
                {"detail": f"PDF generation failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        download_url = request.build_absolute_uri(settings.MEDIA_URL + report.file_reference)

        return Response({
            "report_id": str(report.id),
            "title": report.title,
            "generated_at": report.generated_at,
            "download_url": download_url,
        })

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        """
        POST /api/conversations/{id}/send-message/

        Accepts either:
          - multipart/form-data with a "message" text field, or
          - multipart/form-data with an "audio" file field (mic input)

        Audio is transcribed to English BEFORE the agent runs — the
        agent (KavachAssistant) never receives raw audio, only text
        either way. RBAC-scoped via get_object(), same pattern as
        export_pdf.

        NOTE: KavachAssistant is scoped to conversation.officer, not to
        the requesting officer. get_object() already enforces who is
        ALLOWED to hit this endpoint for this conversation (an officer's
        own conversations, or any conversation for state-scoped roles
        like DGP/SCRB Analyst). But the assistant itself must be built
        for the conversation's owner — that's whose station/RBAC context
        the tools and system prompt should reflect, and it's also what
        KavachAssistant.handle_message() checks against internally. Using
        the requesting officer here would raise a ValueError whenever a
        state-scoped role messages someone else's conversation, and would
        otherwise leak the requester's own RBAC scope into another
        officer's chat history.
        """
        conversation = self.get_object()
        officer = get_officer(request)
        if officer is None:
            return Response(
                {"detail": "No officer profile associated with this account."},
                status=status.HTTP_403_FORBIDDEN,
            )

        audio_file = request.FILES.get("audio")

        if audio_file:
            suffix = os.path.splitext(audio_file.name)[1] or ".wav"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                for chunk in audio_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                user_text = transcribe_speech_to_english(tmp_path)
            except Exception as exc:
                return Response(
                    {"detail": f"Couldn't process audio: {exc}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            finally:
                os.unlink(tmp_path)
        else:
            user_text = request.data.get("message", "").strip()
            if not user_text:
                return Response(
                    {"detail": "No message or audio provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Scoped to the conversation's owner, not the requesting officer —
        # see docstring note above.
        assistant = KavachAssistant(conversation.officer)
        ai_message = assistant.handle_message(conversation, user_text)

        return Response({
            **ChatMessageSerializer(ai_message).data,
            "transcribed_text": user_text if audio_file else None,
        })


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