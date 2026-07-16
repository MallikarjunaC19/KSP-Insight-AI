"""
KSP Insight AI — Module 2: Crime Management
App: crimes

Entities: CrimeCategory, Crime, FIR, FIRCrime

"""

import uuid
from django.db import models
from accounts.models import Officer, PoliceStation
from accounts.validators import phone_validator


class CrimeCategory(models.Model):
    """Master table. One row per offense type / legal section."""

    class Severity(models.TextChoices):
        MINOR = "MINOR", "Minor"
        MODERATE = "MODERATE", "Moderate"
        SEVERE = "SEVERE", "Severe"
        HEINOUS = "HEINOUS", "Heinous"

    class CodeType(models.TextChoices):
        BNS = "BNS", "Bharatiya Nyaya Sanhita"
        IPC = "IPC", "Indian Penal Code (pre-2024, legacy records)"
        IT_ACT = "IT_ACT", "Information Technology Act"
        OTHER = "OTHER", "Other / Special Law"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True, help_text="e.g. Theft, Cyber Fraud, Assault")
    code_type = models.CharField(max_length=10, choices=CodeType.choices, default=CodeType.BNS)
    section_code = models.CharField(max_length=20, help_text="e.g. BNS Section 303")
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MODERATE)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crime_category"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["section_code"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code_type} {self.section_code})"


class Crime(models.Model):
    """One recorded criminal offense instance."""

    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        UNDER_INVESTIGATION = "UNDER_INVESTIGATION", "Under Investigation"
        CHARGESHEET_FILED = "CHARGESHEET_FILED", "Chargesheet Filed"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(CrimeCategory, on_delete=models.PROTECT, related_name="crimes")
    police_station = models.ForeignKey(PoliceStation, on_delete=models.PROTECT, related_name="crimes")
    reported_by = models.ForeignKey(
        Officer, on_delete=models.PROTECT, related_name="crimes_reported"
    )
    description = models.TextField()
    date_of_occurrence = models.DateField()
    time_of_occurrence = models.TimeField(null=True, blank=True)
    location_description = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.REPORTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crime"
        ordering = ["-date_of_occurrence"]
        indexes = [
            models.Index(fields=["police_station"]),
            models.Index(fields=["status"]),
            models.Index(fields=["date_of_occurrence"]),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.date_of_occurrence}"


class FIR(models.Model):
    """
    First Information Report — the formal legal document. Can bundle
    multiple Crime entries via the FIRCrime junction table.
    """

    class Status(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        UNDER_INVESTIGATION = "UNDER_INVESTIGATION", "Under Investigation"
        CHARGESHEET_FILED = "CHARGESHEET_FILED", "Chargesheet Filed"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fir_number = models.CharField(
        max_length=50, unique=True,
        help_text="e.g. 0123/2026 — station code + sequence + year"
    )
    police_station = models.ForeignKey(PoliceStation, on_delete=models.PROTECT, related_name="firs")
    registered_by = models.ForeignKey(
        Officer, on_delete=models.PROTECT, related_name="firs_registered"
    )

    # Temporary complainant fields — see module docstring TODO above.
    complainant_name = models.CharField(max_length=150)
    complainant_phone = models.CharField(max_length=15, blank=True, validators=[phone_validator])

    date_filed = models.DateTimeField(auto_now_add=True)
    incident_date = models.DateField()
    incident_location = models.CharField(max_length=255)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.REGISTERED)
    summary = models.TextField(help_text="Brief narrative of the complaint")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fir"
        ordering = ["-date_filed"]
        indexes = [
            models.Index(fields=["fir_number"]),
            models.Index(fields=["police_station"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.fir_number


class FIRCrime(models.Model):
    """
    Junction table: one FIR can list multiple crimes/sections, and
    (rarely) a crime instance could be referenced by more than one FIR
    amendment — hence a many-to-many with an explicit through table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fir = models.ForeignKey(FIR, on_delete=models.CASCADE, related_name="fir_crimes")
    crime = models.ForeignKey(Crime, on_delete=models.CASCADE, related_name="fir_crimes")
    is_primary_offense = models.BooleanField(
        default=False, help_text="Marks the main/most severe offense in this FIR"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fir_crime"
        unique_together = ("fir", "crime")

    def __str__(self):
        return f"{self.fir.fir_number} -> {self.crime.category.name}"