"""
KAVACH AI — Module 1: Identity & Administration
App: accounts

Entities: Role, Department, Rank, PoliceStation, Officer

Design decisions carried over from the DB design phase:
- UUID primary keys on all business entities (scalability, no collisions
  across future multi-station / multi-district data merges).
- Master data (Role, Department, Rank, PoliceStation) uses PROTECT on delete
  so you can never accidentally wipe out officers by deleting a lookup row.
- Officer extends Django's built-in User (auth/login) via OneToOne, so you
  get password hashing, sessions, permissions for free instead of
  reinventing auth.
"""

import uuid
from django.conf import settings
from django.db import models
from accounts.validators import phone_validator, badge_number_validator, validate_hierarchy_level


class Role(models.Model):
    """
    Master table. Defines system-level ACCESS roles — separate from Rank
    (which is the police hierarchy title, e.g. 'Inspector'). This is what
    drives data visibility/permissions in the system.
    """

    class RoleCode(models.TextChoices):
        CONSTABLE = "CONSTABLE", "Constable"
        STATION_OFFICER = "STATION_OFFICER", "Station Officer"
        SP_DIG = "SP_DIG", "SP / DIG"
        DGP = "DGP", "DGP"
        SCRB_ANALYST = "SCRB_ANALYST", "SCRB Analyst"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20, choices=RoleCode.choices, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "role"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    """Master table. E.g. Crime Branch, Cyber Cell, Traffic, CID."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code, e.g. CYB, CID")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "department"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Rank(models.Model):
    """
    Master table. Police hierarchy: Constable -> Head Constable -> ASI ->
    SI -> Inspector -> DySP -> SP -> DIG -> IGP -> DGP.
    hierarchy_level lets you sort/compare seniority programmatically
    (e.g. for escalation logic or approval chains later).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    hierarchy_level = models.PositiveSmallIntegerField(
        validators=[validate_hierarchy_level],
        help_text="Lower number = more senior. 1 = DGP, ... , 10 = Constable"
    )

    class Meta:
        db_table = "rank"
        ordering = ["hierarchy_level"]

    def __str__(self):
        return self.name


class PoliceStation(models.Model):
    """
    Master table. Physical station. Includes lat/long since your Feature
    Mapping table lists Hotspot Detection / geospatial analytics as a
    PostgreSQL(+PostGIS-ready) feature.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT,null=True,blank=True, related_name="police_stations")
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="Karnataka")
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "police_station"
        ordering = ["district", "name"]
        indexes = [
            models.Index(fields=["district"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.district})"


class Officer(models.Model):
    """
    Transaction/identity table. One-to-one with Django's auth User so you
    get login, password reset, and permission scaffolding without
    building it yourself. All other modules (Investigation, Evidence,
    Chargesheet, AuditLog, etc.) will FK to Officer, not to User directly.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="officer_profile",
    )
    badge_number = models.CharField(max_length=30, unique=True, validators=[badge_number_validator])
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    rank = models.ForeignKey(Rank, on_delete=models.PROTECT, related_name="officers")
    police_station = models.ForeignKey(
        PoliceStation, on_delete=models.PROTECT, related_name="officers"
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="officers")
    jurisdiction_district = models.CharField(
        max_length=100, blank=True,
        help_text="Only set for SP/DIG roles — the district they oversee. "
                   "Leave blank for Constable/Station Officer (use police_station instead) "
                   "and DGP/SCRB Analyst (state-wide, no district restriction)."
    )
    phone = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    email = models.EmailField(blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "officer"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["badge_number"]),
            models.Index(fields=["police_station"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.badge_number})"
