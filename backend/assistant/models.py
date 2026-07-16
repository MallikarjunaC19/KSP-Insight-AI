"""
KSP Insight AI — Module 6: AI
App: assistant

Entities: Conversation, ChatMessage, AuditLog, PredictionHistory, GeneratedReport

"""

import uuid
from django.db import models
from accounts.models import Officer
from investigations.models import InvestigationCase


class Conversation(models.Model):
    """A chat session between an officer and the AI assistant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name="conversations")
    case = models.ForeignKey(
        InvestigationCase, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="conversations", help_text="Optional — link this chat to a specific case"
    )
    title = models.CharField(max_length=200, blank=True, help_text="Auto-generated or officer-set title")
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversation"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["officer"]),
            models.Index(fields=["case"]),
        ]

    def __str__(self):
        return self.title or f"Conversation {self.id}"


class ChatMessage(models.Model):
    """One message within a conversation — either from the officer or the AI."""

    class Sender(models.TextChoices):
        USER = "USER", "User"
        AI = "AI", "AI"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=5, choices=Sender.choices)
    content = models.TextField()
    metadata = models.JSONField(
        null=True, blank=True,
        help_text="LangChain execution trace: tool used, generated SQL/Cypher, source, reasoning"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"


class AuditLog(models.Model):
    """Generic audit trail — chatbot queries and any other sensitive data access."""

    class ActionType(models.TextChoices):
        QUERY = "QUERY", "AI Query"
        LOGIN = "LOGIN", "Login"
        DATA_ACCESS = "DATA_ACCESS", "Data Access"
        EXPORT = "EXPORT", "Export"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name="audit_logs")
    action_type = models.CharField(max_length=15, choices=ActionType.choices)
    description = models.TextField(blank=True)
    related_conversation = models.ForeignKey(
        Conversation, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["officer"]),
            models.Index(fields=["action_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.officer} - {self.action_type} @ {self.created_at}"


class PredictionHistory(models.Model):
    """Stores AI/QuickML prediction outputs — hotspots, trends, risk scores, etc."""

    class PredictionType(models.TextChoices):
        CRIME_HOTSPOT = "CRIME_HOTSPOT", "Crime Hotspot"
        CRIME_TREND = "CRIME_TREND", "Crime Trend"
        RISK_SCORE = "RISK_SCORE", "Risk Score"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name="predictions_requested")
    case = models.ForeignKey(
        InvestigationCase, on_delete=models.SET_NULL, null=True, blank=True, related_name="predictions"
    )
    prediction_type = models.CharField(max_length=20, choices=PredictionType.choices)
    input_parameters = models.JSONField(help_text="Parameters passed to the model")
    output_result = models.JSONField(help_text="Model output — structure varies by prediction_type")
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prediction_history"
        verbose_name_plural = "Prediction History"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["prediction_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.prediction_type} @ {self.created_at}"


class GeneratedReport(models.Model):
    """
    AI-generated report (PDF summary, case report, analytics export).

    TODO: file_reference is a plain string placeholder until file storage
    (Catalyst Stratus or equivalent) is wired in — swap to a real
    file/storage field then.
    """

    class ReportType(models.TextChoices):
        CRIME_SUMMARY = "CRIME_SUMMARY", "Crime Summary"
        CASE_REPORT = "CASE_REPORT", "Case Report"
        ANALYTICS = "ANALYTICS", "Analytics"
        CUSTOM = "CUSTOM", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name="reports_generated")
    case = models.ForeignKey(
        InvestigationCase, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports"
    )
    report_type = models.CharField(max_length=15, choices=ReportType.choices)
    title = models.CharField(max_length=200)
    content_summary = models.TextField(blank=True)
    file_reference = models.CharField(max_length=500, blank=True, help_text="Temporary — path/URL as text")
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "generated_report"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["report_type"]),
            models.Index(fields=["case"]),
        ]

    def __str__(self):
        return self.title