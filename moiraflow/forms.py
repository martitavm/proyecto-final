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

            # Solo guardamos los datos del ciclo si el género es femenino o masculino trans
            if self.cleaned_data['genero'] in ['femenino', 'masculino trans']:
                perfil_data['duracion_ciclo_promedio'] = self.cleaned_data['duracion_ciclo_promedio']
                perfil_data['duracion_periodo_promedio'] = self.cleaned_data['duracion_periodo_promedio']
            else:
                perfil_data['duracion_ciclo_promedio'] = None
                perfil_data['duracion_periodo_promedio'] = None

            Perfil.objects.create(**perfil_data)
        return user


class RegistroDiarioForm(forms.ModelForm):
    class Meta:
        model = RegistroDiario
        fields = '__all__'
        exclude = ['usuario', 'ciclo', 'tratamiento', 'fecha']
        widgets = {
            'hora_medicacion': forms.TimeInput(
                attrs={'type': 'time', 'class': 'form-control'},
                format='%H:%M'
            ),
            'estados_animo': forms.SelectMultiple(
                attrs={'class': 'form-control select2-multiple'},
                choices=RegistroDiario.ESTADO_ANIMO_CHOICES
            ),
            'dolor_cabeza': forms.NumberInput(
                attrs={'min': '0', 'max': '10', 'class': 'form-control'}
            ),
            'dolor_espalda': forms.NumberInput(
                attrs={'min': '0', 'max': '10', 'class': 'form-control'}
            ),
            'fatiga': forms.NumberInput(
                attrs={'min': '0', 'max': '10', 'class': 'form-control'}
            ),
            'notas': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
            'otros_sintomas': forms.Textarea(
                attrs={'rows': 2, 'class': 'form-control'}
            ),
            'cambios_piel': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        tipo_seguimiento = kwargs.pop('tipo_seguimiento', 'ninguno')
        super().__init__(*args, **kwargs)

        # Campos comunes para todos
        campos_comunes = [
            'dolor_cabeza', 'dolor_espalda', 'fatiga',
            'estados_animo', 'cambios_apetito', 'insomnio',
            'medicamentos', 'notas', 'otros_sintomas'
        ]

        # Ocultar campos no relevantes según el tipo de seguimiento
        for field_name in list(self.fields.keys()):
            if field_name not in campos_comunes:
                if tipo_seguimiento == 'ciclo_menstrual' and field_name not in [
                    'es_dia_periodo', 'flujo_menstrual', 'coagulos',
                    'color_flujo', 'senos_sensibles', 'retencion_liquidos',
                    'antojos', 'acné'
                ]:
                    self.fields[field_name].widget = forms.HiddenInput()
                    self.fields[field_name].required = False

                elif tipo_seguimiento == 'tratamiento_hormonal' and field_name not in [
                    'medicacion_tomada', 'hora_medicacion',
                    'sensibilidad_pezon', 'cambios_libido',
                    'sofocos', 'cambios_piel', 'crecimiento_mamario'
                ]:
                    self.fields[field_name].widget = forms.HiddenInput()
                    self.fields[field_name].required = False

                elif tipo_seguimiento == 'ninguno':
                    if field_name not in campos_comunes:
                        self.fields[field_name].widget = forms.HiddenInput()
                        self.fields[field_name].required = False

        # Mejorar la presentación de campos booleanos
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs['class'] = 'form-check-input'

        # Agrupar campos para mejor presentación
        self.fields['estados_animo'].choices = RegistroDiario.ESTADO_ANIMO_CHOICES
        self.fields['flujo_menstrual'].choices = RegistroDiario.FLUJO_CHOICES
        self.fields['color_flujo'].choices = RegistroDiario.COLOR_FLUJO_CHOICES
        self.fields['cambios_libido'].choices = RegistroDiario.LIBIDO_CHOICES


class TratamientoHormonalForm(forms.ModelForm):
    class Meta:
        model = TratamientoHormonal
        fields = ['nombre_tratamiento', 'fecha_inicio', 'fecha_fin',
                  'dosis', 'frecuencia', 'activo', 'notas']
        widgets = {
            'nombre_tratamiento': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'fecha_inicio': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'fecha_fin': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'dosis': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'frecuencia': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'activo': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'notas': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_fin and fecha_inicio and fecha_fin < fecha_inicio:
            raise ValidationError(
                "La fecha de fin no puede ser anterior a la fecha de inicio"
            )


class CicloMenstrualForm(forms.ModelForm):
    class Meta:
        model = CicloMenstrual
        fields = ['fecha_inicio', 'fecha_fin', 'notas']
        widgets = {
            'fecha_inicio': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'fecha_fin': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'notas': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_fin and fecha_inicio and fecha_fin < fecha_inicio:
            raise ValidationError(
                "La fecha de fin no puede ser anterior a la fecha de inicio"
            )

from django import forms
from .models import Articulo

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