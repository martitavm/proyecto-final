from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Perfil(models.Model):
    """
    Modelo para almacenar información adicional del usuario.
    """
    TIPO_PERFIL_CHOICES = [
        ('usuario', 'Usuario normal'),
        ('autor', 'Autor/Artículos'),
        ('administracion', 'Administración'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='perfil')
    foto_perfil = models.ImageField(upload_to="perfiles/", null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=50, blank=True)
    duracion_ciclo_promedio = models.PositiveIntegerField(default=28, help_text="Duración promedio del ciclo en días")
    duracion_periodo_promedio = models.PositiveIntegerField(default=5,
                                                            help_text="Duración promedio del período en días")
    es_premium = models.BooleanField(default=False, help_text="Indica si el usuario tiene cuenta premium")
    tipo_perfil = models.CharField(max_length=15, choices=TIPO_PERFIL_CHOICES, default='usuario')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    @property
    def es_autor(self):
        return self.tipo_perfil == 'autor'

    @property
    def es_administrador(self):
        return self.tipo_perfil == 'administracion'


# Resto de los modelos permanecen igual...
class CicloMenstrual(models.Model):
    """
    Modelo para registrar cada ciclo menstrual.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ciclos')
    fecha_inicio = models.DateField(help_text="Fecha de inicio del ciclo (primer día de menstruación)")
    fecha_fin = models.DateField(null=True, blank=True,
                                 help_text="Fecha de fin del ciclo (último día antes del siguiente ciclo)")
    duracion = models.PositiveIntegerField(null=True, blank=True, help_text="Duración total del ciclo en días")
    notas = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.fecha_fin and not self.duracion:
            delta = self.fecha_fin - self.fecha_inicio
            self.duracion = delta.days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ciclo de {self.usuario.username} iniciado el {self.fecha_inicio}"

    class Meta:
        ordering = ['-fecha_inicio']


class RegistroDiario(models.Model):
    """
    Modelo para registrar información diaria durante el ciclo.
    """
    FLUJO_CHOICES = [
        ('nulo', 'Nulo'),
        ('ligero', 'Ligero'),
        ('moderado', 'Moderado'),
        ('abundante', 'Abundante'),
        ('muy_abundante', 'Muy abundante'),
    ]

    ESTADO_ANIMO_CHOICES = [
        ('feliz', 'Feliz'),
        ('triste', 'Triste'),
        ('irritable', 'Irritable'),
        ('ansiosa', 'Ansiosa'),
        ('neutral', 'Neutral'),
        ('cansada', 'Cansada'),
        ('energica', 'Enérgica'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_diarios')
    ciclo = models.ForeignKey(CicloMenstrual, on_delete=models.CASCADE, related_name='registros', null=True, blank=True)
    fecha = models.DateField()
    es_dia_periodo = models.BooleanField(default=False)
    flujo_menstrual = models.CharField(max_length=15, choices=FLUJO_CHOICES, blank=True, null=True)
    estados_animo = models.CharField(max_length=100, blank=True, help_text="Separados por comas si hay varios")
    dolor = models.PositiveIntegerField(blank=True, null=True, help_text="Escala de 0-10")
    medicamentos = models.TextField(blank=True)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"Registro de {self.usuario.username} del {self.fecha}"

    def registrar_medicamento(self, medicamento, tomado=True, hora=None, dosis=None, notas=''):
        """
        Método para registrar la toma de un medicamento.
        """
        registro_medicamento, created = RegistroMedicamento.objects.get_or_create(
            registro_diario=self,
            medicamento=medicamento,
            defaults={
                'tomado': tomado,
                'hora_toma': hora,
                'dosis': dosis,
                'notas': notas
            }
        )

        if not created:
            registro_medicamento.tomado = tomado
            registro_medicamento.hora_toma = hora
            registro_medicamento.dosis = dosis
            registro_medicamento.notas = notas
            registro_medicamento.save()

        return registro_medicamento

    class Meta:
        ordering = ['-fecha']
        unique_together = ['usuario', 'fecha']


class Medicamento(models.Model):
    """
    Modelo para crear un catálogo de medicamentos.
    """
    TIPO_CHOICES = [
        ('anticonceptivo', 'Anticonceptivo'),
        ('hormonal', 'Tratamiento Hormonal'),
        ('otro', 'Otro')
    ]

    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    dosis_default = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.nombre


class RegistroMedicamento(models.Model):
    """
    Modelo para registrar la toma de medicamentos en un registro diario.
    """
    registro_diario = models.ForeignKey(RegistroDiario, on_delete=models.CASCADE, related_name='medicamentos_tomados')
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
    hora_toma = models.TimeField(null=True, blank=True)
    dosis = models.CharField(max_length=100, blank=True)
    notas = models.TextField(blank=True)
    tomado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.medicamento.nombre} - {self.registro_diario.fecha}"

    class Meta:
        unique_together = ['registro_diario', 'medicamento']


class Sintoma(models.Model):
    """
    Modelo para catálogo de síntomas.
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class RegistroSintoma(models.Model):
    """
    Modelo para relacionar síntomas con registros diarios.
    """
    INTENSIDAD_CHOICES = [
        (1, 'Muy leve'),
        (2, 'Leve'),
        (3, 'Moderado'),
        (4, 'Intenso'),
        (5, 'Muy intenso'),
    ]

    registro_diario = models.ForeignKey(RegistroDiario, on_delete=models.CASCADE, related_name='sintomas')
    sintoma = models.ForeignKey(Sintoma, on_delete=models.CASCADE)
    intensidad = models.PositiveIntegerField(choices=INTENSIDAD_CHOICES, default=3)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.sintoma.nombre} - {self.registro_diario.fecha}"

    class Meta:
        unique_together = ['registro_diario', 'sintoma']


class Recordatorio(models.Model):
    """
    Modelo para recordatorios de medicación, citas, etc.
    """
    TIPO_CHOICES = [
        ('medicacion', 'Medicación'),
        ('cita_medica', 'Cita médica'),
        ('inicio_periodo', 'Inicio de período esperado'),
        ('otro', 'Otro'),
    ]

    FRECUENCIA_CHOICES = [
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('ciclo', 'Basada en ciclo'),
        ('unica', 'Única vez'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordatorios')
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha_inicio = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    frecuencia = models.CharField(max_length=10, choices=FRECUENCIA_CHOICES)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"