from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from moiraflow.models import RegistroDiario, TratamientoHormonal, CicloMenstrual, Perfil, Articulo, EfectoTratamiento


class RegistroCompletoForm(UserCreationForm):
    GENERO_CHOICES = [
        ('', 'Seleccionar...'),
        ('femenino', 'Femenino'),
        ('femenino trans', 'Femenino trans'),
        ('masculino trans', 'Masculino trans'),
    ]

    # Campos de User
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text="Requerido. Ingrese un email válido."
    )

    # Campos de Perfil
    tipo_perfil = forms.ChoiceField(
        label="Tipo de Usuario",
        choices=Perfil._meta.get_field('tipo_perfil').choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='usuario'
    )

    foto_perfil = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Suba una imagen para su perfil"
    )

    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        help_text="Seleccione su fecha de nacimiento"
    )

    genero = forms.ChoiceField(
        choices=GENERO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': "togglePeriodoFields(this.value)"
        }),
        help_text="Seleccione su género"
    )

    duracion_ciclo_promedio = forms.IntegerField(
        label="Duración promedio del ciclo (días)",
        initial=28,
        min_value=21,
        max_value=45,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control periodo-field',
            'min': '21',
            'max': '45'
        }),
        help_text="Normalmente entre 21 y 30 días"
    )

    duracion_periodo_promedio = forms.IntegerField(
        required=False,
        label="Duración promedio del período (días)",
        initial=5,
        min_value=2,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control periodo-field',
            'min': '2',
            'max': '10'
        }),
        help_text="Normalmente entre 2 y 10 días"
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password1',
            'password2',
            'tipo_perfil',
            'foto_perfil',
            'fecha_nacimiento',
            'genero',
            'duracion_ciclo_promedio',
            'duracion_periodo_promedio'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicialmente ocultamos los campos si el género no corresponde
        if self.initial.get('genero') not in ['femenino', 'masculino trans']:
            self.fields['duracion_ciclo_promedio'].widget.attrs['style'] = 'display: none'
            self.fields['duracion_periodo_promedio'].widget.attrs['style'] = 'display: none'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        # Verificar si el usuario ya existe (por si acaso)
        if User.objects.filter(username=user.username).exists():
            raise forms.ValidationError("Este usuario ya existe")
        if commit:
            user.save()

            # 2. Eliminar perfil existente si hay alguno (protección contra inconsistencias)
            if hasattr(user, 'perfil'):
                user.perfil.delete()

            perfil_data = {
                'usuario': user,
                'tipo_perfil': self.cleaned_data['tipo_perfil'],
                'foto_perfil': self.cleaned_data['foto_perfil'],
                'fecha_nacimiento': self.cleaned_data['fecha_nacimiento'],
                'genero': self.cleaned_data['genero'],
            }

            # Solo incluir campos de ciclo si el género lo requiere
            genero = self.cleaned_data['genero']
            if genero in ['femenino', 'masculino trans']:
                perfil_data['duracion_ciclo_promedio'] = self.cleaned_data.get('duracion_ciclo_promedio', 28)
                perfil_data['duracion_periodo_promedio'] = self.cleaned_data.get('duracion_periodo_promedio', 5)
            else:
                # Para otros géneros, establecer explícitamente como None
                perfil_data['duracion_ciclo_promedio'] = None
                perfil_data['duracion_periodo_promedio'] = None

            Perfil.objects.create(**perfil_data)
        return user


