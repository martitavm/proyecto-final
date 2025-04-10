from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from moiraflow.models import RegistroDiario, TratamientoHormonal, CicloMenstrual, Perfil


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


# Formulario para registros diarios
class RegistroDiarioForm(forms.ModelForm):
    class Meta:
        model = RegistroDiario
        fields = ['es_dia_periodo', 'flujo_menstrual', 'medicacion_tomada',
                  'hora_medicacion', 'estados_animo', 'dolor',
                  'medicamentos', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_medicacion': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'estados_animo': forms.TextInput(
                attrs={'placeholder': 'Ej: feliz, cansada, irritable', 'class': 'form-control'}),
            'dolor': forms.NumberInput(attrs={'min': '0', 'max': '10', 'class': 'form-control'}),
            'medicamentos': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        tipo_seguimiento = kwargs.pop('tipo_seguimiento', 'ninguno')
        super(RegistroDiarioForm, self).__init__(*args, **kwargs)

        # Modificar el formulario según el tipo de seguimiento
        if tipo_seguimiento == 'ciclo_menstrual':
            self.fields.pop('medicacion_tomada', None)
            self.fields.pop('hora_medicacion', None)
        elif tipo_seguimiento == 'tratamiento_hormonal':
            self.fields.pop('es_dia_periodo', None)
            self.fields.pop('flujo_menstrual', None)
        elif tipo_seguimiento == 'ninguno':
            self.fields.pop('es_dia_periodo', None)
            self.fields.pop('flujo_menstrual', None)
            self.fields.pop('medicacion_tomada', None)
            self.fields.pop('hora_medicacion', None)


class TratamientoHormonalForm(forms.ModelForm):
    class Meta:
        model = TratamientoHormonal
        fields = ['nombre_tratamiento', 'fecha_inicio', 'fecha_fin',
                  'dosis', 'frecuencia', 'notas']
        widgets = {
            'nombre_tratamiento': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'dosis': forms.TextInput(attrs={'class': 'form-control'}),
            'frecuencia': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class CicloMenstrualForm(forms.ModelForm):
    class Meta:
        model = CicloMenstrual
        fields = ['fecha_inicio', 'fecha_fin', 'notas']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }