"""
KSP Insight AI — DRF Serializers
App: assistant
"""

from rest_framework import serializers

from assistant.models import (
    Conversation, ChatMessage, AuditLog, PredictionHistory, GeneratedReport,
)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "conversation", "sender", "content", "metadata", "created_at"]
        read_only_fields = ["id", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True, default=None)
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id", "officer", "case", "case_number", "title", "is_active",
            "messages", "started_at", "updated_at",
        ]
        read_only_fields = ["id","officer", "started_at", "updated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if "officer" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["officer"] = officer
        return super().create(validated_data)


class AuditLogSerializer(serializers.ModelSerializer):
    officer_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "officer", "officer_name", "action_type", "description",
            "related_conversation", "ip_address", "created_at",
        ]
        read_only_fields = fields  # fully read-only — see views.py, system-written only

    def get_officer_name(self, obj):
        return f"{obj.officer.first_name} {obj.officer.last_name}"


class PredictionHistorySerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True, default=None)

    class Meta:
        model = PredictionHistory
        fields = [
            "id", "officer", "case", "case_number", "prediction_type",
            "input_parameters", "output_result", "confidence_score", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if "officer" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["officer"] = officer
        return super().create(validated_data)


class GeneratedReportSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True, default=None)

    class Meta:
        model = GeneratedReport
        fields = [
            "id", "officer", "case", "case_number", "report_type", "title",
            "content_summary", "file_reference", "generated_at",
        ]
        read_only_fields = ["id", "generated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if "officer" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["officer"] = officer
        return super().create(validated_data)