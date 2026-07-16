"""
KSP Insight AI — DRF Serializers
App: assets
"""

from rest_framework import serializers

from assets.models import Vehicle, VehicleOwnership, Property, Weapon


class VehicleOwnershipSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = VehicleOwnership
        fields = [
            "id", "vehicle", "owner", "owner_name",
            "ownership_type", "start_date", "end_date", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}"


class VehicleSerializer(serializers.ModelSerializer):
    ownerships = VehicleOwnershipSerializer(many=True, read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id", "registration_number", "vehicle_type", "make", "model",
            "color", "chassis_number", "engine_number", "is_stolen", "status",
            "ownerships", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PropertySerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    case_number = serializers.CharField(source="case.case_number", read_only=True, default=None)

    class Meta:
        model = Property
        fields = [
            "id", "property_type", "description", "estimated_value",
            "owner", "owner_name", "case", "case_number",
            "status", "location", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_owner_name(self, obj):
        if obj.owner is None:
            return None
        return f"{obj.owner.first_name} {obj.owner.last_name}"


class WeaponSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    case_number = serializers.CharField(source="case.case_number", read_only=True, default=None)

    class Meta:
        model = Weapon
        fields = [
            "id", "weapon_type", "license_number", "serial_number",
            "owner", "owner_name", "case", "case_number",
            "status", "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_owner_name(self, obj):
        if obj.owner is None:
            return None
        return f"{obj.owner.first_name} {obj.owner.last_name}"