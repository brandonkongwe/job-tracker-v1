from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Document, JobApplication, StatusHistory


class StatusHistorySerializer(serializers.ModelSerializer):
    from_status_display = serializers.CharField(source="get_from_status_display", read_only=True)
    to_status_display   = serializers.CharField(source="get_to_status_display",   read_only=True)

    class Meta:
        model  = StatusHistory
        fields = [
            "id",
            "from_status",
            "from_status_display",
            "to_status",
            "to_status_display",
            "changed_at",
            "note",
        ]
        read_only_fields = fields


class DocumentSerializer(serializers.ModelSerializer):
    file_size_display = serializers.CharField(read_only=True)
    file_url          = serializers.SerializerMethodField()

    class Meta:
        model  = Document
        fields = [
            "id",
            "document_type",
            "file",
            "file_url",
            "original_filename",
            "file_size_display",
            "uploaded_at",
        ]
        read_only_fields = ["id", "original_filename", "file_size_display", "uploaded_at"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def validate_file(self, value):
        """Run extension + size validators and capture original filename."""
        # Validators on the model field run automatically, but we also
        # capture the original name here before Django renames it.
        self._original_filename = value.name
        return value

    def create(self, validated_data):
        validated_data["original_filename"] = getattr(self, "_original_filename", "")
        return super().create(validated_data)


class JobApplicationListSerializer(serializers.ModelSerializer):
    """
    Compact representation for paginated list views.
    Avoids N+1 by not including nested relations.
    Status display label included for frontend rendering.
    """

    status_display   = serializers.CharField(source="get_status_display",    read_only=True)
    work_mode_display = serializers.CharField(source="get_work_mode_display", read_only=True)
    salary_range     = serializers.CharField(source="salary_range_display",   read_only=True)
    document_count   = serializers.SerializerMethodField()

    class Meta:
        model  = JobApplication
        fields = [
            "id",
            "company_name",
            "job_title",
            "location",
            "work_mode",
            "work_mode_display",
            "status",
            "status_display",
            "salary_range",
            "source",
            "applied_date",
            "interview_date",
            "document_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_document_count(self, obj):
        # Relies on prefetch_related("documents") in the viewset queryset
        return obj.documents.count()


class JobApplicationDetailSerializer(JobApplicationListSerializer):
    """
    Full detail view including nested documents and status history.
    """

    documents      = DocumentSerializer(many=True, read_only=True)
    status_history = StatusHistorySerializer(many=True, read_only=True)

    class Meta(JobApplicationListSerializer.Meta):
        fields = JobApplicationListSerializer.Meta.fields + [
            "job_url",
            "salary_min",
            "salary_max",
            "salary_currency",
            "offer_deadline",
            "source_detail",
            "notes",
            "documents",
            "status_history",
        ]


class JobApplicationWriteSerializer(serializers.ModelSerializer):
    """
    Handles creation and updates.
    On status change, automatically writes a StatusHistory entry.
    User is injected from request.user — never from the payload.
    """

    class Meta:
        model  = JobApplication
        fields = [
            "id",
            "company_name",
            "job_title",
            "job_url",
            "location",
            "work_mode",
            "status",
            "salary_min",
            "salary_max",
            "salary_currency",
            "source",
            "source_detail",
            "applied_date",
            "interview_date",
            "offer_deadline",
            "notes",
        ]
        read_only_fields = ["id"]


    def validate(self, attrs):
        salary_min = attrs.get("salary_min") or (self.instance.salary_min if self.instance else None)
        salary_max = attrs.get("salary_max") or (self.instance.salary_max if self.instance else None)
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError(
                {"salary_min": _("Minimum salary cannot exceed maximum salary.")}
            )

        # applied_date required when moving out of 'saved'
        status = attrs.get("status", getattr(self.instance, "status", None))
        applied_date = attrs.get("applied_date") or getattr(self.instance, "applied_date", None)
        if status not in (JobApplication.Status.SAVED, "") and not applied_date:
            raise serializers.ValidationError(
                {"applied_date": _("Applied date is required once the application moves past 'Saved'.")}
            )
        return attrs


    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        application = super().create(validated_data)

        # Record the initial status in history
        StatusHistory.objects.create(
            application=application,
            from_status="",
            to_status=application.status,
            note="Application created.",
        )
        return application


    def update(self, instance, validated_data):
        old_status = instance.status
        application = super().update(instance, validated_data)
        new_status = application.status

        # Only write a history entry if status actually changed
        if old_status != new_status:
            StatusHistory.objects.create(
                application=application,
                from_status=old_status,
                to_status=new_status,
            )
        return application

    def to_representation(self, instance):
        """Return the full detail representation after write operations."""
        return JobApplicationDetailSerializer(instance, context=self.context).data