from django.contrib import admin
from .models import Conversation, ChatMessage, AuditLog, PredictionHistory, GeneratedReport
from .admin_mixins import OwnRecordAdminMixin


class ChatMessageInline(admin.TabularInline):
    """Shows the message thread directly on the conversation page."""
    model = ChatMessage
    extra = 0
    fields = ("sender", "content", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Conversation)
class ConversationAdmin(OwnRecordAdminMixin, admin.ModelAdmin):
    officer_field = "officer"
    list_display = ("title", "officer", "case", "is_active", "started_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "officer__first_name", "officer__last_name")
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    No direct officer_field on ChatMessage itself (it's on the parent
    Conversation) — kept simple/unscoped here since messages are normally
    viewed via the ConversationAdmin inline above, not this list directly.
    """
    list_display = ("conversation", "sender", "short_content", "created_at")
    list_filter = ("sender",)
    search_fields = ("content",)
    date_hierarchy = "created_at"

    def short_content(self, obj):
        return obj.content[:60]


@admin.register(AuditLog)
class AuditLogAdmin(OwnRecordAdminMixin, admin.ModelAdmin):
    """
    Officers see only their own audit trail. DGP/SCRB Analyst see
    everyone's — this is exactly the oversight/compliance use case
    AuditLog exists for.
    """
    officer_field = "officer"
    list_display = ("officer", "action_type", "description", "ip_address", "created_at")
    list_filter = ("action_type",)
    search_fields = ("officer__first_name", "officer__last_name", "description")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False  # audit logs should only ever be written by the system, never manually

    def has_delete_permission(self, request, obj=None):
        return False  # audit trail should never be deletable, even by superuser-adjacent roles


@admin.register(PredictionHistory)
class PredictionHistoryAdmin(OwnRecordAdminMixin, admin.ModelAdmin):
    officer_field = "officer"
    list_display = ("prediction_type", "officer", "case", "confidence_score", "created_at")
    list_filter = ("prediction_type",)
    search_fields = ("officer__first_name", "officer__last_name", "case__case_number")
    date_hierarchy = "created_at"


@admin.register(GeneratedReport)
class GeneratedReportAdmin(OwnRecordAdminMixin, admin.ModelAdmin):
    officer_field = "officer"
    list_display = ("title", "report_type", "officer", "case", "generated_at")
    list_filter = ("report_type",)
    search_fields = ("title", "officer__first_name", "officer__last_name", "case__case_number")
    date_hierarchy = "generated_at"