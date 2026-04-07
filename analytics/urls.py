"""URL patterns for the analytics app."""

from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("dashboard/",      views.DashboardView.as_view(),       name="dashboard"),
    path("status/",         views.StatusBreakdownView.as_view(),  name="status_breakdown"),
    path("volume/weekly/",  views.WeeklyVolumeView.as_view(),     name="weekly_volume"),
    path("volume/monthly/", views.MonthlyVolumeView.as_view(),    name="monthly_volume"),
    path("sources/",        views.SourceBreakdownView.as_view(),  name="source_breakdown"),
    path("funnel/",         views.ConversionFunnelView.as_view(), name="conversion_funnel"),
    path("stage-duration/", views.StageDurationView.as_view(),    name="stage_duration"),
    path("response-rate/",  views.ResponseRateView.as_view(),     name="response_rate"),
    path("top-companies/",  views.TopCompaniesView.as_view(),     name="top_companies"),
    path("heatmap/",        views.ActivityHeatmapView.as_view(),  name="heatmap"),
]