import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.enable_utc = True
app.conf.timezone = 'America/Guayaquil' 
app.autodiscover_tasks()