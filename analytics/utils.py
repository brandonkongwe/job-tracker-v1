"""
Analytics utility functions.

Functions
---------
get_status_breakdown       — count of applications per status
get_weekly_volume          — applications created per week (last N weeks)
get_monthly_volume         — applications created per month (last N months)
get_source_breakdown       — count of applications per discovery source
get_conversion_funnel      — % of applications that reached each pipeline stage
get_avg_days_between_stages — average days from one status to the next
get_response_rate          — % of applications that got any response (screening+)
get_top_companies          — most applied-to companies
get_activity_heatmap       — daily application count over the last 12 months
get_dashboard_summary      — single call aggregating the most-used stats
"""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Avg, Count, F, FloatField, Q
from django.db.models.functions import ExtractWeekDay, TruncMonth, TruncWeek
from django.utils import timezone

from applications.models import JobApplication, StatusHistory


# Helpers

def _weeks_ago(n: int):
    return timezone.now() - timedelta(weeks=n)


def _months_ago(n: int):
    # Approximate: 30 days per month
    return timezone.now() - timedelta(days=30 * n)


PIPELINE_ORDER = [
    JobApplication.Status.SAVED,
    JobApplication.Status.APPLIED,
    JobApplication.Status.SCREENING,
    JobApplication.Status.INTERVIEW,
    JobApplication.Status.OFFER,
    JobApplication.Status.ACCEPTED,
]

TERMINAL_STATUSES = [
    JobApplication.Status.REJECTED,
    JobApplication.Status.WITHDRAWN,
]


def get_status_breakdown(qs) -> list[dict]:
    """
    Count of applications per status, ordered by pipeline stage.
    Returns all statuses with their display label and count (0 if none).

    Example output:
        [{"status": "saved", "label": "Saved", "count": 3}, ...]
    """
    counts = dict(
        qs.values("status")
          .annotate(count=Count("id"))
          .values_list("status", "count")
    )

    # Build result in pipeline order, then append terminal statuses
    result = []
    for choice_value, choice_label in JobApplication.Status.choices:
        result.append({
            "status": choice_value,
            "label":  choice_label,
            "count":  counts.get(choice_value, 0),
        })
    return result


def get_weekly_volume(qs, weeks: int = 12) -> list[dict]:
    """
    Number of applications created per ISO week over the last `weeks` weeks.
    Weeks with zero applications are filled in so the chart has no gaps.

    Example output:
        [{"week": "2024-W22", "count": 4}, ...]
    """
    cutoff = _weeks_ago(weeks)
    raw = (
        qs.filter(created_at__gte=cutoff)
          .annotate(week=TruncWeek("created_at"))
          .values("week")
          .annotate(count=Count("id"))
          .order_by("week")
    )
    raw_map = {r["week"].date(): r["count"] for r in raw}

    result = []
    now = timezone.now().date()
    # Walk back `weeks` weeks from today
    for i in range(weeks - 1, -1, -1):
        day = now - timedelta(weeks=i)
        # Normalise to Monday of that week
        monday = day - timedelta(days=day.weekday())
        iso_label = f"{monday.isocalendar()[0]}-W{monday.isocalendar()[1]:02d}"
        result.append({"week": iso_label, "count": raw_map.get(monday, 0)})

    return result


def get_monthly_volume(qs, months: int = 12) -> list[dict]:
    """
    Number of applications created per calendar month over the last `months` months.

    Example output:
        [{"month": "2024-06", "label": "Jun 2024", "count": 7}, ...]
    """
    cutoff = _months_ago(months)
    raw = (
        qs.filter(created_at__gte=cutoff)
          .annotate(month=TruncMonth("created_at"))
          .values("month")
          .annotate(count=Count("id"))
          .order_by("month")
    )
    raw_map = {r["month"].date().strftime("%Y-%m"): r["count"] for r in raw}

    result = []
    now = timezone.now().date().replace(day=1)
    for i in range(months - 1, -1, -1):
        # Step back month by month
        month_date = (now - timedelta(days=30 * i)).replace(day=1)
        key   = month_date.strftime("%Y-%m")
        label = month_date.strftime("%b %Y")
        result.append({"month": key, "label": label, "count": raw_map.get(key, 0)})

    return result


