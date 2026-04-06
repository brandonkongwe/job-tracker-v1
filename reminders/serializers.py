from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from applications.serializers import JobApplicationListSerializer

from .models import Reminder


class ReminderListSerializer(serializers.ModelSerializer):
    """Compact read-only representation for list views."""

    reminder_type_display = serializers.CharField(
        source="get_reminder_type_display", read_only=True
    )
    is_due      = serializers.BooleanField(read_only=True)
    is_overdue  = serializers.BooleanField(read_only=True)

    # Minimal application info inline
    company_name = serializers.CharField(source="application.company_name", read_only=True)
    job_title    = serializers.CharField(source="application.job_title",    read_only=True)

    class Meta:
        model  = Reminder
        fields = [
            "id",
            "application",
            "company_name",
            "job_title",
            "reminder_type",
            "reminder_type_display",
            "remind_at",
            "message",
            "is_sent",
            "sent_at",
            "is_active",
            "is_due",
            "is_overdue",
            "created_at",
        ]
        read_only_fields = fields


class ReminderDetailSerializer(ReminderListSerializer):
    """Full detail with nested application summary."""

    application_detail = JobApplicationListSerializer(source="application", read_only=True)

    class Meta(ReminderListSerializer.Meta):
        fields = ReminderListSerializer.Meta.fields + ["application_detail", "updated_at"]


class ReminderWriteSerializer(serializers.ModelSerializer):
    """
    Handles reminder creation and updates.

    Validates:
    - remind_at must be in the future (on create)
    - application must belong to the requesting user
    - cannot edit a reminder that has already been sent
    """

    class Meta:
        model  = Reminder
        fields = [
            "id",
            "application",
            "reminder_type",
            "remind_at",
            "message",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_application(self, value):
        """Ensure the application belongs to the requesting user."""
        user = self.context["request"].user
        if not user.is_admin and value.user != user:
            raise serializers.ValidationError(
                _("You can only set reminders for your own applications.")
            )
        return value

    def validate_remind_at(self, value):
        """remind_at must be in the future when creating a new reminder."""
        if self.instance is None and value <= timezone.now():
            raise serializers.ValidationError(
                _("Reminder time must be in the future.")
            )
        return value

    def validate(self, attrs):
        """Block edits on already-sent reminders."""
        if self.instance and self.instance.is_sent:
            raise serializers.ValidationError(
                _("Cannot modify a reminder that has already been sent.")
            )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def to_representation(self, instance):
        return ReminderDetailSerializer(instance, context=self.context).data