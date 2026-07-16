from django.contrib import admin
from .models import Role, Department, Rank, PoliceStation, Officer


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_at")
    search_fields = ("name", "code")


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ("name", "hierarchy_level")
    ordering = ("hierarchy_level",)


@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "department", "district", "state")
    search_fields = ("name", "code", "district")
    list_filter = ("department", "district", "state")


@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ("badge_number", "first_name", "last_name", "rank", "police_station", "is_active")
    search_fields = ("badge_number", "first_name", "last_name")
    list_filter = ("police_station", "rank", "is_active")
