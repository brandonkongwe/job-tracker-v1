"""
AppConfig for reminders.

The post_migrate signal registers the dispatch_due_reminders
periodic task in django_celery_beat's database scheduler so it
runs every minute automatically — no manual configuration needed.
"""

from django.apps import AppConfig


class RemindersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reminders"
    verbose_name = "Reminders"

    def ready(self):
        """Wire up the Celery Beat periodic task after migrations."""
        try:
            from django.db import connection
            # Only register if celery_beat tables exist (i.e. after first migrate)
            tables = connection.introspection.table_names()
            if "django_celery_beat_periodictask" not in tables:
                return
            self._register_beat_schedule()
        except Exception:
            pass  # Suppress errors during initial setup / test runs

    @staticmethod
    def _register_beat_schedule():
        from django_celery_beat.models import IntervalSchedule, PeriodicTask

        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        PeriodicTask.objects.update_or_create(
            name="Dispatch due reminders every minute",
            defaults={
                "task": "reminders.dispatch_due_reminders",
                "interval": schedule,
                "enabled": True,
            },
        )