from rest_framework import serializers
from moiraflow.models import RegistroDiario, Perfil, User

class SintomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroDiario
        fields = [
            'dolor_cabeza', 'dolor_espalda', 'fatiga',
            'senos_sensibles', 'retencion_liquidos', 'antojos',
            'acné', 'sofocos', 'cambios_apetito', 'insomnio',
            'sensibilidad_pezon', 'crecimiento_mamario'
        ]

class EstadisticasSerializer(serializers.Serializer):
    total_usuarios = serializers.IntegerField()
    usuarios_activos = serializers.IntegerField()
    usuarios_nuevos_ultimo_mes = serializers.IntegerField()
    endpoints = serializers.DictField()

class GeneroSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())
    titulo = serializers.CharField()

class SintomasSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())
    titulo = serializers.CharField()

class EdadesSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())
    titulo = serializers.CharField()

class SeguimientoSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())
    titulo = serializers.CharField()
