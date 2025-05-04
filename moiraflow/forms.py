from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from moiraflow.models import RegistroDiario, TratamientoHormonal, CicloMenstrual, Perfil, Articulo

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
        if commit:
            user.save()

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
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=True
    )

    class Meta:
        model = RegistroDiario
        fields = '__all__'
        exclude = ['usuario', 'ciclo', 'tratamiento']  # Quitamos 'fecha' del exclude
        widgets = {
            'hora_medicacion': forms.TimeInput(
                attrs={'type': 'time', 'class': 'form-control'},
                format='%H:%M'
            ),
            # ... mantén tus otros widgets ...
        }

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        tipo_seguimiento = kwargs.pop('tipo_seguimiento', 'ninguno')
        fecha = kwargs.pop('fecha', None)

        super().__init__(*args, **kwargs)

        # Establecer fecha inicial si se proporciona
        if fecha:
            self.fields['fecha'].initial = fecha

        # Determinar tipo de registro basado en perfil de usuario
        if self.usuario and hasattr(self.usuario, 'perfil'):
            perfil = self.usuario.perfil
            if perfil.genero in ['femenino', 'masculino trans']:
                tipo_seguimiento = 'ciclo_menstrual'
            elif perfil.genero == 'femenino trans':
                tipo_seguimiento = 'tratamiento_hormonal'

        # Configurar campos según tipo de seguimiento
        campos_por_tipo = {
            'ciclo_menstrual': [
                'es_dia_periodo', 'flujo_menstrual', 'coagulos',
                'color_flujo', 'senos_sensibles', 'retencion_liquidos',
                'antojos', 'acné', 'dolor_cabeza', 'dolor_espalda',
                'fatiga', 'estados_animo', 'cambios_apetito', 'insomnio',
                'medicamentos', 'notas', 'otros_sintomas'
            ],
            'tratamiento_hormonal': [
                'medicacion_tomada', 'hora_medicacion',
                'sensibilidad_pezon', 'cambios_libido',
                'sofocos', 'cambios_piel', 'crecimiento_mamario',
                'dolor_cabeza', 'fatiga', 'estados_animo',
                'notas', 'otros_sintomas'
            ],
            'ninguno': [
                'dolor_cabeza', 'dolor_espalda', 'fatiga',
                'estados_animo', 'cambios_apetito', 'insomnio',
                'medicamentos', 'notas', 'otros_sintomas'
            ]
        }

        # Ocultar campos no relevantes
        campos_visibles = campos_por_tipo.get(tipo_seguimiento, [])
        for field_name in list(self.fields.keys()):
            if field_name not in campos_visibles:
                self.fields[field_name].widget = forms.HiddenInput()
                self.fields[field_name].required = False

        # Configurar choices dinámicos
        self.fields['estados_animo'].choices = RegistroDiario.ESTADO_ANIMO_CHOICES
        self.fields['flujo_menstrual'].choices = RegistroDiario.FLUJO_CHOICES
        self.fields['color_flujo'].choices = RegistroDiario.COLOR_FLUJO_CHOICES
        self.fields['cambios_libido'].choices = RegistroDiario.LIBIDO_CHOICES

        # Configurar campos booleanos
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs['class'] = 'form-check-input'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.usuario:
            instance.usuario = self.usuario

            # Relacionar con ciclo menstrual si aplica
            if self.usuario.perfil.genero in ['femenino', 'masculino trans']:
                ciclo_actual = CicloMenstrual.objects.filter(
                    usuario=self.usuario,
                    fecha_inicio__lte=instance.fecha,
                    fecha_fin__gte=instance.fecha
                ).first()
                if ciclo_actual:
                    instance.ciclo = ciclo_actual

            # Relacionar con tratamiento hormonal si aplica
            if self.usuario.perfil.genero == 'femenino trans':
                tratamiento_actual = TratamientoHormonal.objects.filter(
                    usuario=self.usuario,
                    activo=True
                ).first()
                if tratamiento_actual:
                    instance.tratamiento = tratamiento_actual

        if commit:
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
                  'fecha_fin', 'dosis', 'frecuencia', 'activo', 'notas']
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
            'dosis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2mg por día'
            }),
            'frecuencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cada 12 horas'
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
            'sintomas_importantes': forms.SelectMultiple(attrs={
                'class': 'form-control select2-multiple',
                'choices': RegistroDiario.SINTOMAS_CHOICES
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