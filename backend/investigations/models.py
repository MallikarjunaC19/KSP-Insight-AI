"""
KSP Insight AI — Module 3: Investigation
App: investigations

Entities: InvestigationCase, Investigation, InvestigationStep, Arrest,
          Chargesheet, CourtCase

"""

import uuid
from django.db import models
from accounts.models import Officer
from crimes.models import FIR


class InvestigationCase(models.Model):
    """The formal case file. One per FIR."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_INVESTIGATION = "UNDER_INVESTIGATION", "Under Investigation"
        CHARGESHEET_FILED = "CHARGESHEET_FILED", "Chargesheet Filed"
        IN_COURT = "IN_COURT", "In Court"
        CLOSED = "CLOSED", "Closed"
        DROPPED = "DROPPED", "Dropped"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=50, unique=True, help_text="e.g. CR-2026-00123")
    fir = models.OneToOneField(FIR, on_delete=models.PROTECT, related_name="investigation_case")
    lead_officer = models.ForeignKey(
        Officer, on_delete=models.PROTECT, related_name="cases_leading",
        help_text="Current officer in charge of the case"
    )
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    opened_date = models.DateField(auto_now_add=True)
    closed_date = models.DateField(null=True, blank=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "investigation_case"
        ordering = ["-opened_date"]
        verbose_name = "Investigation Case"
        verbose_name_plural = "Investigation Cases"
        indexes = [
            models.Index(fields=["case_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.case_number


class Investigation(models.Model):
    """
    One investigation phase/assignment under a case. Multiple rows per
    case if reassigned or reopened, preserving history.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        TRANSFERRED = "TRANSFERRED", "Transferred"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(InvestigationCase, on_delete=models.CASCADE, related_name="investigations")
    officer = models.ForeignKey(Officer, on_delete=models.PROTECT, related_name="investigations_handled")
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    findings = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "investigation"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["case"]),
            models.Index(fields=["officer"]),
        ]

    def __str__(self):
        return f"{self.case.case_number} - {self.officer} ({self.status})"


class InvestigationStep(models.Model):
    """Granular chronological case-diary entry under an investigation phase."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investigation = models.ForeignKey(
        Investigation, on_delete=models.CASCADE, related_name="steps"
    )
    description = models.TextField()
    performed_by = models.ForeignKey(Officer, on_delete=models.PROTECT, related_name="steps_performed")
    step_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "investigation_step"
        ordering = ["step_date"]
        indexes = [
            models.Index(fields=["investigation"]),
            models.Index(fields=["step_date"]),
        ]

    def __str__(self):
        return f"{self.investigation.case.case_number} step @ {self.step_date}"


class Arrest(models.Model):
    """
    An arrest made in connection with a case.

    TODO (Module 5 dependency): arrested_person_name/details are
    temporary plain text. Once Person Management exists, replace with
    ForeignKey(Person) + a PersonCaseRole(role='ACCUSED') entry.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(InvestigationCase, on_delete=models.PROTECT, related_name="arrests")
    arresting_officer = models.ForeignKey(Officer, on_delete=models.PROTECT, related_name="arrests_made")

    arrested_person_name = models.CharField(max_length=150)
    arrested_person_details = models.TextField(
        blank=True, help_text="Temporary free-text: age, address, ID details, etc."
    )

    arrest_date = models.DateTimeField()
    arrest_location = models.CharField(max_length=255, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "arrest"
        ordering = ["-arrest_date"]
        indexes = [
            models.Index(fields=["case"]),
        ]

    def __str__(self):
        return f"{self.arrested_person_name} - {self.case.case_number}"


class Chargesheet(models.Model):
    """
    Formal chargesheet filed for a case. Plain FK (not OneToOne) because
    supplementary chargesheets are legally common for the same case.

    TODO (Judicial module dependency): court_referred is temporary plain
    text until a Court master table exists.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        FILED = "FILED", "Filed"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(InvestigationCase, on_delete=models.PROTECT, related_name="chargesheets")
    filed_by = models.ForeignKey(Officer, on_delete=models.PROTECT, related_name="chargesheets_filed")
    court_referred = models.CharField(max_length=200, blank=True, help_text="Temporary — court name as text")
    filing_date = models.DateField()
    sections_summary = models.TextField(help_text="Summary of sections/charges applied")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chargesheet"
        ordering = ["-filing_date"]
        indexes = [
            models.Index(fields=["case"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Chargesheet - {self.case.case_number} ({self.status})"


class CourtCase(models.Model):
    """
    Court proceeding opened against an accepted chargesheet.

    TODO (Judicial module dependency): court_name is temporary plain text
    until a Court master table exists.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ONGOING = "ONGOING", "Ongoing"
        ADJOURNED = "ADJOURNED", "Adjourned"
        JUDGMENT_RESERVED = "JUDGMENT_RESERVED", "Judgment Reserved"
        DISPOSED = "DISPOSED", "Disposed"
        CONVICTED = "CONVICTED", "Convicted"
        ACQUITTED = "ACQUITTED", "Acquitted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chargesheet = models.OneToOneField(
        Chargesheet, on_delete=models.PROTECT, related_name="court_case"
    )
    court_case_number = models.CharField(max_length=50, unique=True)
    court_name = models.CharField(max_length=200, blank=True, help_text="Temporary — court name as text")
    filing_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    next_hearing_date = models.DateField(null=True, blank=True)
    verdict = models.TextField(blank=True)
    verdict_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "court_case"
        ordering = ["-filing_date"]
        verbose_name = "Court Case"
        verbose_name_plural = "Court Cases"
        indexes = [
            models.Index(fields=["court_case_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.court_case_number