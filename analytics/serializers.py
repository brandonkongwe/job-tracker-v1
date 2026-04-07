"""
Serializers for the analytics app.

These are all read-only, manually constructed response shapes
(not ModelSerializers) — analytics endpoints return aggregated
data, not model instances.

Using explicit Serializer classes rather than returning raw dicts:
- gives us OpenAPI schema generation via drf-spectacular
- enforces output types
- makes the API contract explicit
"""

from rest_framework import serializers


class StatusBreakdownItemSerializer(serializers.Serializer):
    status = serializers.CharField()
    label  = serializers.CharField()
    count  = serializers.IntegerField()


class WeeklyVolumeItemSerializer(serializers.Serializer):
    week  = serializers.CharField(help_text="ISO week label, e.g. '2024-W22'")
    count = serializers.IntegerField()


class MonthlyVolumeItemSerializer(serializers.Serializer):
    month = serializers.CharField(help_text="Month key, e.g. '2024-06'")
    label = serializers.CharField(help_text="Human-readable label, e.g. 'Jun 2024'")
    count = serializers.IntegerField()



class SourceBreakdownItemSerializer(serializers.Serializer):
    source = serializers.CharField()
    label  = serializers.CharField()
    count  = serializers.IntegerField()



class ConversionFunnelItemSerializer(serializers.Serializer):
    stage = serializers.CharField()
    label = serializers.CharField()
    count = serializers.IntegerField()
    rate  = serializers.FloatField(help_text="% of total applications that reached this stage")



class StageDurationItemSerializer(serializers.Serializer):
    from_stage   = serializers.CharField()
    to_stage     = serializers.CharField()
    label        = serializers.CharField(help_text="e.g. 'Applied → Screening'")
    avg_days     = serializers.FloatField()
    sample_size  = serializers.IntegerField(help_text="Number of transitions this average is based on")



class ResponseRateSerializer(serializers.Serializer):
    total           = serializers.IntegerField()
    responded       = serializers.IntegerField()
    response_rate   = serializers.FloatField(help_text="% of applications that moved past 'applied'")
    interview_rate  = serializers.FloatField(help_text="% of applications that reached interview")
    offer_rate      = serializers.FloatField(help_text="% of applications that received an offer")



class TopCompanySerializer(serializers.Serializer):
    company_name = serializers.CharField()
    count        = serializers.IntegerField()


class HeatmapDaySerializer(serializers.Serializer):
    date  = serializers.DateField()
    count = serializers.IntegerField()


class DashboardSummarySerializer(serializers.Serializer):
    total_applications  = serializers.IntegerField()
    active_applications = serializers.IntegerField()
    status_breakdown    = StatusBreakdownItemSerializer(many=True)
    response_rate       = ResponseRateSerializer()
    weekly_volume       = WeeklyVolumeItemSerializer(many=True)
    source_breakdown    = SourceBreakdownItemSerializer(many=True)
    conversion_funnel   = ConversionFunnelItemSerializer(many=True)
    top_companies       = TopCompanySerializer(many=True)