"""
KSP Insight AI — DRF Serializers
App: persons
"""

from rest_framework import serializers

from persons.models import Person, PersonCaseRole, Phone, Email, Address


class PhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phone
        fields = ["id", "person", "phone_number", "phone_type", "is_primary", "created_at"]
        read_only_fields = ["id", "created_at"]


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = ["id", "person", "email", "email_type", "is_primary", "created_at"]
        read_only_fields = ["id", "created_at"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id", "person", "address_line", "city", "district", "state",
            "pincode", "address_type", "is_primary", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PersonSerializer(serializers.ModelSerializer):
    """
    Nests phones/emails/addresses read-only for convenience (mirrors the
    inlines on PersonAdmin) — writes to those still go through their own
    endpoints (/api/phones/, /api/emails/, /api/addresses/).
    """
    phones = PhoneSerializer(many=True, read_only=True)
    emails = EmailSerializer(many=True, read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = Person
        fields = [
            "id", "first_name", "last_name", "date_of_birth", "gender",
            "nationality", "aadhaar_number", "father_or_guardian_name",
            "occupation", "notes", "phones", "emails", "addresses",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PersonCaseRoleSerializer(serializers.ModelSerializer):
    person_name = serializers.SerializerMethodField()
    case_number = serializers.CharField(source="case.case_number", read_only=True)
    added_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PersonCaseRole
        fields = [
            "id", "person", "person_name", "case", "case_number",
            "role", "added_by", "added_by_name", "remarks", "added_at",
        ]
        read_only_fields = ["id", "added_at"]

    def get_person_name(self, obj):
        return f"{obj.person.first_name} {obj.person.last_name}".strip()

    def get_added_by_name(self, obj):
        return f"{obj.added_by.first_name} {obj.added_by.last_name}"

    def create(self, validated_data):
        request = self.context.get("request")
        if "added_by" not in validated_data and request is not None:
            officer = getattr(request.user, "officer_profile", None)
            if officer is not None:
                validated_data["added_by"] = officer
        return super().create(validated_data)