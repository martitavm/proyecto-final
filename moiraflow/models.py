from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import get_user

class Perfil(models.Model):
    """
    Modelo para almacenar información adicional del usuario.
    """
    TIPO_PERFIL_CHOICES = [
        ('usuario', 'Usuario normal'),
        ('autor', 'Autor/Artículos'),
        ('administracion', 'Administración'),
    ]

    TIPO_SEGUIMIENTO_CHOICES = [
        ('ciclo_menstrual', 'Ciclo Menstrual'),
        ('tratamiento_hormonal', 'Tratamiento Hormonal'),
        ('ambos', 'Ambos'),
        ('ninguno', 'Sin seguimiento especial'),
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
    tipo_seguimiento = models.CharField(max_length=20, choices=TIPO_SEGUIMIENTO_CHOICES, default='ninguno')
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


# Nuevo modelo para tratamientos hormonales
class TratamientoHormonal(models.Model):
    """
    Modelo para seguimiento de tratamientos hormonales
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tratamientos_hormonales')
    nombre_tratamiento = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"Tratamiento de {self.usuario.username} - {self.nombre_tratamiento}"

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
    Modelo para registrar información diaria durante el ciclo o tratamiento.
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

    COLOR_FLUJO_CHOICES = [
        ('rojo', 'Rojo vivo'),
        ('oscuro', 'Rojo oscuro'),
        ('marron', 'Marrón'),
        ('rosado', 'Rosado')
    ]

    LIBIDO_CHOICES = [
        ('aumento', 'Aumento'),
        ('disminucion', 'Disminución'),
        ('normal', 'Normal')
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_diarios')
    ciclo = models.ForeignKey('CicloMenstrual', on_delete=models.CASCADE, related_name='registros', null=True,
                              blank=True)
    tratamiento = models.ForeignKey('TratamientoHormonal', on_delete=models.CASCADE, related_name='registros',
                                    null=True, blank=True)
    fecha = models.DateField()

    # --- Campos comunes a todos los tipos de seguimiento ---
    # Estados físicos generales
    dolor_cabeza = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Intensidad de dolor de cabeza (0-10)",
        verbose_name="Dolor de cabeza"
    )
    dolor_espalda = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Intensidad de dolor de espalda (0-10)",
        verbose_name="Dolor de espalda"
    )
    fatiga = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Nivel de fatiga (0-10)",
        verbose_name="Fatiga"
    )

    # Estados emocionales/anímicos
    estados_animo = models.CharField(
        max_length=100,
        blank=True,
        help_text="Separados por comas si hay varios"
    )

    # Hábitos
    cambios_apetito = models.BooleanField(
        default=False,
        help_text="¿Has experimentado cambios en el apetito?",
        verbose_name="Cambios en el apetito"
    )
    insomnio = models.BooleanField(
        default=False,
        help_text="¿Has tenido dificultades para dormir?",
        verbose_name="Insomnio"
    )

    # --- Campos específicos para seguimiento menstrual ---
    es_dia_periodo = models.BooleanField(
        default=False,
        verbose_name="Día de período"
    )
    flujo_menstrual = models.CharField(
        max_length=15,
        choices=FLUJO_CHOICES,
        blank=True, null=True,
        verbose_name="Flujo menstrual"
    )
    coagulos = models.BooleanField(
        default=False,
        help_text="¿Has notado coágulos en el flujo?",
        verbose_name="Coágulos"
    )
    color_flujo = models.CharField(
        max_length=20,
        choices=COLOR_FLUJO_CHOICES,
        blank=True, null=True,
        verbose_name="Color del flujo"
    )
    senos_sensibles = models.BooleanField(
        default=False,
        help_text="¿Tienes los senos/sensibilidad mamaria aumentada?",
        verbose_name="Senos sensibles"
    )
    retencion_liquidos = models.BooleanField(
        default=False,
        help_text="¿Sientes retención de líquidos?",
        verbose_name="Retención de líquidos"
    )
    antojos = models.BooleanField(
        default=False,
        help_text="¿Has tenido antojos alimenticios?",
        verbose_name="Antojos"
    )
    acné = models.BooleanField(
        default=False,
        help_text="¿Has notado aumento de acné?",
        verbose_name="Acné"
    )

    # --- Campos específicos para tratamiento hormonal ---
    medicacion_tomada = models.BooleanField(
        default=False,
        verbose_name="Medicación tomada"
    )
    hora_medicacion = models.TimeField(
        null=True, blank=True,
        verbose_name="Hora de medicación"
    )
    sensibilidad_pezon = models.BooleanField(
        default=False,
        help_text="¿Sensibilidad en los pezones?",
        verbose_name="Sensibilidad en pezones"
    )
    cambios_libido = models.CharField(
        max_length=11,
        choices=LIBIDO_CHOICES,
        blank=True, null=True,
        verbose_name="Cambios en la libido"
    )
    sofocos = models.BooleanField(
        default=False,
        help_text="¿Has experimentado sofocos?",
        verbose_name="Sofocos"
    )
    cambios_piel = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text="Describe cambios en la piel",
        verbose_name="Cambios en la piel"
    )
    crecimiento_mamario = models.BooleanField(
        default=False,
        help_text="¿Has notado crecimiento mamario?",
        verbose_name="Crecimiento mamario"
    )

    # --- Campos adicionales ---
    medicamentos = models.TextField(
        blank=True,
        verbose_name="Medicamentos adicionales"
    )
    notas = models.TextField(
        blank=True,
        verbose_name="Notas adicionales"
    )
    otros_sintomas = models.TextField(
        blank=True,
        help_text="Describe cualquier otro síntoma no listado",
        verbose_name="Otros síntomas"
    )

    def __str__(self):
        return f"Registro de {self.usuario.username} del {self.fecha}"

    @property
    def es_registro_menstrual(self):
        return self.ciclo is not None and self.usuario.perfil.tipo_seguimiento in ['ciclo_menstrual', 'ambos']

    @property
    def es_registro_hormonal(self):
        return self.tratamiento is not None and self.usuario.perfil.tipo_seguimiento in ['tratamiento_hormonal',
                                                                                         'ambos']
    def clean(self):
        if self.es_registro_menstrual and not self.es_dia_periodo and self.flujo_menstrual:
            raise ValidationError("No puede haber flujo menstrual si no es día de período")

        if self.es_registro_hormonal and self.medicacion_tomada and not self.hora_medicacion:
            raise ValidationError("Debe especificar la hora de la medicación")


    class Meta:
        ordering = ['-fecha']
        unique_together = ['usuario', 'fecha']


# Mejora al modelo Recordatorio para permitir recordatorios más específicos
class Recordatorio(models.Model):
    """
    Modelo para recordatorios de medicación, citas, etc.
    """
    TIPO_CHOICES = [
        ('medicacion', 'Medicación'),
        ('medicacion_hormonal', 'Medicación Hormonal'),
        ('cita_medica', 'Cita médica'),
        ('inicio_periodo', 'Inicio de período esperado'),
        ('ovulacion', 'Ovulación esperada'),
        ('otro', 'Otro'),
    ]

    FRECUENCIA_CHOICES = [
        ('diaria', 'Diaria'),
        ('cada_x_dias', 'Cada X días'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('ciclo', 'Basada en ciclo'),
        ('unica', 'Única vez'),
    ]

    METODO_NOTIFICACION_CHOICES = [
        ('app', 'Notificación en app'),
        ('email', 'Correo electrónico'),
        ('ambos', 'App y correo'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordatorios')
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha_inicio = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    frecuencia = models.CharField(max_length=15, choices=FRECUENCIA_CHOICES)
    dias_frecuencia = models.PositiveIntegerField(default=1, help_text="Para frecuencia 'Cada X días'")
    metodo_notificacion = models.CharField(max_length=10, choices=METODO_NOTIFICACION_CHOICES, default='app')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"


# Nuevo modelo para estadísticas
class EstadisticaUsuario(models.Model):
    """
    Modelo para almacenar estadísticas calculadas del usuario
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='estadisticas')
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    duracion_ciclo_promedio_calculado = models.FloatField(null=True, blank=True)
    duracion_periodo_promedio_calculado = models.FloatField(null=True, blank=True)
    dias_ovulacion_tipicos = models.CharField(max_length=100, blank=True,
                                              help_text="Días del ciclo separados por comas")
    sintomas_comunes = models.TextField(blank=True, help_text="JSON con síntomas frecuentes y su frecuencia")
    estados_animo_comunes = models.TextField(blank=True, help_text="JSON con estados de ánimo frecuentes")

    def __str__(self):
        return f"Estadísticas de {self.usuario.username}"


