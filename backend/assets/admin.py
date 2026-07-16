from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Vehicle, VehicleOwnership, Property, Weapon


class VehicleOwnershipInline(admin.TabularInline):
    """Shows ownership history directly on the vehicle page."""
    model = VehicleOwnership
    extra = 1


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "vehicle_type", "make", "model", "is_stolen", "status")
    list_filter = ("vehicle_type", "status", "is_stolen")
    search_fields = ("registration_number", "chassis_number", "engine_number")
    inlines = [VehicleOwnershipInline]


@admin.register(VehicleOwnership)
class VehicleOwnershipAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "owner", "ownership_type", "start_date", "end_date")
    list_filter = ("ownership_type",)
    search_fields = ("vehicle__registration_number", "owner__first_name", "owner__last_name")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("property_type", "description", "owner", "case", "status", "estimated_value")
    list_filter = ("property_type", "status")
    search_fields = ("description", "owner__first_name", "owner__last_name", "case__case_number")


@admin.register(Weapon)
class WeaponAdmin(admin.ModelAdmin):
    list_display = ("weapon_type", "serial_number", "license_number", "owner", "case", "status")
    list_filter = ("weapon_type", "status")
    search_fields = ("serial_number", "license_number", "owner__first_name", "case__case_number")