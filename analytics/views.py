"""
Views for the analytics app.

All endpoints are GET-only, read-only, and scoped to the
authenticated user's own applications (admins see all).

Endpoints (all under /api/v1/analytics/)
-----------------------------------------
GET /dashboard/         — combined summary for the main dashboard
GET /status/            — application count per status
GET /volume/weekly/     — weekly application volume (last 12 weeks)
GET /volume/monthly/    — monthly application volume (last 12 months)
GET /sources/           — breakdown by discovery source
GET /funnel/            — stage conversion funnel
GET /stage-duration/    — average days between status transitions
GET /response-rate/     — response, interview, and offer rates
GET /top-companies/     — most applied-to companies
GET /heatmap/           — daily activity for the last 365 days
"""

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import JobApplication

from . import utils
from .serializers import (
    ConversionFunnelItemSerializer,
    DashboardSummarySerializer,
    HeatmapDaySerializer,
    MonthlyVolumeItemSerializer,
    ResponseRateSerializer,
    StageDurationItemSerializer,
    SourceBreakdownItemSerializer,
    StatusBreakdownItemSerializer,
    TopCompanySerializer,
    WeeklyVolumeItemSerializer,
)


class AnalyticsBaseView(APIView):
    """
    Shared base for all analytics views.
    Provides a scoped queryset: own applications for job seekers,
    all applications for admins.
    Accepts an optional ?user_id= query param for admins to scope to one user.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        qs   = JobApplication.objects.all()

        if not user.is_admin:
            return qs.filter(user=user)

        # Admins can optionally scope to a specific user
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return qs.filter(user_id=user_id)
        return qs


@extend_schema(
    tags=["analytics"],
    summary="Main dashboard summary",
    description=(
        "Returns all key metrics in a single call. "
        "Designed for the main dashboard to avoid multiple round-trips."
    ),
    responses={200: DashboardSummarySerializer},
)
class DashboardView(AnalyticsBaseView):
    def get(self, request):
        data = utils.get_dashboard_summary(self.get_queryset())
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)


@extend_schema(
    tags=["analytics"],
    summary="Application count per status",
    description="Returns all pipeline statuses with their application count. Zero counts are included.",
    responses={200: StatusBreakdownItemSerializer(many=True)},
)
class StatusBreakdownView(AnalyticsBaseView):
    def get(self, request):
        data = utils.get_status_breakdown(self.get_queryset())
        return Response(StatusBreakdownItemSerializer(data, many=True).data)



@extend_schema(
    tags=["analytics"],
    summary="Weekly application volume",
    parameters=[
        OpenApiParameter("weeks", int, description="Number of weeks to include (default 12, max 52)"),
    ],
    responses={200: WeeklyVolumeItemSerializer(many=True)},
)
class WeeklyVolumeView(AnalyticsBaseView):
    def get(self, request):
        weeks = min(int(request.query_params.get("weeks", 12)), 52)
        data  = utils.get_weekly_volume(self.get_queryset(), weeks=weeks)
        return Response(WeeklyVolumeItemSerializer(data, many=True).data)


@extend_schema(
    tags=["analytics"],
    summary="Monthly application volume",
    parameters=[
        OpenApiParameter("months", int, description="Number of months to include (default 12, max 24)"),
    ],
    responses={200: MonthlyVolumeItemSerializer(many=True)},
)
class MonthlyVolumeView(AnalyticsBaseView):
    def get(self, request):
        months = min(int(request.query_params.get("months", 12)), 24)
        data   = utils.get_monthly_volume(self.get_queryset(), months=months)
        return Response(MonthlyVolumeItemSerializer(data, many=True).data)


@extend_schema(
    tags=["analytics"],
    summary="Applications by discovery source",
    description="Only sources with at least one application are returned, sorted by count descending.",
    responses={200: SourceBreakdownItemSerializer(many=True)},
)
class SourceBreakdownView(AnalyticsBaseView):
    def get(self, request):
        data = utils.get_source_breakdown(self.get_queryset())
        return Response(SourceBreakdownItemSerializer(data, many=True).data)


@extend_schema(
    tags=["analytics"],
    summary="Stage conversion funnel",
    description=(
        "For each pipeline stage, returns the count and percentage of applications "
        "that ever reached that stage (including those that have since moved on or been rejected)."
    ),
    responses={200: ConversionFunnelItemSerializer(many=True)},
)
class ConversionFunnelView(AnalyticsBaseView):
    def get(self, request):
        data = utils.get_conversion_funnel(self.get_queryset())
        return Response(ConversionFunnelItemSerializer(data, many=True).data)


@extend_schema(
    tags=["analytics"],
    summary="Average days between pipeline stages",
    description=(
        "Computed from StatusHistory entries. "
        "Only transitions with at least one data point are returned. "
        "sample_size tells you how many transitions the average is based on."
    ),
    responses={200: StageDurationItemSerializer(many=True)},
)
class StageDurationView(AnalyticsBaseView):
    def get(self, request):
        data = utils.get_avg_days_between_stages(self.get_queryset())
        return Response(StageDurationItemSerializer(data, many=True).data)


@extend_schema(
    tags=["analytics"],
    summary="Response, interview, and offer rates",
    description=(
        "response_rate: % of applications that moved past 'applied'. "
        "interview_rate: % that reached interview stage. "
        "offer_rate: % that received an offer."
    ),
    responses={200: ResponseRateSerializer},
)
class ResponseRateView(AnalyticsBaseView):
    def get(self, request):
        data = utils.get_response_rate(self.get_queryset())
        return Response(ResponseRateSerializer(data).data)


@extend_schema(
    tags=["analytics"],
    summary="Most applied-to companies",
    parameters=[
        OpenApiParameter("limit", int, description="Max companies to return (default 10)"),
    ],
    responses={200: TopCompanySerializer(many=True)},
)
class TopCompaniesView(AnalyticsBaseView):
    def get(self, request):
        limit = min(int(request.query_params.get("limit", 10)), 50)
        data  = utils.get_top_companies(self.get_queryset(), limit=limit)
        return Response(TopCompanySerializer(data, many=True).data)


@extend_schema(
    tags=["analytics"],
    summary="Daily application activity (heatmap data)",
    description=(
        "Returns one entry per day for the last 365 days. "
        "Days with zero activity are included so the frontend can render a full heatmap grid."
    ),
    responses={200: HeatmapDaySerializer(many=True)},
)
class ActivityHeatmapView(AnalyticsBaseView):
    def get(self, request):
        data = utils.get_activity_heatmap(self.get_queryset(), days=365)
        return Response(HeatmapDaySerializer(data, many=True).data)