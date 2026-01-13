import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('jobpulse')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.enable_utc = True
app.conf.timezone = settings.TIME_ZONE
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')