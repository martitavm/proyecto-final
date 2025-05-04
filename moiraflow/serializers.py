from rest_framework import serializers

class SintomaSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    dias_presente = serializers.IntegerField()
    intensidad_promedio = serializers.FloatField(allow_null=True)  # Permitimos null