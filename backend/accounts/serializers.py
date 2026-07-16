"""
KSP Insight AI — DRF Serializers
App: accounts

Master data (Role, Department, Rank, PoliceStation) gets simple
ModelSerializers — no RBAC needed at the serializer level, that's
handled in views.py/permissions.

Officer is the one RBAC-relevant resource: write fields use PK
relations (for create/update), and we add read-only "display" fields
so the frontend doesn't have to do a second lookup per row.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.models import Role, Department, Rank, PoliceStation, Officer

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ["id", "name", "hierarchy_level"]
        read_only_fields = ["id"]


class PoliceStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoliceStation
        fields = [
            "id", "name", "code", "district", "state", "address",
            "contact_number", "latitude", "longitude", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OfficerSerializer(serializers.ModelSerializer):
    """
    Read fields expose human-readable names (rank_name, department_name,
    etc.) alongside the PK so the frontend can display without extra
    calls. Write fields (rank, department, police_station, role, user)
    take PKs, standard DRF ModelSerializer behaviour.
    """

    # Read-only display helpers
    rank_name = serializers.CharField(source="rank.name", read_only=True)
    department_name = serializers.CharField(source="police_station.department.name", read_only=True)
    police_station_name = serializers.CharField(source="police_station.name", read_only=True)
    role_name = serializers.CharField(source="role.get_name_display", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    # Write-only: set a password when creating a brand-new officer+user pair.
    # Optional — omit on update, or if the User already exists elsewhere.
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Officer
        fields = [
            "id", "user", "username", "password",
            "badge_number", "first_name", "last_name",
            "rank", "rank_name",
            "department_name",
            "police_station", "police_station_name",
            "role", "role_name",
            "jurisdiction_district",
            "phone", "email", "date_of_joining", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "user": {"required": False},  # allow create() to build the User itself
        }

    def validate(self, attrs):
        role = attrs.get("role") or getattr(self.instance, "role", None)
        jurisdiction_district = attrs.get(
            "jurisdiction_district",
            getattr(self.instance, "jurisdiction_district", "") if self.instance else "",
        )
        if role is not None:
            if role.name == Role.RoleCode.SP_DIG and not jurisdiction_district:
                raise serializers.ValidationError(
                    {"jurisdiction_district": "Required for SP/DIG role."}
                )
            if role.name != Role.RoleCode.SP_DIG and jurisdiction_district:
                raise serializers.ValidationError(
                    {"jurisdiction_district": "Only SP/DIG officers should have a district set."}
                )
        return attrs

    def create(self, validated_data):
        # If no existing user was supplied, create one from badge_number + password.
        password = validated_data.pop("password", None)
        user = validated_data.get("user")
        if user is None:
            username = validated_data["badge_number"]
            user = User.objects.create_user(
                username=username,
                password=password or User.objects.make_random_password(),
                first_name=validated_data.get("first_name", ""),
                last_name=validated_data.get("last_name", ""),
                email=validated_data.get("email", ""),
            )
            validated_data["user"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.user.set_password(password)
            instance.user.save(update_fields=["password"])
        return super().update(instance, validated_data)