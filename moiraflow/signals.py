from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from moiraflow.models import (
    RegistroDiario,
    CicloMenstrual,
    TratamientoHormonal,
    Perfil, Recordatorio
)

User = get_user_model()


def conectar_signals():
    """Conexión explícita de todas las signals"""
    # Las signals ya están conectadas mediante @receiver
    # Esta función queda como punto central de configuración
    pass

@receiver(post_save, sender=Recordatorio)
def crear_notificacion_recordatorio(sender, instance, created, **kwargs):
    """
    Crea una notificación cuando se crea o modifica un recordatorio
    """
    if created or instance.esta_pendiente():

        pass