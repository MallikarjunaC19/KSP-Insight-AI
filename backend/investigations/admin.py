from django.contrib import admin
from .models import (
    InvestigationCase,
    Investigation,
    InvestigationStep,
    Arrest,
    Chargesheet,
    CourtCase,
)
from accounts.admin_mixins import ScopedAdminMixin


class InvestigationInline(admin.TabularInline):
    """Shows investigation phases directly on the case page."""
    model = Investigation
    extra = 1
    fields = ("officer", "start_date", "end_date", "status")
    readonly_fields = ("start_date",)


class ArrestInline(admin.TabularInline):
    model = Arrest
    extra = 0
    fields = ("arrested_person_name", "arresting_officer", "arrest_date")


class ChargesheetInline(admin.TabularInline):
    model = Chargesheet
    extra = 0
    fields = ("filed_by", "filing_date", "status")


@admin.register(InvestigationCase)
class InvestigationCaseAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "fir__police_station"
    list_display = ("case_number", "fir", "lead_officer", "status", "priority", "opened_date")
    list_filter = ("status", "priority")
    search_fields = ("case_number", "fir__fir_number")
    date_hierarchy = "opened_date"
    inlines = [InvestigationInline, ArrestInline, ChargesheetInline]


class InvestigationStepInline(admin.TabularInline):
    """Shows case-diary steps directly on the investigation page."""
    model = InvestigationStep
    extra = 1
    fields = ("description", "performed_by", "step_date")


@admin.register(Investigation)
class InvestigationAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "case__fir__police_station"
    list_display = ("case", "officer", "start_date", "end_date", "status")
    list_filter = ("status",)
    search_fields = ("case__case_number",)
    inlines = [InvestigationStepInline]


@admin.register(InvestigationStep)
class InvestigationStepAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "investigation__case__fir__police_station"
    list_display = ("investigation", "performed_by", "step_date")
    list_filter = ("performed_by",)
    date_hierarchy = "step_date"


@admin.register(Arrest)
class ArrestAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "case__fir__police_station"
    list_display = ("arrested_person_name", "case", "arresting_officer", "arrest_date")
    search_fields = ("arrested_person_name", "case__case_number")
    date_hierarchy = "arrest_date"


@admin.register(Chargesheet)
class ChargesheetAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "case__fir__police_station"
    list_display = ("case", "filed_by", "filing_date", "status")
    list_filter = ("status",)
    search_fields = ("case__case_number",)
    date_hierarchy = "filing_date"


@admin.register(CourtCase)
class CourtCaseAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "chargesheet__case__fir__police_station"
    list_display = ("court_case_number", "chargesheet", "court_name", "status", "next_hearing_date")
    list_filter = ("status",)
    search_fields = ("court_case_number", "court_name")
    date_hierarchy = "filing_date"