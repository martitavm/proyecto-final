from celery import shared_task
from django.core.management import call_command

@shared_task
def generar_notificaciones_recordatorios():
    call_command('generar_notificaciones_recordatorios')