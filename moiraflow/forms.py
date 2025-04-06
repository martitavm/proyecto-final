from django import forms
from .models import Perfil


class PerfilForm(forms.ModelForm):
    nombre_perfil = forms.CharField(
        label="Nombre de Perfil",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=50,
        required=True
    )

    tipo_perfil = forms.ChoiceField(
        label="Tipo de Usuario",
        choices=Perfil.TIPO_PERFIL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='usuario'
    )

    class Meta:
        model = Perfil
        fields = ['nombre_perfil', 'tipo_perfil', 'foto_perfil', 'fecha_nacimiento', 'genero',
                  'duracion_ciclo_promedio', 'duracion_periodo_promedio']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'genero': forms.TextInput(attrs={'class': 'form-control'}),
            'duracion_ciclo_promedio': forms.NumberInput(attrs={'class': 'form-control'}),
            'duracion_periodo_promedio': forms.NumberInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.creating = kwargs.pop('creating', False)
        super().__init__(*args, **kwargs)

        # Lógica mejorada para el campo tipo_perfil
        if not self.creating and self.instance.pk:
            # Si estamos editando un perfil existente
            if not (self.user and hasattr(self.user, 'perfil') and self.user.perfil.es_administrador):
                self.fields['tipo_perfil'].disabled = True
                self.fields['tipo_perfil'].help_text = "Solo los administradores pueden modificar este campo"
                # Mantener el valor actual aunque el campo esté deshabilitado
                self.initial['tipo_perfil'] = self.instance.tipo_perfil