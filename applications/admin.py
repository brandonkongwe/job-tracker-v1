from django.contrib import admin

from .models import Document, JobApplication, StatusHistory


class DocumentInline(admin.TabularInline):
    model  = Document
    extra  = 0
    fields = ["document_type", "file", "original_filename", "uploaded_at"]
    readonly_fields = ["original_filename", "uploaded_at"]


class StatusHistoryInline(admin.TabularInline):
    model      = StatusHistory
    extra      = 0
    fields     = ["from_status", "to_status", "changed_at", "note"]
    readonly_fields = ["from_status", "to_status", "changed_at"]
    can_delete = False


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display   = ["job_title", "company_name", "user", "status", "applied_date", "created_at"]
    list_filter    = ["status", "work_mode", "source", "created_at"]
    search_fields  = ["company_name", "job_title", "user__email", "notes"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering       = ["-created_at"]
    inlines        = [DocumentInline, StatusHistoryInline]

    fieldsets = (
        ("Job Info", {"fields": ("id", "user", "company_name", "job_title", "job_url", "location", "work_mode")}),
        ("Pipeline", {"fields": ("status", "applied_date", "interview_date", "offer_deadline")}),
        ("Compensation", {"fields": ("salary_min", "salary_max", "salary_currency")}),
        ("Discovery", {"fields": ("source", "source_detail")}),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ["original_filename", "document_type", "application", "uploaded_at"]
    list_filter   = ["document_type", "uploaded_at"]
    search_fields = ["original_filename", "application__company_name"]
    readonly_fields = ["id", "original_filename", "uploaded_at"]