import random
from collections import defaultdict
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
#from django_cron import CronJobBase, Schedule

class Perfil(models.Model):
    class TipoPerfil(models.TextChoices):
        USUARIO = 'usuario', 'Usuario normal'
        AUTOR = 'autor', 'Autor/Artículos'
        ADMIN = 'administracion', 'Administración'

    class TipoSeguimiento(models.TextChoices):
        MENSTRUAL = 'ciclo_menstrual', 'Ciclo Menstrual'
        HORMONAL = 'tratamiento_hormonal', 'Tratamiento Hormonal'

    class Genero(models.TextChoices):
        FEMENINO = 'femenino', 'Femenino'
        MASCULINO_TRANS = 'masculino trans', 'Masculino Trans'
        FEMENINO_TRANS = 'femenino trans', 'Femenino Trans'
        OTRO = 'otro', 'Otro'

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    foto_perfil = models.ImageField(upload_to="perfiles/", null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=20, choices=Genero.choices)
    duracion_ciclo_promedio = models.PositiveIntegerField(
        null=True, blank=True,
        default=28,
        help_text="Duración promedio del ciclo en días (solo para seguimiento menstrual)"
    )
    duracion_periodo_promedio = models.PositiveIntegerField(
        null=True, blank=True,
        default=5,
        help_text="Duración promedio del período en días (solo para seguimiento menstrual)"
    )
    es_premium = models.BooleanField(default=False)
    tipo_perfil = models.CharField(max_length=15, choices=TipoPerfil.choices, default=TipoPerfil.USUARIO)
    tipo_seguimiento = models.CharField(max_length=20, choices=TipoSeguimiento.choices)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Asignación automática de tipo_seguimiento basado en género
        if self.genero in [self.Genero.FEMENINO, self.Genero.MASCULINO_TRANS]:
            self.tipo_seguimiento = self.TipoSeguimiento.MENSTRUAL
        elif self.genero == self.Genero.FEMENINO_TRANS:
            self.tipo_seguimiento = self.TipoSeguimiento.HORMONAL

        # Limpieza de campos no relevantes
        if self.tipo_seguimiento != self.TipoSeguimiento.MENSTRUAL:
            self.duracion_ciclo_promedio = None
            self.duracion_periodo_promedio = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    @property
    def es_autor(self):
        return self.tipo_perfil == 'autor'

    @property
    def es_administrador(self):
        return self.tipo_perfil == 'administracion'

    @property
    def puede_acceder_premium(self):
        return self.es_premium or self.es_administrador

    def calcular_estadisticas_ciclo(self):
        ciclos = CicloMenstrual.objects.filter(usuario=self.usuario).exclude(fecha_fin__isnull=True)
        if not ciclos.exists():
            return None

        # Cálculo de duraciones
        duraciones = [c.duracion for c in ciclos]
        promedio = sum(duraciones) / len(duraciones)

        # Fases más comunes con síntomas
        estadisticas = {
            'total_ciclos': len(duraciones),
            'duracion_promedio': promedio,
            'duracion_min': min(duraciones),
            'duracion_max': max(duraciones),
            'regularidad': (max(duraciones) - min(duraciones)) <= 3  # Consideramos regular si varía menos de 3 días
        }
        return estadisticas


