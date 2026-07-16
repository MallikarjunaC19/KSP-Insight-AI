"""
KSP Insight AI — Module 4: Person Management
App: persons

Entities: Person, PersonCaseRole, Phone, Email, Address

"""

import uuid
from django.db import models
from accounts.models import Officer
from accounts.validators import phone_validator
from investigations.models import InvestigationCase


class Person(models.Model):
    """Master entity for any individual — victim, suspect, witness, accused, officer's contact, etc."""

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"
        UNKNOWN = "UNKNOWN", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.UNKNOWN)
    nationality = models.CharField(max_length=100, default="Indian")
    aadhaar_number = models.CharField(
        max_length=12, unique=True, null=True, blank=True,
        help_text="12-digit Aadhaar ID, optional/unknown for many records"
    )
    father_or_guardian_name = models.CharField(max_length=150, blank=True)
    occupation = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "person"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["aadhaar_number"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class PersonCaseRole(models.Model):
    """
    Records the role a Person played in a specific InvestigationCase.
    This is what replaces separate Victim/Suspect/Witness/Accused tables.
    """

    class Role(models.TextChoices):
        VICTIM = "VICTIM", "Victim"
        SUSPECT = "SUSPECT", "Suspect"
        WITNESS = "WITNESS", "Witness"
        ACCUSED = "ACCUSED", "Accused"
        COMPLAINANT = "COMPLAINANT", "Complainant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="case_roles")
    case = models.ForeignKey(InvestigationCase, on_delete=models.CASCADE, related_name="person_roles")
    role = models.CharField(max_length=15, choices=Role.choices)
    added_by = models.ForeignKey(Officer, on_delete=models.PROTECT, related_name="person_roles_added")
    remarks = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "person_case_role"
        unique_together = ("person", "case", "role")
        indexes = [
            models.Index(fields=["case"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.person} - {self.role} in {self.case.case_number}"


class Phone(models.Model):
    """One-to-many: a person can have multiple phone numbers."""

    class PhoneType(models.TextChoices):
        MOBILE = "MOBILE", "Mobile"
        HOME = "HOME", "Home"
        WORK = "WORK", "Work"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="phones")
    phone_number = models.CharField(max_length=15, validators=[phone_validator])
    phone_type = models.CharField(max_length=10, choices=PhoneType.choices, default=PhoneType.MOBILE)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "phone"
        indexes = [
            models.Index(fields=["phone_number"]),
            models.Index(fields=["person"]),
        ]

    def __str__(self):
        return self.phone_number


class Email(models.Model):
    """One-to-many: a person can have multiple email addresses."""

    class EmailType(models.TextChoices):
        PERSONAL = "PERSONAL", "Personal"
        WORK = "WORK", "Work"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="emails")
    email = models.EmailField()
    email_type = models.CharField(max_length=10, choices=EmailType.choices, default=EmailType.PERSONAL)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["person"]),
        ]

    def __str__(self):
        return self.email


class Address(models.Model):
    """One-to-many: a person can have multiple addresses (permanent, current, work, etc.)."""

    class AddressType(models.TextChoices):
        PERMANENT = "PERMANENT", "Permanent"
        CURRENT = "CURRENT", "Current"
        WORK = "WORK", "Work"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="addresses")
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, default="Karnataka")
    pincode = models.CharField(max_length=10, blank=True)
    address_type = models.CharField(max_length=10, choices=AddressType.choices, default=AddressType.CURRENT)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "address"
        indexes = [
            models.Index(fields=["person"]),
            models.Index(fields=["district"]),
        ]

    def __str__(self):
        return f"{self.address_line}, {self.city}"