def get_source_breakdown(qs) -> list[dict]:
    """
    Count of applications grouped by discovery source.

    Example output:
        [{"source": "linkedin", "label": "LinkedIn", "count": 12}, ...]
    """
    counts = dict(
        qs.values("source")
          .annotate(count=Count("id"))
          .values_list("source", "count")
    )
    result = []
    for value, label in JobApplication.Source.choices:
        count = counts.get(value, 0)
        if count > 0:
            result.append({"source": value, "label": label, "count": count})
    return sorted(result, key=lambda x: x["count"], reverse=True)


def get_conversion_funnel(qs) -> list[dict]:
    """
    For each pipeline stage, compute:
    - count of applications that REACHED that stage (i.e. status >= stage)
    - conversion rate relative to the total number of applications

    Only counts stages an application has EVER been in (via StatusHistory),
    not just its current status — so a rejected application that reached
    interview still counts toward the interview stage.

    Example output:
        [{"stage": "applied", "label": "Applied", "count": 45, "rate": 90.0}, ...]
    """
    total = qs.count()
    if total == 0:
        return [
            {"stage": s, "label": l, "count": 0, "rate": 0.0}
            for s, l in JobApplication.Status.choices
            if s in [v for v, _ in [(s, l) for s, l in JobApplication.Status.choices
                                    if s in [p for p in PIPELINE_ORDER]]]
        ]

    app_ids = qs.values_list("id", flat=True)

    # Get the set of statuses each application ever reached
    ever_reached = (
        StatusHistory.objects
        .filter(application_id__in=app_ids)
        .values("application_id", "to_status")
        .distinct()
    )

    # Also include current status (in case history wasn't written for oldest apps)
    current_statuses = qs.values("id", "status")

    reached_per_stage: dict[str, set] = defaultdict(set)
    for entry in ever_reached:
        reached_per_stage[entry["to_status"]].add(entry["application_id"])
    for entry in current_statuses:
        reached_per_stage[entry["status"]].add(entry["id"])

    result = []
    for stage in PIPELINE_ORDER:
        label = JobApplication.Status(stage).label
        count = len(reached_per_stage.get(stage, set()))
        result.append({
            "stage": stage,
            "label": label,
            "count": count,
            "rate":  round((count / total) * 100, 1) if total else 0.0,
        })
    return result


def get_avg_days_between_stages(qs) -> list[dict]:
    """
    Average number of days between consecutive status transitions,
    computed from StatusHistory entries.

    Example output:
        [
          {"from_stage": "applied", "to_stage": "screening",
           "label": "Applied → Screening", "avg_days": 4.2, "sample_size": 18},
          ...
        ]
    """
    app_ids = list(qs.values_list("id", flat=True))
    if not app_ids:
        return []

    # Pull all history entries ordered by application + time
    history = (
        StatusHistory.objects
        .filter(application_id__in=app_ids)
        .order_by("application_id", "changed_at")
        .values("application_id", "from_status", "to_status", "changed_at")
    )

    # Build per-application timeline: {app_id: [(status, timestamp), ...]}
    timelines: dict = defaultdict(list)
    for entry in history:
        timelines[entry["application_id"]].append(
            (entry["to_status"], entry["changed_at"])
        )

    # Accumulate days between each transition pair
    transition_days: dict[tuple, list[float]] = defaultdict(list)
    for app_id, events in timelines.items():
        for i in range(1, len(events)):
            prev_status, prev_time = events[i - 1]
            curr_status, curr_time = events[i]
            delta_days = (curr_time - prev_time).total_seconds() / 86400
            if delta_days >= 0:
                transition_days[(prev_status, curr_status)].append(delta_days)

    if not transition_days:
        return []

    result = []
    for (from_s, to_s), days_list in sorted(transition_days.items()):
        avg = round(sum(days_list) / len(days_list), 1)
        try:
            from_label = JobApplication.Status(from_s).label
            to_label   = JobApplication.Status(to_s).label
        except ValueError:
            continue
        result.append({
            "from_stage":  from_s,
            "to_stage":    to_s,
            "label":       f"{from_label} → {to_label}",
            "avg_days":    avg,
            "sample_size": len(days_list),
        })
    return result