# Nuevo modelo para tratamientos hormonales
class TratamientoHormonal(models.Model):
    class TipoHormona(models.TextChoices):
        ESTROGENO = 'estrogeno', 'Estógeno'
        PROGESTERONA = 'progesterona', 'Progesterona'
        TESTOSTERONA = 'testosterona', 'Testosterona'
        COMBINADO = 'combinado', 'Combinado'

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tratamientos_hormonales')
    nombre_tratamiento = models.CharField(max_length=100)
    tipo_hormona = models.CharField(max_length=12, choices=TipoHormona.choices)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    dosis = models.DecimalField(max_digits=6, decimal_places=2)  # Más preciso que CharField
    frecuencia = models.PositiveIntegerField(help_text="Veces por día/semana según frecuencia_tipo")
    frecuencia_tipo = models.CharField(max_length=10, choices=[('diario', 'Diario'), ('semanal', 'Semanal')])
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)

    @property
    def dosis_diaria(self):
        if self.frecuencia_tipo == 'diario':
            return self.dosis / self.frecuencia
        elif self.frecuencia_tipo == 'semanal':
            return (self.dosis / self.frecuencia) / 7
        return 0

    # Añadir método para verificar si está activo en una fecha
    def esta_activo_en_fecha(self, fecha=None):
        fecha = fecha or timezone.now().date()
        return (self.activo and
                self.fecha_inicio <= fecha and
                (self.fecha_fin is None or fecha <= self.fecha_fin))

    # Añadir propiedad para progreso del tratamiento
    @property
    def progreso(self):
        if not self.fecha_fin:
            return None
        total_dias = (self.fecha_fin - self.fecha_inicio).days
        dias_transcurridos = (timezone.now().date() - self.fecha_inicio).days
        return min(100, max(0, int((dias_transcurridos / total_dias) * 100)))

    def __str__(self):
        return f"Tratamiento de {self.usuario.username} - {self.nombre_tratamiento}"

# Resto de los modelos permanecen igual...
class CicloMenstrual(models.Model):
    class FaseCiclo(models.TextChoices):
        FOLICULAR = 'folicular', 'Fase Folicular'
        OVULACION = 'ovulacion', 'Ovulación'
        LUTEA = 'lutea', 'Fase Lútea'
        MENSTRUAL = 'menstrual', 'Fase Menstrual'

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ciclos')
    fecha_inicio = models.DateField(help_text="Primer día de menstruación")
    fecha_fin = models.DateField(
        null=True, blank=True,
        help_text="Último día antes del siguiente ciclo",
        verbose_name="Fecha de fin (automática)"
    )
    fase_actual = models.CharField(
        max_length=10,
        choices=FaseCiclo.choices,
        blank=True,
        null=True,
        editable=False  # Se calcula automáticamente
    )
    notas = models.TextField(blank=True)
    sintomas_importantes = models.JSONField(default=dict, blank=True)  # Más flexible que CharField

    @property
    def duracion(self):
        """Calcula la duración en días, incluyendo ambos extremos"""
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days + 1
        return None

    def determinar_fase(self, fecha=None):
        fecha = fecha or timezone.now().date()

        if not all([self.fecha_inicio, self.fecha_fin, self.fecha_inicio <= fecha <= self.fecha_fin]):
            return None

        dias_transcurridos = (fecha - self.fecha_inicio).days
        perfil = self.usuario.perfil

        # Cálculo basado en porcentajes del ciclo
        porcentaje_ciclo = dias_transcurridos / self.duracion

        if porcentaje_ciclo < 0.2:  # Primer 20% -> menstrual
            return self.FaseCiclo.MENSTRUAL
        elif porcentaje_ciclo < 0.5:  # 20-50% -> folicular
            return self.FaseCiclo.FOLICULAR
        elif porcentaje_ciclo < 0.6:  # 50-60% -> ovulación
            return self.FaseCiclo.OVULACION
        else:  # Restante -> lútea
            return self.FaseCiclo.LUTEA

    def save(self, *args, **kwargs):
        # Actualizar fase actual al guardar
        if self.fecha_inicio and self.fecha_fin:
            self.fase_actual = self.determinar_fase()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ciclo de {self.usuario.username} iniciado el {self.fecha_inicio}"

    class Meta:
        ordering = ['-fecha_inicio']


