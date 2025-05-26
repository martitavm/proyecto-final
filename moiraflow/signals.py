from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Recordatorio, Notificacion
from datetime import timedelta


@receiver(post_save, sender=Recordatorio)
def crear_notificacion_recordatorio(sender, instance, created, **kwargs):
    hoy = timezone.now().date()

    if not (instance.activo and instance.notificar):
        return

    # Notificación inicial solo si es creación nueva
    if created:
        mensaje = f"Nuevo recordatorio: {instance.titulo} para el {instance.fecha_inicio.strftime('%d/%m/%Y')}"
        Notificacion.objects.get_or_create(
            usuario=instance.usuario,
            recordatorio=instance,
            mensaje=mensaje,
            defaults={'leida': False}
        )