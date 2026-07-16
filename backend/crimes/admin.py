from django.contrib import admin
from .models import CrimeCategory, Crime, FIR, FIRCrime
from accounts.admin_mixins import ScopedAdminMixin


@admin.register(CrimeCategory)
class CrimeCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code_type", "section_code", "severity")
    list_filter = ("code_type", "severity")
    search_fields = ("name", "section_code")


class FIRCrimeInline(admin.TabularInline):
    """Lets you add/view linked crimes directly inside the FIR admin page."""
    model = FIRCrime
    extra = 1


@admin.register(Crime)
class CrimeAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "police_station"
    list_display = ("category", "police_station", "reported_by", "date_of_occurrence", "status")
    list_filter = ("status", "police_station", "category")
    search_fields = ("description", "location_description")
    date_hierarchy = "date_of_occurrence"


@admin.register(FIR)
class FIRAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "police_station"
    list_display = ("fir_number", "police_station", "registered_by", "complainant_name", "status", "date_filed")
    list_filter = ("status", "police_station")
    search_fields = ("fir_number", "complainant_name", "complainant_phone")
    date_hierarchy = "date_filed"
    inlines = [FIRCrimeInline]


@admin.register(FIRCrime)
class FIRCrimeAdmin(admin.ModelAdmin):
    list_display = ("fir", "crime", "is_primary_offense")
    list_filter = ("is_primary_offense",)