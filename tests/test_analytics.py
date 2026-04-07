"""
Tests for the analytics app.

Covers every endpoint and utility function:
- dashboard summary
- status breakdown (all statuses present, correct counts)
- weekly/monthly volume (zero-fill, correct bucketing)
- source breakdown (sorted, excludes zeros)
- conversion funnel (uses StatusHistory, not just current status)
- stage duration (avg days, sample size)
- response rate (correct percentages)
- top companies (sorted by count)
- heatmap (365 days, zero fill)
- admin scoping (user_id filter)
- ownership isolation
"""

import pytest
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from applications.models import JobApplication, StatusHistory
from analytics.utils import (
    get_activity_heatmap,
    get_avg_days_between_stages,
    get_conversion_funnel,
    get_dashboard_summary,
    get_monthly_volume,
    get_response_rate,
    get_source_breakdown,
    get_status_breakdown,
    get_top_companies,
    get_weekly_volume,
)

User = get_user_model()


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="analyst@example.com", password="Pass123!",
        first_name="Ana", last_name="Lyst",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com", password="Pass123!",
        first_name="Admin", last_name="User",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other@example.com", password="Pass123!",
        first_name="Other", last_name="User",
    )


def auth_client_for(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
    return client


@pytest.fixture
def client(user):
    return auth_client_for(user)


@pytest.fixture
def admin_client(admin_user):
    return auth_client_for(admin_user)


def make_app(user, status_val, source=JobApplication.Source.LINKEDIN,
             company="TestCo", days_ago=1, applied=True):
    """Helper to create a JobApplication quickly."""
    return JobApplication.objects.create(
        user=user,
        company_name=company,
        job_title="Engineer",
        status=status_val,
        source=source,
        applied_date=date.today() - timedelta(days=days_ago) if applied else None,
        created_at=timezone.now() - timedelta(days=days_ago),
    )


@pytest.fixture
def populated_qs(db, user):
    """
    Creates a varied set of applications for the user:
    3 applied, 2 screening, 1 interview, 1 offer, 2 rejected
    Sources: 4 LinkedIn, 3 Indeed, 2 Company, 1 Referral
    """
    apps = []
    for i in range(3):
        apps.append(make_app(user, JobApplication.Status.APPLIED,
                             source=JobApplication.Source.LINKEDIN,
                             company="AlphaCorp", days_ago=10 + i))
    for i in range(2):
        apps.append(make_app(user, JobApplication.Status.SCREENING,
                             source=JobApplication.Source.INDEED,
                             company="BetaInc", days_ago=8 + i))
    apps.append(make_app(user, JobApplication.Status.INTERVIEW,
                         source=JobApplication.Source.INDEED,
                         company="GammaTech", days_ago=5))
    apps.append(make_app(user, JobApplication.Status.OFFER,
                         source=JobApplication.Source.COMPANY,
                         company="DeltaLtd", days_ago=3))
    for i in range(2):
        apps.append(make_app(user, JobApplication.Status.REJECTED,
                             source=JobApplication.Source.LINKEDIN,
                             company="EpsilonCo", days_ago=2 + i))

    # Write StatusHistory for funnel/duration tests
    for app in apps:
        StatusHistory.objects.create(
            application=app,
            from_status="",
            to_status=app.status,
            changed_at=timezone.now() - timedelta(days=7),
        )

    return JobApplication.objects.filter(user=user)


# ─── Utility Function Tests ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStatusBreakdown:

    def test_all_statuses_present(self, populated_qs):
        result = get_status_breakdown(populated_qs)
        statuses = [r["status"] for r in result]
        for choice_val, _ in JobApplication.Status.choices:
            assert choice_val in statuses

    def test_counts_are_correct(self, populated_qs):
        result = {r["status"]: r["count"] for r in get_status_breakdown(populated_qs)}
        assert result["applied"]   == 3
        assert result["screening"] == 2
        assert result["interview"] == 1
        assert result["offer"]     == 1
        assert result["rejected"]  == 2
        assert result["saved"]     == 0

    def test_empty_qs_returns_zeros(self, db, user):
        qs = JobApplication.objects.filter(user=user)
        result = get_status_breakdown(qs)
        assert all(r["count"] == 0 for r in result)


@pytest.mark.django_db
class TestWeeklyVolume:

    def test_returns_correct_number_of_weeks(self, populated_qs):
        result = get_weekly_volume(populated_qs, weeks=12)
        assert len(result) == 12

    def test_weeks_are_iso_formatted(self, populated_qs):
        result = get_weekly_volume(populated_qs, weeks=4)
        for item in result:
            assert "-W" in item["week"]

    def test_zero_fill_for_empty_weeks(self, db, user):
        qs = JobApplication.objects.filter(user=user)
        result = get_weekly_volume(qs, weeks=4)
        assert all(r["count"] == 0 for r in result)


@pytest.mark.django_db
class TestMonthlyVolume:

    def test_returns_correct_number_of_months(self, populated_qs):
        result = get_monthly_volume(populated_qs, months=12)
        assert len(result) == 12

    def test_labels_are_human_readable(self, populated_qs):
        result = get_monthly_volume(populated_qs, months=3)
        for item in result:
            assert len(item["label"]) > 4  # e.g. "Jun 2024"


@pytest.mark.django_db
class TestSourceBreakdown:

    def test_excludes_zero_count_sources(self, populated_qs):
        result = get_source_breakdown(populated_qs)
        assert all(r["count"] > 0 for r in result)

    def test_sorted_descending(self, populated_qs):
        result = get_source_breakdown(populated_qs)
        counts = [r["count"] for r in result]
        assert counts == sorted(counts, reverse=True)

    def test_linkedin_is_top_source(self, populated_qs):
        result = get_source_breakdown(populated_qs)
        assert result[0]["source"] == "linkedin"


@pytest.mark.django_db
class TestConversionFunnel:

    def test_funnel_uses_history_not_only_current_status(self, db, user):
        """An app currently 'rejected' that passed through 'interview'
        should still count in the interview stage of the funnel."""
        app = make_app(user, JobApplication.Status.REJECTED, days_ago=5)
        StatusHistory.objects.create(
            application=app, from_status="", to_status="applied",
            changed_at=timezone.now() - timedelta(days=5),
        )
        StatusHistory.objects.create(
            application=app, from_status="applied", to_status="interview",
            changed_at=timezone.now() - timedelta(days=3),
        )
        StatusHistory.objects.create(
            application=app, from_status="interview", to_status="rejected",
            changed_at=timezone.now() - timedelta(days=1),
        )
        qs = JobApplication.objects.filter(user=user)
        result = {r["stage"]: r["count"] for r in get_conversion_funnel(qs)}
        assert result["interview"] == 1
        assert result["applied"] == 1

    def test_rates_are_percentages(self, populated_qs):
        result = get_conversion_funnel(populated_qs)
        for item in result:
            assert 0.0 <= item["rate"] <= 100.0

    def test_empty_qs_returns_zero_rates(self, db, user):
        qs = JobApplication.objects.filter(user=user)
        result = get_conversion_funnel(qs)
        assert all(r["count"] == 0 for r in result)


@pytest.mark.django_db
class TestStageDuration:

    def test_returns_transitions_with_avg_days(self, db, user):
        app = make_app(user, JobApplication.Status.INTERVIEW, days_ago=10)
        t0 = timezone.now() - timedelta(days=10)
        StatusHistory.objects.create(application=app, from_status="", to_status="applied", changed_at=t0)
        StatusHistory.objects.create(application=app, from_status="applied", to_status="screening",
                                     changed_at=t0 + timedelta(days=3))
        StatusHistory.objects.create(application=app, from_status="screening", to_status="interview",
                                     changed_at=t0 + timedelta(days=7))

        qs = JobApplication.objects.filter(user=user)
        result = get_avg_days_between_stages(qs)
        labels = [r["label"] for r in result]
        assert "Applied → Screening" in labels
        assert "Screening → Interview" in labels

        by_label = {r["label"]: r for r in result}
        assert by_label["Applied → Screening"]["avg_days"] == pytest.approx(3.0, abs=0.1)
        assert by_label["Screening → Interview"]["avg_days"] == pytest.approx(4.0, abs=0.1)

    def test_empty_qs_returns_empty_list(self, db, user):
        qs = JobApplication.objects.filter(user=user)
        assert get_avg_days_between_stages(qs) == []


@pytest.mark.django_db
class TestResponseRate:

    def test_response_rate_calculation(self, populated_qs):
        result = get_response_rate(populated_qs)
        assert result["total"] == 9
        # screening(2) + interview(1) + offer(1) + rejected(2) = 6 responded
        assert result["responded"] == 6
        assert result["response_rate"] == pytest.approx(66.7, abs=0.2)

    def test_zero_total_returns_zero_rates(self, db, user):
        qs = JobApplication.objects.filter(user=user)
        result = get_response_rate(qs)
        assert result["response_rate"] == 0.0
        assert result["interview_rate"] == 0.0
        assert result["offer_rate"] == 0.0


@pytest.mark.django_db
class TestTopCompanies:

    def test_sorted_by_count_descending(self, populated_qs):
        result = get_top_companies(populated_qs)
        counts = [r["count"] for r in result]
        assert counts == sorted(counts, reverse=True)

    def test_limit_respected(self, populated_qs):
        result = get_top_companies(populated_qs, limit=2)
        assert len(result) <= 2

    def test_alpha_corp_appears(self, populated_qs):
        result = get_top_companies(populated_qs)
        names = [r["company_name"] for r in result]
        assert "AlphaCorp" in names


@pytest.mark.django_db
class TestActivityHeatmap:

    def test_returns_365_days(self, populated_qs):
        result = get_activity_heatmap(populated_qs, days=365)
        assert len(result) == 366  # 365 + today

    def test_dates_are_sequential(self, populated_qs):
        result = get_activity_heatmap(populated_qs, days=7)
        dates = [item["date"] for item in result]
        assert dates == sorted(dates)

    def test_zero_fill_present(self, populated_qs):
        result = get_activity_heatmap(populated_qs, days=365)
        assert any(item["count"] == 0 for item in result)


@pytest.mark.django_db
class TestDashboardSummary:

    def test_all_keys_present(self, populated_qs):
        result = get_dashboard_summary(populated_qs)
        expected_keys = {
            "total_applications", "active_applications", "status_breakdown",
            "response_rate", "weekly_volume", "source_breakdown",
            "conversion_funnel", "top_companies",
        }
        assert expected_keys.issubset(result.keys())

    def test_total_count_correct(self, populated_qs):
        result = get_dashboard_summary(populated_qs)
        assert result["total_applications"] == 9

    def test_active_excludes_terminal(self, populated_qs):
        result = get_dashboard_summary(populated_qs)
        # terminal: 2 rejected — rest are active
        assert result["active_applications"] == 7


# ─── API Endpoint Tests ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnalyticsEndpoints:

    def test_dashboard_endpoint(self, client, populated_qs):
        url = reverse("api_v1:analytics:dashboard")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "total_applications" in response.data
        assert "status_breakdown" in response.data

    def test_status_endpoint(self, client, populated_qs):
        url = reverse("api_v1:analytics:status_breakdown")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_weekly_volume_endpoint(self, client, populated_qs):
        url = reverse("api_v1:analytics:weekly_volume")
        response = client.get(url, {"weeks": "8"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 8

    def test_monthly_volume_endpoint(self, client, populated_qs):
        url = reverse("api_v1:analytics:monthly_volume")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_funnel_endpoint(self, client, populated_qs):
        url = reverse("api_v1:analytics:conversion_funnel")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_heatmap_endpoint(self, client, populated_qs):
        url = reverse("api_v1:analytics:heatmap")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 300  # ~365 days

    def test_analytics_require_auth(self):
        anon = APIClient()
        url = reverse("api_v1:analytics:dashboard")
        response = anon.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_only_sees_own_data(self, client, user, other_user, db):
        make_app(other_user, JobApplication.Status.APPLIED, company="OtherCo")
        make_app(user, JobApplication.Status.APPLIED, company="MyCo")
        url = reverse("api_v1:analytics:status_breakdown")
        response = client.get(url)
        # total should be 1, not 2
        result = {r["status"]: r["count"] for r in response.data}
        assert result["applied"] == 1

    def test_admin_can_scope_to_user(self, admin_client, user, db):
        make_app(user, JobApplication.Status.APPLIED, company="UserCo")
        url = reverse("api_v1:analytics:dashboard")
        response = admin_client.get(url, {"user_id": str(user.id)})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_applications"] == 1