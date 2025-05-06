from rest_framework import serializers
from moiraflow.models import RegistroDiario

class SintomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroDiario
        fields = [
            'dolor_cabeza', 'dolor_espalda', 'fatiga',
            'senos_sensibles', 'retencion_liquidos', 'antojos',
            'acné', 'sofocos', 'cambios_apetito', 'insomnio',
            'sensibilidad_pezon', 'crecimiento_mamario'
        ]