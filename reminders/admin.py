from django.contrib import admin
from django.utils.html import format_html

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display  = [
        "short_description", "user", "reminder_type",
        "remind_at", "is_sent", "is_active", "sent_at",
    ]
    list_filter   = ["reminder_type", "is_sent", "is_active", "remind_at"]
    search_fields = ["user__email", "application__company_name", "application__job_title", "message"]
    readonly_fields = ["id", "is_sent", "sent_at", "created_at", "updated_at"]
    ordering      = ["remind_at"]

    fieldsets = (
        ("Reminder", {
            "fields": ("id", "user", "application", "reminder_type", "remind_at", "message", "is_active"),
        }),
        ("Dispatch state", {
            "fields": ("is_sent", "sent_at"),
            "classes": ("collapse",),
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def short_description(self, obj):
        return format_html(
            "<strong>{}</strong> @ {}",
            obj.application.job_title,
            obj.application.company_name,
        )
    short_description.short_description = "Application"