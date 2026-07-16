from django.contrib import admin
from .models import Person, PersonCaseRole, Phone, Email, Address
from accounts.admin_mixins import ScopedAdminMixin


class PhoneInline(admin.TabularInline):
    model = Phone
    extra = 1


class EmailInline(admin.TabularInline):
    model = Email
    extra = 1


class AddressInline(admin.TabularInline):
    model = Address
    extra = 1


class PersonCaseRoleInline(admin.TabularInline):
    """Shows every case this person has been involved in, right on their profile."""
    model = PersonCaseRole
    extra = 0
    fields = ("case", "role", "added_by", "remarks")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "gender", "date_of_birth", "aadhaar_number")
    search_fields = ("first_name", "last_name", "aadhaar_number")
    list_filter = ("gender", "nationality")
    inlines = [PhoneInline, EmailInline, AddressInline, PersonCaseRoleInline]


@admin.register(PersonCaseRole)
class PersonCaseRoleAdmin(ScopedAdminMixin, admin.ModelAdmin):
    station_field = "case__fir__police_station"
    list_display = ("person", "case", "role", "added_by", "added_at")
    list_filter = ("role",)
    search_fields = ("person__first_name", "person__last_name", "case__case_number")
    date_hierarchy = "added_at"


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "person", "phone_type", "is_primary")
    search_fields = ("phone_number", "person__first_name", "person__last_name")


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("email", "person", "email_type", "is_primary")
    search_fields = ("email", "person__first_name", "person__last_name")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("address_line", "city", "district", "person", "address_type")
    list_filter = ("district", "address_type")
    search_fields = ("address_line", "city", "person__first_name", "person__last_name")