class EditarPerfilForm(forms.ModelForm):
    GENERO_CHOICES = [
        ('', 'Seleccionar...'),
        ('femenino', 'Femenino'),
        ('femenino trans', 'Femenino trans'),
        ('masculino trans', 'Masculino trans'),
    ]

    foto_perfil = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Suba una imagen para su perfil"
    )

    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        help_text="Seleccione su fecha de nacimiento"
    )

    genero = forms.ChoiceField(
        choices=GENERO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': "togglePeriodoFields(this.value)"
        }),
        help_text="Seleccione su género"
    )

    duracion_ciclo_promedio = forms.IntegerField(
        label="Duración promedio del ciclo (días)",
        initial=28,
        min_value=21,
        max_value=45,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control periodo-field',
            'min': '21',
            'max': '45'
        }),
        help_text="Normalmente entre 21 y 30 días"
    )

    duracion_periodo_promedio = forms.IntegerField(
        required=False,
        label="Duración promedio del período (días)",
        initial=5,
        min_value=2,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control periodo-field',
            'min': '2',
            'max': '10'
        }),
        help_text="Normalmente entre 2 y 10 días"
    )

    class Meta:
        model = Perfil
        fields = [
            'foto_perfil',
            'fecha_nacimiento',
            'genero',
            'duracion_ciclo_promedio',
            'duracion_periodo_promedio'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ocultar campos de ciclo si no aplica
        if self.instance and self.instance.genero not in ['femenino', 'masculino trans']:
            self.fields['duracion_ciclo_promedio'].widget.attrs['style'] = 'display: none'
            self.fields['duracion_periodo_promedio'].widget.attrs['style'] = 'display: none'


class RegistroDiarioForm(forms.ModelForm):
    class Meta:
        model = RegistroDiario
        fields = '__all__'
        exclude = ['usuario', 'ciclo', 'tratamiento', 'fecha']
        widgets = {
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe cualquier observación adicional...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        self.fecha = kwargs.pop('fecha', None)
        self.tipo_seguimiento = kwargs.pop('tipo_seguimiento')
        self.ciclo = kwargs.pop('ciclo', None)
        self.tratamiento = kwargs.pop('tratamiento', None)

        super().__init__(*args, **kwargs)

        # Campos comunes a ambos tipos de seguimiento
        self.fields['estados_animo'] = forms.MultipleChoiceField(
            choices=RegistroDiario.EstadoAnimo.choices,
            widget=forms.CheckboxSelectMultiple(),
            required=False,
            initial=self.instance.estados_animo if self.instance else []
        )

        self.fields['sintomas_comunes'] = forms.MultipleChoiceField(
            choices=RegistroDiario.SintomasComunes.choices,
            widget=forms.CheckboxSelectMultiple(),
            required=False,
            initial=self.instance.sintomas_comunes if self.instance else []
        )

        # Eliminar todos los campos específicos primero
        campos_menstrual = [
            'es_dia_periodo', 'flujo_menstrual', 'color_flujo',
            'coagulos', 'senos_sensibles', 'retencion_liquidos',
            'antojos', 'acne'
        ]

        campos_hormonal = [
            'medicacion_tomada', 'hora_medicacion', 'efectos_tratamiento',
            'sensibilidad_pezon', 'cambios_libido', 'sofocos',
            'cambios_piel', 'crecimiento_mamario'
        ]

        for field in campos_menstrual + campos_hormonal:
            if field in self.fields:
                del self.fields[field]

        # Configurar campos según el tipo de seguimiento
        if self.tipo_seguimiento == 'ciclo_menstrual':
            self._configurar_campos_menstruales()
        elif self.tipo_seguimiento == 'tratamiento_hormonal':
            self._configurar_campos_hormonales()

    def _configurar_campos_menstruales(self):
        """Configura los campos específicos para seguimiento menstrual"""
        self.fields['es_dia_periodo'] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
        )

        self.fields['flujo_menstrual'] = forms.ChoiceField(
            choices=RegistroDiario.FlujoMenstrual.choices,
            widget=forms.RadioSelect(),
            required=False
        )

        self.fields['color_flujo'] = forms.ChoiceField(
            choices=RegistroDiario.ColorFlujo.choices,
            widget=forms.RadioSelect(),
            required=False
        )

        # Síntomas menstruales
        sintomas_menstruales = {
            'coagulos': '¿Coágulos?',
            'senos_sensibles': 'Sensibilidad en senos',
            'retencion_liquidos': 'Retención de líquidos',
            'antojos': 'Antojos',
            'acne': 'Acné'
        }

        for field_name, label in sintomas_menstruales.items():
            self.fields[field_name] = forms.BooleanField(
                required=False,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                label=label
            )

    def _configurar_campos_hormonales(self):
        """Configura los campos específicos para tratamiento hormonal"""
        self.fields['medicacion_tomada'] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            label='¿Tomaste la medicación hoy?'
        )

        self.fields['hora_medicacion'] = forms.TimeField(
            required=False,
            widget=forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            label='Hora de la medicación'
        )

        self.fields['efectos_tratamiento'] = forms.MultipleChoiceField(
            choices=EfectoTratamiento.EFECTO_CHOICES,
            widget=forms.CheckboxSelectMultiple(),
            required=False,
            label='Efectos del tratamiento'
        )

        self.fields['sensibilidad_pezon'] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            label='Sensibilidad en pezones'
        )

        self.fields['cambios_libido'] = forms.ChoiceField(
            choices=RegistroDiario.Libido.choices,
            widget=forms.RadioSelect(),
            required=False,
            label='Cambios en la libido'
        )

        self.fields['sofocos'] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            label='Sofocos'
        )

        self.fields['cambios_piel'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            label='Cambios en la piel'
        )

        self.fields['crecimiento_mamario'] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            label='Crecimiento mamario'
        )

    def clean(self):
        cleaned_data = super().clean()

        if self.tipo_seguimiento == 'ciclo_menstrual':
            if cleaned_data.get('es_dia_periodo'):
                if not cleaned_data.get('flujo_menstrual'):
                    self.add_error('flujo_menstrual', 'Este campo es requerido para días de período')
                if not cleaned_data.get('color_flujo'):
                    self.add_error('color_flujo', 'Este campo es requerido para días de período')

        elif self.tipo_seguimiento == 'tratamiento_hormonal':
            if cleaned_data.get('medicacion_tomada') and not cleaned_data.get('hora_medicacion'):
                self.add_error('hora_medicacion', 'Debe especificar la hora cuando ha tomado la medicación')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.usuario:
            instance.usuario = self.usuario
            instance.fecha = self.fecha

            # Asignar ciclo o tratamiento según corresponda
            if self.tipo_seguimiento == 'ciclo_menstrual' and self.ciclo:
                instance.ciclo = self.ciclo
            elif self.tipo_seguimiento == 'tratamiento_hormonal' and self.tratamiento:
                instance.tratamiento = self.tratamiento

        if commit:
            instance.save()
            # Guardar campos ManyToMany manualmente
            self.save_m2m = lambda: None  # Desactivar el save_m2m por defecto
            instance.estados_animo = self.cleaned_data.get('estados_animo', [])
            instance.sintomas_comunes = self.cleaned_data.get('sintomas_comunes', [])

            if self.tipo_seguimiento == 'tratamiento_hormonal':
                instance.efectos_tratamiento = self.cleaned_data.get('efectos_tratamiento', [])

            instance.save()

        return instance

