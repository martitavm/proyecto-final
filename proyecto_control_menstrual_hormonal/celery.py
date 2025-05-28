import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_control_menstrual_hormonal.settings')

app = Celery('proyecto_control_menstrual_hormonal', broker='redis://localhost:6379/0')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()