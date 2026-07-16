"""
KSP Insight AI — DRF Serializers
App: crimes
"""

from rest_framework import serializers

from crimes.models import CrimeCategory, Crime, FIR, FIRCrime


class CrimeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeCategory
        fields = [
            "id", "name", "code_type", "section_code", "severity",
            "description", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CrimeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    police_station_name = serializers.CharField(source="police_station.name", read_only=True)
    reported_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Crime
        fields = [
            "id", "category", "category_name",
            "police_station", "police_station_name",
            "reported_by", "reported_by_name",
            "description", "date_of_occurrence", "time_of_occurrence",
            "location_description", "latitude", "longitude",
            "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at","reported_by"]

    def get_reported_by_name(self, obj):
        return f"{obj.reported_by.first_name} {obj.reported_by.last_name}"

    def create(self, validated_data):
        # Default reported_by to the requesting officer if not explicitly set.
        request = self.context.get("request")
        if "reported_by" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["reported_by"] = officer
        return super().create(validated_data)


class FIRSerializer(serializers.ModelSerializer):
    police_station_name = serializers.CharField(source="police_station.name", read_only=True)
    registered_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FIR
        fields = [
            "id", "fir_number",
            "police_station", "police_station_name",
            "registered_by", "registered_by_name",
            "complainant_name", "complainant_phone",
            "date_filed", "incident_date", "incident_location",
            "status", "summary", "updated_at",
        ]
        read_only_fields = ["id", "date_filed", "updated_at"]

    def get_registered_by_name(self, obj):
        return f"{obj.registered_by.first_name} {obj.registered_by.last_name}"

    def create(self, validated_data):
        request = self.context.get("request")
        if "registered_by" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["registered_by"] = officer
        return super().create(validated_data)


class FIRCrimeSerializer(serializers.ModelSerializer):
    fir_number = serializers.CharField(source="fir.fir_number", read_only=True)
    crime_category_name = serializers.CharField(source="crime.category.name", read_only=True)

    class Meta:
        model = FIRCrime
        fields = [
            "id", "fir", "fir_number", "crime", "crime_category_name",
            "is_primary_offense", "created_at",
        ]
        read_only_fields = ["id", "created_at"]