from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class RegistroDiario(models.Model):
    """
    Modelo para registro diario que varía completamente según el tipo de seguimiento:
    - Ciclo menstrual (género femenino o masculino trans)
    - Tratamiento hormonal (género femenino trans)
    """

    # ---------------------------
    # Opciones comunes (para ambos tipos)
    # ---------------------------
    class EstadoAnimo(models.TextChoices):
        FELIZ = 'feliz', 'Feliz'
        TRISTE = 'triste', 'Triste'
        IRRITABLE = 'irritable', 'Irritable'
        ANSIOSO = 'ansioso', 'Ansioso/a'
        NEUTRAL = 'neutral', 'Neutral'
        CANSADO = 'cansado', 'Cansado/a'
        ENERGETICO = 'energico', 'Enérgico/a'

    class SintomasComunes(models.TextChoices):
        DOLOR_CABEZA = 'dolor_cabeza', 'Dolor de cabeza'
        DOLOR_ESPALDA = 'dolor_espalda', 'Dolor de espalda'
        FATIGA = 'fatiga', 'Fatiga'
        CAMBIOS_APETITO = 'cambios_apetito', 'Cambios en el apetito'
        INSOMNIO = 'insomnio', 'Insomnio'

    # ---------------------------
    # Campos base
    # ---------------------------
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='registros_diarios'
    )
    fecha = models.DateField(default=timezone.now)

    # Campos comunes a todos
    estados_animo = models.JSONField(default=list)  # Almacena claves de EstadoAnimo
    sintomas_comunes = models.JSONField(default=list)  # Almacena claves de SintomasComunes
    notas = models.TextField(blank=True)

    # ---------------------------
    # Campos específicos para CICLO MENSTRUAL
    # ---------------------------
    ciclo = models.ForeignKey(
        CicloMenstrual,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros'
    )

    class FlujoMenstrual(models.TextChoices):
        NULO = 'nulo', 'Nulo'
        LIGERO = 'ligero', 'Ligero'
        MODERADO = 'moderado', 'Moderado'
        ABUNDANTE = 'abundante', 'Abundante'
        MUY_ABUNDANTE = 'muy_abundante', 'Muy abundante'

    class ColorFlujo(models.TextChoices):
        ROJO = 'rojo', 'Rojo vivo'
        OSCURO = 'oscuro', 'Rojo oscuro'
        MARRON = 'marron', 'Marrón'
        ROSADO = 'rosado', 'Rosado'

    es_dia_periodo = models.BooleanField(default=False)
    flujo_menstrual = models.CharField(
        max_length=15,
        choices=FlujoMenstrual.choices,
        blank=True, null=True
    )
    coagulos = models.BooleanField(default=False)
    color_flujo = models.CharField(
        max_length=20,
        choices=ColorFlujo.choices,
        blank=True, null=True
    )
    senos_sensibles = models.BooleanField(default=False)
    retencion_liquidos = models.BooleanField(default=False)
    antojos = models.BooleanField(default=False)
    acne = models.BooleanField(default=False)

    # ---------------------------
    # Campos específicos para TRATAMIENTO HORMONAL
    # ---------------------------
    tratamiento = models.ForeignKey(
        TratamientoHormonal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros'
    )

    class Libido(models.TextChoices):
        AUMENTO = 'aumento', 'Aumento'
        DISMINUCION = 'disminucion', 'Disminución'
        NORMAL = 'normal', 'Normal'

    medicacion_tomada = models.BooleanField(default=False)
    hora_medicacion = models.TimeField(null=True, blank=True)
    sensibilidad_pezon = models.BooleanField(default=False)
    cambios_libido = models.CharField(
        max_length=11,
        choices=Libido.choices,
        blank=True, null=True
    )
    sofocos = models.BooleanField(default=False)
    cambios_piel = models.CharField(max_length=100, blank=True)
    crecimiento_mamario = models.BooleanField(default=False)

    # ---------------------------
    # Métodos y propiedades
    # ---------------------------
    @property
    def tipo_seguimiento(self):
        """Determina automáticamente el tipo de seguimiento basado en el perfil del usuario"""
        return self.usuario.perfil.tipo_seguimiento

    @property
    def fase_ciclo(self):
        """Para registros menstruales, devuelve la fase actual"""
        if self.tipo_seguimiento == 'ciclo_menstrual' and self.ciclo:
            return self.ciclo.determinar_fase(self.fecha)
        return None

    def clean(self):
        # No validar si no hay usuario asignado
        if not hasattr(self, 'usuario') or not self.usuario:
            return

        # Validación específica para cada tipo de seguimiento
        if self.usuario.perfil.tipo_seguimiento == 'ciclo_menstrual':
            if not self.ciclo:
                raise ValidationError("Debe asociar un ciclo menstrual para este tipo de registro")

            if not self.es_dia_periodo and any([self.flujo_menstrual, self.coagulos, self.color_flujo]):
                raise ValidationError({
                    'es_dia_periodo': "Los detalles menstruales solo pueden registrarse en días de período"
                })

        elif self.usuario.perfil.tipo_seguimiento == 'tratamiento_hormonal':
            if not self.tratamiento:
                raise ValidationError("Debe asociar un tratamiento hormonal para este tipo de registro")

            if self.medicacion_tomada and not self.hora_medicacion:
                raise ValidationError({
                    'hora_medicacion': "Debe especificar la hora de la medicación"
                })

        # Limpiar campos que no correspondan al tipo de seguimiento
        if self.tipo_seguimiento == 'ciclo_menstrual':
            self.tratamiento = None
            # Limpiar campos hormonales
            self.medicacion_tomada = False
            self.hora_medicacion = None
            self.sensibilidad_pezon = False
            self.cambios_libido = None
            self.sofocos = False
            self.cambios_piel = ''
            self.crecimiento_mamario = False

        elif self.tipo_seguimiento == 'tratamiento_hormonal':
            self.ciclo = None
            # Limpiar campos menstruales
            self.es_dia_periodo = False
            self.flujo_menstrual = None
            self.coagulos = False
            self.color_flujo = None
            self.senos_sensibles = False
            self.retencion_liquidos = False
            self.antojos = False
            self.acne = False

    class Meta:
        ordering = ['-fecha']
        unique_together = ['usuario', 'fecha']
        verbose_name = 'Registro diario'
        verbose_name_plural = 'Registros diarios'

    def __str__(self):
        return f"Registro de {self.usuario.username} ({self.tipo_seguimiento}) - {self.fecha}"

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
    class Meta:
        verbose_name = "Estadísticas de usuario"
        verbose_name_plural = "Estadísticas de usuarios"

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='estadisticas')
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    # Menstrual
    duracion_ciclo_promedio = models.FloatField(null=True, blank=True, help_text="Días")
    variabilidad_ciclo = models.FloatField(null=True, blank=True, help_text="Desviación estándar en días")
    dias_ovulacion_probables = models.JSONField(default=list, help_text="Días del ciclo más probables para ovulación")

    # Síntomas (común a ambos)
    sintomas_frecuentes = models.JSONField(
        default=list,
        help_text="Lista de {'sintoma': str, 'frecuencia': int, 'fase_ciclo': str|null}"
    )

    # Hormonal
    progreso_tratamiento = models.JSONField(
        null=True, blank=True,
        help_text="Para tratamientos activos: {'progreso': %, 'efectividad_estimada': %}"
    )

    # Métricas emocionales
    estado_animo_promedio = models.JSONField(
        default=dict,
        help_text="Distribución de estados de ánimo: {'feliz': 25%, 'cansado': 15%, ...}"
    )

    # Nuevos campos para análisis visual
    ciclo_heatmap_data = models.JSONField(
        default=dict,
        help_text="Datos para calendario de ciclo (ej: {'2023-10-01': 'menstrual', ...})"
    )

    tratamiento_progreso_data = models.JSONField(
        default=list,
        help_text="Evolución semanal de síntomas hormonales"
    )

    sintomas_por_fase = models.JSONField(
        default=dict,
        help_text="Frecuencia de síntomas por fase (ej: {'folicular': {'dolor_cabeza': 3}})"
    )

    def actualizar_estadisticas(self):
        """Método que centraliza todos los cálculos"""
        perfil = self.usuario.perfil

        if perfil.tipo_seguimiento == 'ciclo_menstrual':
            self.actualizar_datos_ciclo()
        elif perfil.tipo_seguimiento == 'tratamiento_hormonal':
            self.actualizar_datos_hormonal()

        # Actualizar métricas comunes a ambos tipos
        self.actualizar_estados_animo()
        self.save()

    def actualizar_datos_ciclo(self):
        """Actualiza todos los datos para análisis de ciclo menstrual"""
        ciclos = CicloMenstrual.objects.filter(
            usuario=self.usuario
        ).exclude(fecha_fin__isnull=True)

        if not ciclos.exists():
            return

        # Calcular duraciones
        duraciones = [c.duracion for c in ciclos if c.duracion is not None]

        if duraciones:
            self.duracion_ciclo_promedio = sum(duraciones) / len(duraciones)
            self.variabilidad_ciclo = max(duraciones) - min(duraciones)

            # Calcular días probables de ovulación (aproximadamente 14 días antes del fin del ciclo)
            self.dias_ovulacion_probables = [
                int(self.duracion_ciclo_promedio) - 14
            ]

        # Actualizar heatmap y síntomas por fase
        registros = RegistroDiario.objects.filter(
            usuario=self.usuario,
            ciclo__isnull=False
        ).select_related('ciclo')

        # Heatmap
        self.ciclo_heatmap_data = {
            str(r.fecha): r.ciclo.determinar_fase(r.fecha)
            for r in registros if r.ciclo
        }

        # Síntomas por fase
        sintomas_por_fase = defaultdict(lambda: defaultdict(int))
        for r in registros:
            if r.ciclo and r.sintomas_comunes:
                fase = r.ciclo.determinar_fase(r.fecha)
                for sintoma in r.sintomas_comunes:
                    sintomas_por_fase[fase][sintoma] += 1

        self.sintomas_por_fase = dict(sintomas_por_fase)

    def actualizar_datos_hormonal(self):
        """Actualiza datos para análisis de tratamiento hormonal"""
        tratamientos = TratamientoHormonal.objects.filter(
            usuario=self.usuario,
            activo=True
        )

        # Progreso semanal
        progreso = defaultdict(dict)
        for t in tratamientos:
            semanas = (timezone.now().date() - t.fecha_inicio).days // 7
            for semana in range(semanas + 1):
                inicio_semana = t.fecha_inicio + timedelta(weeks=semana)
                fin_semana = inicio_semana + timedelta(days=6)

                registros = RegistroDiario.objects.filter(
                    usuario=self.usuario,
                    tratamiento=t,
                    fecha__range=(inicio_semana, fin_semana)
                )

                for sintoma in ['sofocos', 'cambios_libido', 'sensibilidad_pezon']:
                    count = registros.filter(**{sintoma: True}).count()
                    progreso[f"Semana {semana + 1}"][sintoma] = count

        self.tratamiento_progreso_data = dict(progreso)

        # Calcular progreso del tratamiento
        if tratamientos.exists():
            tratamiento = tratamientos.first()
            if tratamiento.fecha_fin:
                total_dias = (tratamiento.fecha_fin - tratamiento.fecha_inicio).days
                dias_transcurridos = (timezone.now().date() - tratamiento.fecha_inicio).days
                self.progreso_tratamiento = {
                    'progreso': min(100, max(0, int((dias_transcurridos / total_dias) * 100))),
                    'efectividad_estimada': 80  # Valor temporal, puedes implementar tu propia lógica
                }

    def actualizar_estados_animo(self):
        """Actualiza las estadísticas de estados de ánimo"""
        registros = RegistroDiario.objects.filter(usuario=self.usuario)

        contador_animos = defaultdict(int)
        total_registros = 0

        for r in registros:
            if r.estados_animo:
                for animo in r.estados_animo:
                    contador_animos[animo] += 1
                total_registros += 1

        if total_registros > 0:
            self.estado_animo_promedio = {
                animo: f"{round((count / total_registros) * 100)}%"
                for animo, count in contador_animos.items()
            }
        else:
            self.estado_animo_promedio = {}

    def __str__(self):
        return f"Estadísticas de {self.usuario.username}"



# class ActualizarEstadisticasCronJob(CronJobBase):
#    schedule = Schedule(run_every_mins=1440)  # 24h
#    code = 'app.actualizar_estadisticas'

#    def do(self):
#        for usuario in User.objects.all():
#            stats, _ = EstadisticaUsuario.objects.get_or_create(usuario=usuario)
#            stats.actualizar_estadisticas()


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
    # Añade estas opciones
    EFECTO_CHOICES = [
        ('aumento_energia', 'Aumento de energía'),
        ('cambios_humor', 'Cambios de humor'),
        ('sensibilidad_pechos', 'Sensibilidad en los pechos'),
        ('nauseas', 'Náuseas'),
        ('aumento_peso', 'Aumento de peso'),
        ('dolor_cabeza', 'Dolor de cabeza'),
        ('sofocos', 'Sofocos'),
        ('sequedad_vaginal', 'Sequedad vaginal'),
        ('libido_aumentada', 'Libido aumentada'),
        ('libido_disminuida', 'Libido disminuida'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='efectos_tratamiento')
    tratamiento = models.ForeignKey('TratamientoHormonal', on_delete=models.CASCADE, related_name='efectos')
    nombre_efecto = models.CharField(
        max_length=20,
        choices=EFECTO_CHOICES,
        help_text="Efecto específico del tratamiento"
    )
    descripcion = models.TextField(blank=True)
    tipo_efecto = models.CharField(max_length=15, choices=TIPO_EFECTO_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    intensidad = models.PositiveIntegerField(choices=[(1, 'Muy leve'), (2, 'Leve'), (3, 'Moderado'),
                                                      (4, 'Intenso'), (5, 'Muy intenso')], default=3)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre_efecto} - {self.tratamiento.nombre_tratamiento} - {self.usuario.username}"

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Articulo(models.Model):
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
        if self.estado == 'publicado' and not self.fecha_publicacion:
            self.fecha_publicacion = timezone.now()
        super().save(*args, **kwargs)

    def puede_editar(self, user):
        """Determina si un usuario puede editar este artículo"""
        return user == self.autor or user.perfil.es_administrador


class Mascota(models.Model):
    ESTADOS = [
        ('normal', 'Normal'),
        ('hambrienta', 'Hambrienta'),
        ('feliz', 'Feliz'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mascota')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='normal')
    nivel_hambre = models.PositiveIntegerField(default=50)  # Rango de 0 a 100
    ultimo_cambio_estado = models.DateTimeField(auto_now=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    CONSEJOS = [
        "Recuerda beber suficiente agua hoy 💧",
        "Hoy es un buen día para hacer ejercicio 🏃‍♀️",
        "No olvides tomarte un tiempo para relajarte 🧘‍♀️",
        "¿Has registrado tus síntomas hoy? 📝",
        "Mantén una dieta equilibrada hoy 🥗",
    ]

    def __str__(self):
        return f"Mascota de {self.usuario.username}"

    @property
    def imagen_estado(self):
        return f'images/mascota_{self.estado}.gif'

    def puede_dar_consejo(self):
        return self.nivel_hambre >= 15

    def alimentar(self):
        # Aumentar nivel de hambre (entre 20 y 40 puntos)
        self.nivel_hambre = min(100, self.nivel_hambre + random.randint(20, 40))
        self.actualizar_estado()
        self.save()
        return True

    def dar_consejo(self):
        if self.puede_dar_consejo():
            # Disminuir hambre al dar consejo
            self.nivel_hambre = max(0, self.nivel_hambre - random.randint(5, 15))
            # Forzar actualización del estado
            self.actualizar_estado()
            self.save()
            return random.choice(self.CONSEJOS)
        return None

    def actualizar_estado(self):
        if self.nivel_hambre < 30:
            self.estado = 'hambrienta'
        elif self.nivel_hambre > 70:
            self.estado = 'feliz'
        else:
            self.estado = 'normal'
        self.save()