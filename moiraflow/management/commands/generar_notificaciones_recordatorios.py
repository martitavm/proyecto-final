from django.core.management.base import BaseCommand
from django.utils import timezone
from moiraflow.models import Recordatorio, Notificacion
from datetime import timedelta

class Command(BaseCommand):
    help = 'Genera notificaciones para recordatorios programados para hoy'

    def handle(self, *args, **options):
        hoy = timezone.now().date()
        self.stdout.write(f"\nIniciando generación de notificaciones para {hoy}...")

        # Obtenemos todos los recordatorios activos y notificables
        recordatorios = Recordatorio.objects.filter(
            activo=True,
            notificar=True
        )

        notificaciones_generadas = 0

        for recordatorio in recordatorios:
            try:
                # Verificamos si hoy es la fecha de notificación
                if hoy == recordatorio.fecha_notificacion:
                    mensaje = f"Recordatorio próximo: {recordatorio.titulo} para el {recordatorio.proxima_fecha.strftime('%d/%m/%Y')}"

                    Notificacion.objects.create(
                        usuario=recordatorio.usuario,
                        recordatorio=recordatorio,
                        mensaje=mensaje
                    )
                    notificaciones_generadas += 1
                    self.stdout.write(f"Creada notificación: {mensaje}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error con recordatorio {recordatorio.id}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f'\nTotal generadas: {notificaciones_generadas} notificaciones'))