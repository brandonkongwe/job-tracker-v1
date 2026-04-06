import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Reminder(models.Model):
    """
    A user-defined reminder attached to one job application.

    Fields
    ------
    remind_at   : exact datetime when the email should fire
    message     : optional custom note included in the email body
    is_sent     : flipped to True once the Celery task dispatches the email
    sent_at     : timestamp of successful dispatch
    is_active   : allows the user to cancel a reminder without deleting it
    created_at  : audit timestamp
    """

    class ReminderType(models.TextChoices):
        FOLLOW_UP       = "follow_up",      _("Follow Up")
        INTERVIEW_PREP  = "interview_prep", _("Interview Prep")
        DEADLINE        = "deadline",       _("Deadline")
        GENERAL         = "general",        _("General")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reminders",
        db_index=True,
    )
    application = models.ForeignKey(
        "applications.JobApplication",
        on_delete=models.CASCADE,
        related_name="reminders",
    )

    reminder_type = models.CharField(
        _("reminder type"),
        max_length=20,
        choices=ReminderType.choices,
        default=ReminderType.GENERAL,
    )
    remind_at = models.DateTimeField(
        _("remind at"),
        db_index=True,
        help_text=_("Exact date and time to send the reminder email (UTC)."),
    )
    message = models.TextField(
        _("message"),
        blank=True,
        default="",
        help_text=_("Optional note to include in the reminder email."),
    )

    # Dispatch state
    is_sent  = models.BooleanField(_("sent"), default=False, db_index=True)
    sent_at  = models.DateTimeField(_("sent at"), null=True, blank=True)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_index=True,
        help_text=_("Uncheck to cancel this reminder without deleting it."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("reminder")
        verbose_name_plural = _("reminders")
        ordering = ["remind_at"]
        indexes = [
            # The Celery task's primary query: due, unsent, active reminders
            models.Index(
                fields=["is_sent", "is_active", "remind_at"],
                name="reminders_due_idx",
            ),
        ]

    def __str__(self):
        return (
            f"[{self.get_reminder_type_display()}] "
            f"{self.application.job_title} @ {self.application.company_name} "
            f"— {self.remind_at:%Y-%m-%d %H:%M} UTC"
        )

    @property
    def is_due(self):
        return self.is_active and not self.is_sent and self.remind_at <= timezone.now()

    @property
    def is_overdue(self):
        """True if the reminder is due but more than 24h have passed."""
        if not self.is_due:
            return False
        return (timezone.now() - self.remind_at).total_seconds() > 86400

    def mark_sent(self):
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=["is_sent", "sent_at", "updated_at"])