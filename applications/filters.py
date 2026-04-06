"""
FilterSet for JobApplication.

Supports filtering by:
- status (exact, multiple via ?status=applied&status=interview)
- work_mode
- source
- salary range (min/max bounds)
- applied_date range
- created_at range
- is_active (derived — filters out terminal statuses)
"""

import django_filters
from django.db.models import Q

from .models import JobApplication


class JobApplicationFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=JobApplication.Status.choices,
        help_text="Filter by one or more statuses. Repeat parameter for multiple: ?status=applied&status=interview",
    )

    work_mode = django_filters.MultipleChoiceFilter(
        choices=JobApplication.WorkMode.choices,
    )

    source = django_filters.MultipleChoiceFilter(
        choices=JobApplication.Source.choices,
    )

    salary_min_gte = django_filters.NumberFilter(
        field_name="salary_min",
        lookup_expr="gte",
        label="Salary min at least",
    )
    salary_max_lte = django_filters.NumberFilter(
        field_name="salary_max",
        lookup_expr="lte",
        label="Salary max at most",
    )

    applied_after  = django_filters.DateFilter(field_name="applied_date", lookup_expr="gte")
    applied_before = django_filters.DateFilter(field_name="applied_date", lookup_expr="lte")

    created_after  = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    is_active = django_filters.BooleanFilter(
        method="filter_is_active",
        label="Active applications only (excludes accepted, rejected, withdrawn)",
    )

    def filter_is_active(self, queryset, name, value):
        terminal = [
            JobApplication.Status.ACCEPTED,
            JobApplication.Status.REJECTED,
            JobApplication.Status.WITHDRAWN,
        ]
        if value:
            return queryset.exclude(status__in=terminal)
        return queryset.filter(status__in=terminal)

    class Meta:
        model  = JobApplication
        fields = [
            "status",
            "work_mode",
            "source",
            "salary_min_gte",
            "salary_max_lte",
            "applied_after",
            "applied_before",
            "created_after",
            "created_before",
            "is_active",
        ]