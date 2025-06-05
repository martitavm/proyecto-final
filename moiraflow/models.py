import random
from collections import defaultdict
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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


class Recordatorio(models.Model):
    """
    Modelo para recordatorios de medicación, citas, etc.
    """
    TIPO_CHOICES = [
        ('medicacion', 'Medicación'),
        ('medicacion_hormonal', 'Medicación Hormonal'),
        ('cita_medica', 'Cita médica'),
        ('otro', 'Otro'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordatorios')
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha_inicio = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    dias_frecuencia = models.PositiveIntegerField(
        default=1,
        help_text="Para frecuencia 'Cada X días' (0 para eventos únicos)"
    )
    activo = models.BooleanField(default=True)
    notificar = models.BooleanField(
        default=True,
        help_text="Enviar notificación al usuario"
    )
    dias_antelacion = models.PositiveIntegerField(
        default=1,
        help_text="Días de antelación para la notificación"
    )
    visto = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"

    @property
    def es_recurrente(self):
        return self.dias_frecuencia > 0

    @property
    def proxima_fecha(self):
        """Calcula la próxima fecha en la que debe activarse este recordatorio"""
        if not self.es_recurrente:
            return self.fecha_inicio

        hoy = timezone.now().date()
        delta = hoy - self.fecha_inicio
        dias_transcurridos = delta.days
        ciclos_completos = dias_transcurridos // self.dias_frecuencia
        proxima_fecha = self.fecha_inicio + timedelta(days=(ciclos_completos + 1) * self.dias_frecuencia)
        return proxima_fecha

    @property
    def fecha_notificacion(self):
        """Fecha en la que debe mostrarse la notificación"""
        return self.proxima_fecha - timedelta(days=self.dias_antelacion)

    def esta_pendiente(self):
        """Determina si el recordatorio está pendiente de notificación"""
        hoy = timezone.now().date()
        return (
                self.activo and
                self.notificar and
                not self.visto and
                hoy >= self.fecha_notificacion and
                hoy < self.proxima_fecha
        )

    def marcar_como_visto(self):
        """Marca el recordatorio como visto"""
        self.visto = True
        self.save()


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


class Notificacion(models.Model):
    """
    Modelo para almacenar notificaciones de recordatorios para los usuarios
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    recordatorio = models.ForeignKey(Recordatorio, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje}"