def get_response_rate(qs) -> dict:
    """
    Percentage of applications that received any response
    (i.e. moved beyond 'applied' — screening or further).

    Example output:
        {"total": 50, "responded": 22, "response_rate": 44.0,
         "interview_rate": 20.0, "offer_rate": 8.0}
    """
    total = qs.count()
    if total == 0:
        return {
            "total": 0, "responded": 0,
            "response_rate": 0.0, "interview_rate": 0.0, "offer_rate": 0.0,
        }

    responded = qs.exclude(
        status__in=[JobApplication.Status.SAVED, JobApplication.Status.APPLIED]
    ).count()

    interviewed = qs.filter(
        status__in=[
            JobApplication.Status.INTERVIEW,
            JobApplication.Status.OFFER,
            JobApplication.Status.ACCEPTED,
        ]
    ).count()

    offered = qs.filter(
        status__in=[JobApplication.Status.OFFER, JobApplication.Status.ACCEPTED]
    ).count()

    return {
        "total":           total,
        "responded":       responded,
        "response_rate":   round((responded   / total) * 100, 1),
        "interview_rate":  round((interviewed / total) * 100, 1),
        "offer_rate":      round((offered     / total) * 100, 1),
    }


def get_top_companies(qs, limit: int = 10) -> list[dict]:
    """
    Most applied-to companies, sorted by application count descending.

    Example output:
        [{"company_name": "Google", "count": 3}, ...]
    """
    return list(
        qs.values("company_name")
          .annotate(count=Count("id"))
          .order_by("-count")
          .values("company_name", "count")
        [:limit]
    )


def get_activity_heatmap(qs, days: int = 365) -> list[dict]:
    """
    Daily application count for the last `days` days.
    Returns a list of {date, count} dicts suitable for a GitHub-style heatmap.
    Days with zero activity are included.

    Example output:
        [{"date": "2024-01-01", "count": 0}, {"date": "2024-01-02", "count": 2}, ...]
    """
    cutoff = timezone.now().date() - timedelta(days=days)
    raw = (
        qs.filter(created_at__date__gte=cutoff)
          .values(date=F("created_at__date"))
          .annotate(count=Count("id"))
          .order_by("date")
    )
    raw_map = {r["date"]: r["count"] for r in raw}

    today  = timezone.now().date()
    result = []
    for i in range(days, -1, -1):
        day = today - timedelta(days=i)
        result.append({"date": day.isoformat(), "count": raw_map.get(day, 0)})
    return result


def get_dashboard_summary(qs) -> dict:
    """
    Single aggregated call for the main dashboard.
    Combines the most important metrics to minimise round-trips.

    Returns a dict with:
        total_applications, active_applications, status_breakdown,
        response_rate, weekly_volume (last 12 weeks), source_breakdown,
        conversion_funnel, top_companies
    """
    total  = qs.count()
    active = qs.exclude(
        status__in=[
            JobApplication.Status.ACCEPTED,
            JobApplication.Status.REJECTED,
            JobApplication.Status.WITHDRAWN,
        ]
    ).count()

    return {
        "total_applications":  total,
        "active_applications": active,
        "status_breakdown":    get_status_breakdown(qs),
        "response_rate":       get_response_rate(qs),
        "weekly_volume":       get_weekly_volume(qs, weeks=12),
        "source_breakdown":    get_source_breakdown(qs),
        "conversion_funnel":   get_conversion_funnel(qs),
        "top_companies":       get_top_companies(qs, limit=5),
    }