"""
Tests for the reminders app.

Covers: CRUD, ownership scoping, validation (future time, sent reminders),
        cancel action, Celery task dispatch logic, email content.
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from applications.models import JobApplication
from reminders.models import Reminder
from reminders.tasks import dispatch_due_reminders, send_reminder_email

User = get_user_model()


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="usera@example.com", password="Pass123!",
        first_name="Jane", last_name="Seeker",
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="userb@example.com", password="Pass123!",
        first_name="Bob", last_name="Other",
    )


def auth_client_for(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
    return client


@pytest.fixture
def client_a(user_a):
    return auth_client_for(user_a)


@pytest.fixture
def client_b(user_b):
    return auth_client_for(user_b)


@pytest.fixture
def application_a(db, user_a):
    return JobApplication.objects.create(
        user=user_a,
        company_name="Acme Corp",
        job_title="Data Engineer",
        status=JobApplication.Status.APPLIED,
        applied_date="2024-06-01",
    )


@pytest.fixture
def application_b(db, user_b):
    return JobApplication.objects.create(
        user=user_b,
        company_name="Beta Ltd",
        job_title="Analyst",
        status=JobApplication.Status.SAVED,
    )


@pytest.fixture
def future_reminder(db, user_a, application_a):
    return Reminder.objects.create(
        user=user_a,
        application=application_a,
        reminder_type=Reminder.ReminderType.FOLLOW_UP,
        remind_at=timezone.now() + timedelta(days=2),
        message="Send follow-up email.",
    )


@pytest.fixture
def due_reminder(db, user_a, application_a):
    return Reminder.objects.create(
        user=user_a,
        application=application_a,
        reminder_type=Reminder.ReminderType.GENERAL,
        remind_at=timezone.now() - timedelta(minutes=5),
    )


@pytest.fixture
def sent_reminder(db, user_a, application_a):
    r = Reminder.objects.create(
        user=user_a,
        application=application_a,
        reminder_type=Reminder.ReminderType.DEADLINE,
        remind_at=timezone.now() - timedelta(hours=1),
        is_sent=True,
        sent_at=timezone.now() - timedelta(hours=1),
    )
    return r


def list_url():
    return reverse("api_v1:reminders:reminder-list")


def detail_url(pk):
    return reverse("api_v1:reminders:reminder-detail", kwargs={"pk": str(pk)})


def cancel_url(pk):
    return reverse("api_v1:reminders:reminder-cancel", kwargs={"pk": str(pk)})


# ─── CRUD ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreateReminder:

    def test_create_future_reminder_success(self, client_a, application_a):
        payload = {
            "application": str(application_a.id),
            "reminder_type": "follow_up",
            "remind_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "message": "Check in with recruiter.",
        }
        response = client_a.post(list_url(), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["reminder_type"] == "follow_up"
        assert response.data["is_sent"] is False

    def test_create_past_reminder_rejected(self, client_a, application_a):
        payload = {
            "application": str(application_a.id),
            "reminder_type": "general",
            "remind_at": (timezone.now() - timedelta(hours=1)).isoformat(),
        }
        response = client_a.post(list_url(), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "remind_at" in response.data

    def test_cannot_create_reminder_for_other_users_application(self, client_a, application_b):
        payload = {
            "application": str(application_b.id),
            "reminder_type": "general",
            "remind_at": (timezone.now() + timedelta(days=1)).isoformat(),
        }
        response = client_a.post(list_url(), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestListReminders:

    def test_user_sees_only_own_reminders(self, client_a, future_reminder, db, user_b, application_b):
        other = Reminder.objects.create(
            user=user_b, application=application_b,
            remind_at=timezone.now() + timedelta(days=1),
        )
        response = client_a.get(list_url())
        ids = [r["id"] for r in response.data["results"]]
        assert str(future_reminder.id) in ids
        assert str(other.id) not in ids

    def test_filter_by_is_sent(self, client_a, future_reminder, sent_reminder):
        response = client_a.get(list_url(), {"is_sent": "true"})
        assert all(r["is_sent"] for r in response.data["results"])

    def test_filter_by_application(self, client_a, future_reminder, application_a):
        response = client_a.get(list_url(), {"application": str(application_a.id)})
        assert all(r["application"] == str(application_a.id) for r in response.data["results"])


@pytest.mark.django_db
class TestUpdateReminder:

    def test_reschedule_future_reminder(self, client_a, future_reminder):
        new_time = (timezone.now() + timedelta(days=5)).isoformat()
        response = client_a.patch(detail_url(future_reminder.id), {"remind_at": new_time}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_cannot_edit_sent_reminder(self, client_a, sent_reminder):
        response = client_a.patch(
            detail_url(sent_reminder.id),
            {"message": "Updated message"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancel_action_deactivates_reminder(self, client_a, future_reminder):
        response = client_a.post(cancel_url(future_reminder.id))
        assert response.status_code == status.HTTP_200_OK
        future_reminder.refresh_from_db()
        assert future_reminder.is_active is False

    def test_cancel_sent_reminder_rejected(self, client_a, sent_reminder):
        response = client_a.post(cancel_url(sent_reminder.id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─── Celery Tasks ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDispatchDueReminders:

    def test_dispatch_queues_due_reminders(self, due_reminder):
        with patch("reminders.tasks.send_reminder_email.apply_async") as mock_apply:
            result = dispatch_due_reminders.apply().get()
            mock_apply.assert_called_once_with(
                args=[str(due_reminder.id)], queue="reminders"
            )
            assert result["dispatched"] == 1

    def test_dispatch_skips_future_reminders(self, future_reminder):
        with patch("reminders.tasks.send_reminder_email.apply_async") as mock_apply:
            result = dispatch_due_reminders.apply().get()
            mock_apply.assert_not_called()
            assert result["dispatched"] == 0

    def test_dispatch_skips_sent_reminders(self, sent_reminder):
        with patch("reminders.tasks.send_reminder_email.apply_async") as mock_apply:
            dispatch_due_reminders.apply().get()
            mock_apply.assert_not_called()


@pytest.mark.django_db
class TestSendReminderEmailTask:

    def test_sends_email_and_marks_sent(self, due_reminder):
        result = send_reminder_email.apply(args=[str(due_reminder.id)]).get()
        assert result["status"] == "sent"
        due_reminder.refresh_from_db()
        assert due_reminder.is_sent is True
        assert due_reminder.sent_at is not None
        # Django test runner captures outbox
        assert len(mail.outbox) == 1
        assert due_reminder.application.company_name in mail.outbox[0].subject

    def test_email_sent_to_correct_address(self, due_reminder):
        send_reminder_email.apply(args=[str(due_reminder.id)]).get()
        assert mail.outbox[0].to == [due_reminder.user.email]

    def test_skips_already_sent_reminder(self, sent_reminder):
        result = send_reminder_email.apply(args=[str(sent_reminder.id)]).get()
        assert result["status"] == "skipped"
        assert len(mail.outbox) == 0

    def test_handles_nonexistent_reminder_gracefully(self, db):
        result = send_reminder_email.apply(args=["00000000-0000-0000-0000-000000000000"]).get()
        assert result["status"] == "not_found"

    def test_double_send_protection(self, due_reminder):
        """Simulate two workers racing — second should be skipped."""
        send_reminder_email.apply(args=[str(due_reminder.id)]).get()
        send_reminder_email.apply(args=[str(due_reminder.id)]).get()
        # Only one email despite two task executions
        assert len(mail.outbox) == 1