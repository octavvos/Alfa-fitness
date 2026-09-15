import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("fitness")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "expire-memberships-daily": {
        "task": "api.tasks.expire_memberships",
        "schedule": crontab(hour=0, minute=5),
    },
    "unfreeze-memberships-daily": {
        "task": "api.tasks.unfreeze_memberships",
        "schedule": crontab(hour=0, minute=10),
    },
    "send-expiry-reminders": {
        "task": "api.tasks.send_expiry_reminders",
        "schedule": crontab(hour=10, minute=0),
    },
}
