"""
Celery tasks for the reminders app.

send_reminder_email   — sends a single reminder email and marks it sent
dispatch_due_reminders — beat task: queries all due reminders and fans out
                         individual send tasks. Runs every minute via Celery Beat.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,       # 60s, 120s, 240s
    retry_backoff_max=600,  # cap at 10 minutes
    acks_late=True,         # only ack after the task completes (safer for emails)
    queue="reminders",
)
def send_reminder_email(self, reminder_id: str) -> dict:
    """
    Send a single reminder email for the given reminder_id.

    Returns a status dict for logging / result inspection.
    Uses select_for_update inside a transaction to prevent double-sending
    in case two workers pick up the same task concurrently.
    """
    from .models import Reminder  

    try:
        with transaction.atomic():
            try:
                reminder = (
                    Reminder.objects
                    .select_for_update(nowait=True)
                    .select_related("user", "application")
                    .get(id=reminder_id)
                )
            except Reminder.DoesNotExist:
                logger.warning("send_reminder_email: reminder %s not found.", reminder_id)
                return {"status": "not_found", "reminder_id": reminder_id}

            # Guard: skip if already sent or deactivated since the task was queued
            if reminder.is_sent or not reminder.is_active:
                logger.info(
                    "send_reminder_email: skipping reminder %s (sent=%s active=%s).",
                    reminder_id, reminder.is_sent, reminder.is_active,
                )
                return {"status": "skipped", "reminder_id": reminder_id}

            # Build email context
            app  = reminder.application
            user = reminder.user
            context = {
                "user_first_name":    user.first_name,
                "job_title":          app.job_title,
                "company_name":       app.company_name,
                "application_status": app.get_status_display(),
                "application_location": app.location,
                "applied_date":       app.applied_date.strftime("%d %b %Y") if app.applied_date else None,
                "message":            reminder.message,
                "reminder_type":      reminder.reminder_type,
                "reminder_type_display": reminder.get_reminder_type_display(),
                "application_url":    f"{settings.FRONTEND_URL}/applications/{app.id}",
                "frontend_url":       settings.FRONTEND_URL,
            }

            # Render both text and HTML
            text_body = render_to_string("reminders/reminder_email.txt", context)
            html_body = render_to_string("reminders/reminder_email.html", context)

            subject = (
                f"[{reminder.get_reminder_type_display()}] "
                f"Reminder: {app.job_title} at {app.company_name}"
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_body, "text/html")
            email.send(fail_silently=False)

            # Mark as sent inside the same transaction
            reminder.mark_sent()

        logger.info(
            "send_reminder_email: sent reminder %s to %s for '%s' @ '%s'.",
            reminder_id, user.email, app.job_title, app.company_name,
        )
        return {"status": "sent", "reminder_id": reminder_id, "to": user.email}

    except Exception as exc:
        logger.error(
            "send_reminder_email: failed for reminder %s — %s. Retrying…",
            reminder_id, exc,
        )
        raise  # triggers autoretry


@shared_task(
    bind=True,
    queue="default",
    name="reminders.dispatch_due_reminders",
)
def dispatch_due_reminders(self) -> dict:
    """
    Beat task — runs every minute via Celery Beat.

    Finds all reminders that are:
      - active (is_active=True)
      - not yet sent (is_sent=False)
      - due now or in the past (remind_at <= now)

    For each, fires an individual send_reminder_email task.
    This keeps the beat task fast and stateless.
    """
    from .models import Reminder  # local import

    now = timezone.now()
    due_ids = list(
        Reminder.objects
        .filter(is_active=True, is_sent=False, remind_at__lte=now)
        .values_list("id", flat=True)
    )

    if not due_ids:
        return {"dispatched": 0}

    for reminder_id in due_ids:
        send_reminder_email.apply_async(
            args=[str(reminder_id)],
            queue="reminders",
        )

    logger.info("dispatch_due_reminders: dispatched %d reminder tasks.", len(due_ids))
    return {"dispatched": len(due_ids), "reminder_ids": [str(r) for r in due_ids]}