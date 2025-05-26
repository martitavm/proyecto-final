from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Recordatorio, Notificacion


@shared_task
def generar_notificaciones_recordatorios():
    hoy = timezone.now().date()
    recordatorios = Recordatorio.objects.filter(
        activo=True,
        notificar=True,
        fecha_notificacion=hoy
    )

    for recordatorio in recordatorios:
        mensaje = f"Recordatorio próximo: {recordatorio.titulo} para el {recordatorio.proxima_fecha.strftime('%d/%m/%Y')}"

        # Verificar si ya existe una notificación similar hoy
        existe = Notificacion.objects.filter(
            usuario=recordatorio.usuario,
            recordatorio=recordatorio,
            mensaje=mensaje,
            fecha_creacion__date=hoy
        ).exists()

        if not existe:
            Notificacion.objects.create(
                usuario=recordatorio.usuario,
                recordatorio=recordatorio,
                mensaje=mensaje
            )

    return f"Generadas {recordatorios.count()} notificaciones"