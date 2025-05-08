from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    RegistroDiario, 
    CicloMenstrual, 
    TratamientoHormonal,
    EstadisticaUsuario,
    Perfil
)

User = get_user_model()

def _actualizar_con_retraso(estadisticas):
    """Función helper para actualización diferida"""
    from datetime import timedelta
    if (not estadisticas.ultima_actualizacion or 
        (timezone.now() - estadisticas.ultima_actualizacion) > timedelta(minutes=5)):
        estadisticas.actualizar_estadisticas()
        estadisticas.refresh_from_db()

@receiver(post_save, sender=User)
def crear_perfil_y_estadisticas(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)
        EstadisticaUsuario.objects.create(usuario=instance)

@receiver(post_save, sender=Perfil)
@receiver(post_delete, sender=Perfil)
def actualizar_estadisticas_cambio_perfil(sender, instance, **kwargs):
    if instance.usuario.perfil.puede_acceder_premium:
        with transaction.atomic():
            estadisticas, _ = EstadisticaUsuario.objects.select_for_update().get_or_create(
                usuario=instance.usuario
            )
            estadisticas.actualizar_estadisticas()

@receiver(post_save, sender=RegistroDiario)
@receiver(post_delete, sender=RegistroDiario)
def actualizar_estadisticas_registro(sender, instance, **kwargs):
    if instance.usuario.perfil.puede_acceder_premium:
        with transaction.atomic():
            estadisticas = EstadisticaUsuario.objects.select_for_update().get(
                usuario=instance.usuario
            )
            if not hasattr(estadisticas, '_pendiente_actualizacion'):
                estadisticas._pendiente_actualizacion = True
                transaction.on_commit(
                    lambda: _actualizar_con_retraso(estadisticas)
                )

@receiver(post_save, sender=CicloMenstrual)
@receiver(post_delete, sender=CicloMenstrual)
def actualizar_estadisticas_ciclo(sender, instance, **kwargs):
    if instance.usuario.perfil.puede_acceder_premium:
        with transaction.atomic():
            estadisticas = EstadisticaUsuario.objects.select_for_update().get(
                usuario=instance.usuario
            )
            estadisticas.actualizar_estadisticas()

@receiver(post_save, sender=TratamientoHormonal)
@receiver(post_delete, sender=TratamientoHormonal)
def actualizar_estadisticas_tratamiento(sender, instance, **kwargs):
    if instance.usuario.perfil.puede_acceder_premium:
        with transaction.atomic():
            estadisticas = EstadisticaUsuario.objects.select_for_update().get(
                usuario=instance.usuario
            )
            estadisticas.actualizar_estadisticas()

def conectar_signals():
    """Conexión explícita de todas las signals"""
    # Las signals ya están conectadas mediante @receiver
    # Esta función queda como punto central de configuración
    pass