# Nuevo modelo para seguimiento de efectos de tratamientos hormonales
class EfectoTratamiento(models.Model):
    """
    Modelo para seguimiento de efectos de tratamientos hormonales
    """
    TIPO_EFECTO_CHOICES = [
        ('fisico', 'Físico'),
        ('emocional', 'Emocional'),
        ('secundario', 'Efecto secundario'),
        ('deseado', 'Efecto deseado'),
        ('otro', 'Otro'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='efectos_tratamiento')
    tratamiento = models.ForeignKey('TratamientoHormonal', on_delete=models.CASCADE, related_name='efectos')
    nombre_efecto = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo_efecto = models.CharField(max_length=15, choices=TIPO_EFECTO_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    intensidad = models.PositiveIntegerField(choices=[(1, 'Muy leve'), (2, 'Leve'), (3, 'Moderado'),
                                                      (4, 'Intenso'), (5, 'Muy intenso')], default=3)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre_efecto} - {self.tratamiento.nombre_tratamiento} - {self.usuario.username}"

class Articulo(models.Model):
    """
    Modelo para artículos creados por autores
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado'),
    ]

    CATEGORIA_CHOICES = [
        ('salud_menstrual', 'Salud Menstrual'),
        ('tratamientos_hormonales', 'Tratamientos Hormonales'),
        ('bienestar', 'Bienestar General'),
        ('consejos', 'Consejos Prácticos'),
        ('investigacion', 'Investigación'),
        ('historias', 'Historias Personales'),
    ]

    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articulos')
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    contenido = models.TextField()
    imagen_portada = models.ImageField(upload_to='articulos/', null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='borrador')
    categoria = models.CharField(max_length=25, choices=CATEGORIA_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    destacado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_publicacion']
        verbose_name = 'Artículo'
        verbose_name_plural = 'Artículos'

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        if self.estado == 'publicado' and not self.fecha_publicacion:
            self.fecha_publicacion = timezone.now()
        super().save(*args, **kwargs)