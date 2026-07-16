"""
KSP Insight AI — DRF Serializers
App: investigations
"""

from rest_framework import serializers

from investigations.models import (
    InvestigationCase, Investigation, InvestigationStep,
    Arrest, Chargesheet, CourtCase,
)


class InvestigationCaseSerializer(serializers.ModelSerializer):
    fir_number = serializers.CharField(source="fir.fir_number", read_only=True)
    lead_officer_name = serializers.SerializerMethodField()

    class Meta:
        model = InvestigationCase
        fields = [
            "id", "case_number", "fir", "fir_number",
            "lead_officer", "lead_officer_name",
            "status", "priority", "opened_date", "closed_date",
            "summary", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "opened_date", "created_at", "updated_at"]

    def get_lead_officer_name(self, obj):
        return f"{obj.lead_officer.first_name} {obj.lead_officer.last_name}"


class InvestigationSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True)
    officer_name = serializers.SerializerMethodField()

    class Meta:
        model = Investigation
        fields = [
            "id", "case", "case_number",
            "officer", "officer_name",
            "start_date", "end_date", "findings", "status", "created_at",
        ]
        read_only_fields = ["id", "start_date", "created_at"]

    def get_officer_name(self, obj):
        return f"{obj.officer.first_name} {obj.officer.last_name}"

    def create(self, validated_data):
        request = self.context.get("request")
        if "officer" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["officer"] = officer
        return super().create(validated_data)


class InvestigationStepSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="investigation.case.case_number", read_only=True)
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = InvestigationStep
        fields = [
            "id", "investigation", "case_number",
            "description", "performed_by", "performed_by_name",
            "step_date", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_performed_by_name(self, obj):
        return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"

    def create(self, validated_data):
        request = self.context.get("request")
        if "performed_by" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["performed_by"] = officer
        return super().create(validated_data)


class ArrestSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True)
    arresting_officer_name = serializers.SerializerMethodField()

    class Meta:
        model = Arrest
        fields = [
            "id", "case", "case_number",
            "arresting_officer", "arresting_officer_name",
            "arrested_person_name", "arrested_person_details",
            "arrest_date", "arrest_location", "remarks", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_arresting_officer_name(self, obj):
        return f"{obj.arresting_officer.first_name} {obj.arresting_officer.last_name}"

    def create(self, validated_data):
        request = self.context.get("request")
        if "arresting_officer" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["arresting_officer"] = officer
        return super().create(validated_data)


class ChargesheetSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True)
    filed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Chargesheet
        fields = [
            "id", "case", "case_number",
            "filed_by", "filed_by_name",
            "court_referred", "filing_date", "sections_summary",
            "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_filed_by_name(self, obj):
        return f"{obj.filed_by.first_name} {obj.filed_by.last_name}"

    def create(self, validated_data):
        request = self.context.get("request")
        if "filed_by" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["filed_by"] = officer
        return super().create(validated_data)


class CourtCaseSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="chargesheet.case.case_number", read_only=True)

    class Meta:
        model = CourtCase
        fields = [
            "id", "chargesheet", "case_number",
            "court_case_number", "court_name", "filing_date",
            "status", "next_hearing_date", "verdict", "verdict_date",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]