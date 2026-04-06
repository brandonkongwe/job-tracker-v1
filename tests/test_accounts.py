"""
Tests for the accounts app.

Covers: registration, login, token refresh, logout,
        profile retrieval/update, password change, admin user listing.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def job_seeker(db):
    return User.objects.create_user(
        email="seeker@example.com",
        password="SecurePass123!",
        first_name="Jane",
        last_name="Seeker",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com",
        password="AdminPass123!",
        first_name="Admin",
        last_name="User",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def auth_client(api_client, job_seeker):
    """APIClient pre-authenticated as a job seeker."""
    refresh = RefreshToken.for_user(job_seeker)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client, job_seeker, str(refresh)


@pytest.fixture
def admin_client(api_client, admin_user):
    """APIClient pre-authenticated as an admin."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client, admin_user


# ─── Registration ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistration:
    url = reverse("api_v1:accounts:register")

    def test_register_success(self, api_client):
        payload = {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass99!",
            "password_confirm": "StrongPass99!",
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert User.objects.filter(email="new@example.com").exists()

    def test_register_email_normalised_to_lowercase(self, api_client):
        payload = {
            "email": "UPPER@EXAMPLE.COM",
            "first_name": "Up",
            "last_name": "Per",
            "password": "StrongPass99!",
            "password_confirm": "StrongPass99!",
        }
        api_client.post(self.url, payload)
        assert User.objects.filter(email="upper@example.com").exists()

    def test_register_duplicate_email(self, api_client, job_seeker):
        payload = {
            "email": job_seeker.email,
            "first_name": "Dup",
            "last_name": "User",
            "password": "StrongPass99!",
            "password_confirm": "StrongPass99!",
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client):
        payload = {
            "email": "mismatch@example.com",
            "first_name": "A",
            "last_name": "B",
            "password": "StrongPass99!",
            "password_confirm": "WrongPass99!",
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    def test_register_weak_password_rejected(self, api_client):
        payload = {
            "email": "weak@example.com",
            "first_name": "Weak",
            "last_name": "Pass",
            "password": "123",
            "password_confirm": "123",
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─── Login ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogin:
    url = reverse("api_v1:accounts:login")

    def test_login_success_returns_tokens_and_user(self, api_client, job_seeker):
        response = api_client.post(self.url, {"email": job_seeker.email, "password": "SecurePass123!"})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == job_seeker.email

    def test_login_wrong_password(self, api_client, job_seeker):
        response = api_client.post(self.url, {"email": job_seeker.email, "password": "WrongPass!"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_unknown_email(self, api_client):
        response = api_client.post(self.url, {"email": "nobody@example.com", "password": "Pass123!"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Logout ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogout:
    url = reverse("api_v1:accounts:logout")

    def test_logout_blacklists_refresh_token(self, auth_client):
        client, user, refresh_token = auth_client
        response = client.post(self.url, {"refresh": refresh_token})
        assert response.status_code == status.HTTP_205_RESET_CONTENT

    def test_logout_invalid_token(self, auth_client):
        client, _, _ = auth_client
        response = client.post(self.url, {"refresh": "not-a-real-token"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_requires_auth(self, api_client):
        response = api_client.post(self.url, {"refresh": "any"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Profile ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProfile:
    url = reverse("api_v1:accounts:me")

    def test_get_own_profile(self, auth_client):
        client, user, _ = auth_client
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert "application_count" in response.data

    def test_update_profile_patch(self, auth_client):
        client, user, _ = auth_client
        response = client.patch(self.url, {"bio": "Looking for data engineering roles."})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.bio == "Looking for data engineering roles."

    def test_cannot_change_email_via_profile(self, auth_client):
        client, user, _ = auth_client
        response = client.patch(self.url, {"email": "hacked@example.com"})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.email == "seeker@example.com"  # unchanged

    def test_profile_requires_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Password Change ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPasswordChange:
    url = reverse("api_v1:accounts:password_change")

    def test_change_password_success(self, auth_client):
        client, user, _ = auth_client
        payload = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!",
            "new_password_confirm": "NewSecurePass456!",
        }
        response = client.post(self.url, payload)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewSecurePass456!")

    def test_wrong_current_password_rejected(self, auth_client):
        client, _, _ = auth_client
        payload = {
            "current_password": "WrongPassword!",
            "new_password": "NewPass456!",
            "new_password_confirm": "NewPass456!",
        }
        response = client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─── Admin User Listing ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserListing:
    url = reverse("api_v1:accounts:user_list")

    def test_admin_can_list_users(self, admin_client):
        client, _ = admin_client
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data  # paginated

    def test_job_seeker_cannot_list_users(self, auth_client):
        client, _, _ = auth_client
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_list_users(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED