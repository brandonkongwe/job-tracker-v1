"""
Celery application configuration.

Usage:
    Start worker:  celery -A jobtracker worker -l info
    Start beat:    celery -A jobtracker beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
"""

import os

from celery import Celery

# Use dev settings by default; override via environment in production.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobtracker.settings.dev")

app = Celery("jobtracker")

# Read config from Django settings, namespaced under CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Utility task for confirming Celery is running correctly."""
    print(f"Request: {self.request!r}")