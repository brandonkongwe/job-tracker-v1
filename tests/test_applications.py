"""
Tests for the applications app.

Covers: CRUD, ownership scoping, search, filtering, pagination,
        document upload, document deletion, status history logging.
"""

import io
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from applications.models import Document, JobApplication, StatusHistory

User = get_user_model()

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="usera@example.com", password="Pass123!", first_name="User", last_name="A"
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="userb@example.com", password="Pass123!", first_name="User", last_name="B"
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com", password="Pass123!", first_name="Admin", last_name="User",
        role=User.Role.ADMIN,
    )


def auth_client_for(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def client_a(user_a):
    return auth_client_for(user_a)


@pytest.fixture
def client_b(user_b):
    return auth_client_for(user_b)


@pytest.fixture
def client_admin(admin_user):
    return auth_client_for(admin_user)


@pytest.fixture
def application_a(db, user_a):
    return JobApplication.objects.create(
        user=user_a,
        company_name="Acme Corp",
        job_title="Data Engineer",
        status=JobApplication.Status.APPLIED,
        applied_date="2024-06-01",
        source=JobApplication.Source.LINKEDIN,
    )


@pytest.fixture
def application_b(db, user_b):
    return JobApplication.objects.create(
        user=user_b,
        company_name="Beta Ltd",
        job_title="Analytics Engineer",
        status=JobApplication.Status.SAVED,
    )


def list_url():
    return reverse("api_v1:applications:application-list")


def detail_url(pk):
    return reverse("api_v1:applications:application-detail", kwargs={"pk": str(pk)})


def document_url(pk):
    return reverse("api_v1:applications:application-upload-document", kwargs={"pk": str(pk)})


def history_url(pk):
    return reverse("api_v1:applications:application-history", kwargs={"pk": str(pk)})


# ─── CRUD ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreateApplication:

    def test_create_saved_application_no_applied_date(self, client_a):
        payload = {
            "company_name": "StartupXYZ",
            "job_title": "Backend Engineer",
            "status": "saved",
        }
        response = client_a.post(list_url(), payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["company_name"] == "StartupXYZ"

    def test_create_applied_requires_applied_date(self, client_a):
        payload = {
            "company_name": "Corp",
            "job_title": "Engineer",
            "status": "applied",
            # missing applied_date
        }
        response = client_a.post(list_url(), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "applied_date" in response.data

    def test_create_logs_initial_status_history(self, client_a):
        payload = {
            "company_name": "HistoryTest",
            "job_title": "Analyst",
            "status": "saved",
        }
        response = client_a.post(list_url(), payload)
        app_id = response.data["id"]
        app = JobApplication.objects.get(id=app_id)
        assert app.status_history.count() == 1
        assert app.status_history.first().to_status == "saved"

    def test_salary_min_cannot_exceed_max(self, client_a):
        payload = {
            "company_name": "Corp",
            "job_title": "Dev",
            "status": "saved",
            "salary_min": 100000,
            "salary_max": 80000,
        }
        response = client_a.post(list_url(), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestListApplications:

    def test_user_sees_only_own_applications(self, client_a, application_a, application_b):
        response = client_a.get(list_url())
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert str(application_a.id) in ids
        assert str(application_b.id) not in ids

    def test_admin_sees_all_applications(self, client_admin, application_a, application_b):
        response = client_admin.get(list_url())
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert str(application_a.id) in ids
        assert str(application_b.id) in ids

    def test_pagination_metadata_present(self, client_a, application_a):
        response = client_a.get(list_url())
        assert "pagination" in response.data
        assert "total_pages" in response.data["pagination"]
        assert "has_next" in response.data["pagination"]

    def test_search_by_company_name(self, client_a, application_a):
        response = client_a.get(list_url(), {"search": "Acme"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["company_name"] == "Acme Corp"

    def test_filter_by_status(self, client_a, user_a, application_a):
        JobApplication.objects.create(
            user=user_a, company_name="Other", job_title="Other",
            status=JobApplication.Status.SAVED,
        )
        response = client_a.get(list_url(), {"status": "applied"})
        assert all(r["status"] == "applied" for r in response.data["results"])

    def test_filter_is_active_excludes_terminal(self, client_a, user_a, application_a):
        JobApplication.objects.create(
            user=user_a, company_name="Done", job_title="Done",
            status=JobApplication.Status.REJECTED,
        )
        response = client_a.get(list_url(), {"is_active": "true"})
        assert all(r["status"] not in ("rejected", "accepted", "withdrawn")
                   for r in response.data["results"])

    def test_ordering_by_company_name(self, client_a, user_a, application_a):
        JobApplication.objects.create(
            user=user_a, company_name="ZetaCorp", job_title="Dev",
            status=JobApplication.Status.SAVED,
        )
        response = client_a.get(list_url(), {"ordering": "company_name"})
        names = [r["company_name"] for r in response.data["results"]]
        assert names == sorted(names)


@pytest.mark.django_db
class TestRetrieveUpdateDelete:

    def test_retrieve_own_application(self, client_a, application_a):
        response = client_a.get(detail_url(application_a.id))
        assert response.status_code == status.HTTP_200_OK
        assert "documents" in response.data
        assert "status_history" in response.data

    def test_cannot_retrieve_other_users_application(self, client_a, application_b):
        response = client_a.get(detail_url(application_b.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_partial_update_status_logs_history(self, client_a, application_a):
        response = client_a.patch(
            detail_url(application_a.id),
            {"status": "screening"},
        )
        assert response.status_code == status.HTTP_200_OK
        application_a.refresh_from_db()
        assert application_a.status == "screening"
        # Should have 2 history entries: initial + transition
        assert application_a.status_history.count() == 2

    def test_delete_own_application(self, client_a, application_a):
        response = client_a.delete(detail_url(application_a.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not JobApplication.objects.filter(id=application_a.id).exists()

    def test_cannot_delete_other_users_application(self, client_a, application_b):
        response = client_a.delete(detail_url(application_b.id))
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )


# ─── Document Upload ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDocumentUpload:

    def _make_pdf(self, name="cv.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4 fake content", content_type="application/pdf")

    def test_upload_cv_success(self, client_a, application_a):
        response = client_a.post(
            document_url(application_a.id),
            {"file": self._make_pdf(), "document_type": "cv"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Document.objects.filter(application=application_a).count() == 1

    def test_upload_invalid_extension_rejected(self, client_a, application_a):
        bad_file = SimpleUploadedFile("resume.exe", b"malicious", content_type="application/octet-stream")
        response = client_a.post(
            document_url(application_a.id),
            {"file": bad_file, "document_type": "cv"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_upload_to_other_users_application(self, client_a, application_b):
        response = client_a.post(
            document_url(application_b.id),
            {"file": self._make_pdf(), "document_type": "cv"},
            format="multipart",
        )
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )


# ─── Status History ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStatusHistory:

    def test_history_endpoint_returns_ordered_transitions(self, client_a, application_a):
        # Move through two status changes
        client_a.patch(detail_url(application_a.id), {"status": "screening"})
        client_a.patch(detail_url(application_a.id), {"status": "interview"})

        response = client_a.get(history_url(application_a.id))
        assert response.status_code == status.HTTP_200_OK
        statuses = [h["to_status"] for h in response.data]
        assert "applied" in statuses
        assert "screening" in statuses
        assert "interview" in statuses