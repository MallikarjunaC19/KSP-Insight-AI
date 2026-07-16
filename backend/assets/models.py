"""
KSP Insight AI — Module 5: Assets
App: assets

Entities: Vehicle, VehicleOwnership, Property, Weapon

Design notes:
- Vehicle is master-ish data about the vehicle itself (registration,
  chassis, engine numbers) — separate from who owns it.
- VehicleOwnership is a junction table tracking ownership over time
  (current + previous owners), since vehicles change hands and
  investigations often need to trace ownership history, not just
  "who owns it now."
- Property and Weapon both optionally link to an owner (Person) and
  optionally to an InvestigationCase — "optionally" because not every
  recorded property/weapon is tied to an active case (e.g. a licensed
  weapon registry entry with no case), and not every one has a known
  owner (e.g. unclaimed recovered property).
"""

import uuid
from django.db import models
from persons.models import Person
from investigations.models import InvestigationCase


class Vehicle(models.Model):
    """A registered or identified vehicle."""

    class VehicleType(models.TextChoices):
        CAR = "CAR", "Car"
        BIKE = "BIKE", "Bike / Motorcycle"
        TRUCK = "TRUCK", "Truck"
        BUS = "BUS", "Bus"
        AUTO = "AUTO", "Auto Rickshaw"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SEIZED = "SEIZED", "Seized"
        IMPOUNDED = "IMPOUNDED", "Impounded"
        RECOVERED = "RECOVERED", "Recovered"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices, default=VehicleType.CAR)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    chassis_number = models.CharField(max_length=50, blank=True)
    engine_number = models.CharField(max_length=50, blank=True)
    is_stolen = models.BooleanField(default=False)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vehicle"
        ordering = ["registration_number"]
        indexes = [
            models.Index(fields=["registration_number"]),
            models.Index(fields=["is_stolen"]),
        ]

    def __str__(self):
        return self.registration_number


class VehicleOwnership(models.Model):
    """Tracks who owns/owned a vehicle, and when — supports ownership history."""

    class OwnershipType(models.TextChoices):
        CURRENT = "CURRENT", "Current"
        PREVIOUS = "PREVIOUS", "Previous"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="ownerships")
    owner = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="vehicle_ownerships")
    ownership_type = models.CharField(max_length=10, choices=OwnershipType.choices, default=OwnershipType.CURRENT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vehicle_ownership"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["vehicle"]),
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return f"{self.owner} -> {self.vehicle} ({self.ownership_type})"


class Property(models.Model):
    """Movable/immovable property — reported stolen, recovered, or seized as part of a case."""

    class PropertyType(models.TextChoices):
        LAND = "LAND", "Land"
        BUILDING = "BUILDING", "Building"
        JEWELRY = "JEWELRY", "Jewelry"
        ELECTRONICS = "ELECTRONICS", "Electronics"
        CASH = "CASH", "Cash"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        REPORTED_STOLEN = "REPORTED_STOLEN", "Reported Stolen"
        RECOVERED = "RECOVERED", "Recovered"
        SEIZED = "SEIZED", "Seized"
        RELEASED = "RELEASED", "Released"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property_type = models.CharField(max_length=15, choices=PropertyType.choices)
    description = models.TextField()
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    owner = models.ForeignKey(
        Person, on_delete=models.SET_NULL, null=True, blank=True, related_name="properties"
    )
    case = models.ForeignKey(
        InvestigationCase, on_delete=models.SET_NULL, null=True, blank=True, related_name="properties"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REPORTED_STOLEN)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "property"
        verbose_name_plural = "Properties"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["case"]),
        ]

    def __str__(self):
        return f"{self.property_type} - {self.description[:40]}"


class Weapon(models.Model):
    """A firearm, knife, explosive, or other weapon — licensed or seized."""

    class WeaponType(models.TextChoices):
        FIREARM = "FIREARM", "Firearm"
        KNIFE = "KNIFE", "Knife"
        EXPLOSIVE = "EXPLOSIVE", "Explosive"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        LICENSED = "LICENSED", "Licensed"
        ILLEGAL = "ILLEGAL", "Illegal"
        SEIZED = "SEIZED", "Seized"
        RELEASED = "RELEASED", "Released"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    weapon_type = models.CharField(max_length=10, choices=WeaponType.choices)
    license_number = models.CharField(max_length=50, blank=True, help_text="Blank if unlicensed/illegal")
    serial_number = models.CharField(max_length=50, blank=True)
    owner = models.ForeignKey(
        Person, on_delete=models.SET_NULL, null=True, blank=True, related_name="weapons"
    )
    case = models.ForeignKey(
        InvestigationCase, on_delete=models.SET_NULL, null=True, blank=True, related_name="weapons"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ILLEGAL)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weapon"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["case"]),
        ]

    def __str__(self):
        return f"{self.weapon_type} - {self.serial_number or 'no serial'}"