class TratamientoHormonalForm(forms.ModelForm):
    TIPO_HORMONA_CHOICES = [
        ('estrogeno', 'Estógeno'),
        ('progesterona', 'Progesterona'),
        ('testosterona', 'Testosterona'),
        ('combinado', 'Combinado')
    ]

    tipo_hormona = forms.ChoiceField(
        choices=TIPO_HORMONA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = TratamientoHormonal
        fields = ['nombre_tratamiento', 'tipo_hormona', 'fecha_inicio',
                  'fecha_fin', 'dosis', 'frecuencia', 'frecuencia_tipo', 'activo', 'notas']
        widgets = {
            'nombre_tratamiento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Estradiol valerato 2mg'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Opcional para tratamientos temporales'
            }),
            'dosis': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'frecuencia': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'frecuencia_tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notas': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Efectos secundarios, observaciones...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.usuario:
            instance.usuario = self.usuario
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_fin and fecha_inicio and fecha_fin < fecha_inicio:
            raise ValidationError(
                "La fecha de fin no puede ser anterior a la fecha de inicio"
            )

        return cleaned_data


class CicloMenstrualForm(forms.ModelForm):
    class Meta:
        model = CicloMenstrual
        fields = ['fecha_inicio', 'fecha_fin', 'notas', 'sintomas_importantes']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'fecha_inicio'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'fecha_fin'
            }),
            'notas': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Observaciones sobre este ciclo...'
            }),
            'sintomas_importantes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Describe los síntomas importantes'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)

        # Establecer fecha_fin inicial basada en duración promedio
        if self.usuario and hasattr(self.usuario, 'perfil'):
            perfil = self.usuario.perfil
            if perfil.duracion_ciclo_promedio and 'fecha_inicio' in self.initial:
                fecha_inicio = self.initial['fecha_inicio']
                if isinstance(fecha_inicio, str):
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin = fecha_inicio + timedelta(days=perfil.duracion_ciclo_promedio - 1)
                self.initial['fecha_fin'] = fecha_fin

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.usuario:
            instance.usuario = self.usuario
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_fin and fecha_inicio and fecha_fin < fecha_inicio:
            raise ValidationError(
                "La fecha de fin no puede ser anterior a la fecha de inicio"
            )

        # Validar solapamiento con otros ciclos
        if self.usuario and fecha_inicio and fecha_fin:
            ciclos_solapados = CicloMenstrual.objects.filter(
                usuario=self.usuario,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio
            ).exclude(pk=self.instance.pk if self.instance else None)

            if ciclos_solapados.exists():
                raise ValidationError(
                    "Este ciclo se solapa con otro ciclo existente. "
                    "Por favor, ajusta las fechas."
                )

        return cleaned_data


class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulo
        fields = ['titulo', 'contenido', 'imagen_portada', 'estado', 'categoria', 'destacado']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe un título atractivo'
            }),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control editor-texto',
                'rows': 10
            }),
            'imagen_portada': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'destacado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'destacado': 'Marcar como artículo destacado'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contenido'].widget.attrs.update({'class': 'form-control editor-texto'})

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo']
        if len(titulo) < 10:
            raise forms.ValidationError("El título debe tener al menos 10 caracteres")
        return titulo