from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    Perfil,
    CicloMenstrual,
    RegistroDiario,
    Sintoma,
    RegistroSintoma,
    Recordatorio,
    NivelHormonal
)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'genero', 'duracion_ciclo_promedio', 'fecha_creacion')
    search_fields = ('usuario__username', 'genero')

@admin.register(CicloMenstrual)
class CicloMenstrualAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_inicio', 'fecha_fin', 'duracion')
    list_filter = ('usuario',)
    search_fields = ('usuario__username', 'notas')
    date_hierarchy = 'fecha_inicio'

@admin.register(RegistroDiario)
class RegistroDiarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'es_dia_periodo', 'flujo_menstrual', 'dolor')
    list_filter = ('es_dia_periodo', 'flujo_menstrual', 'usuario')
    search_fields = ('usuario__username', 'notas')
    date_hierarchy = 'fecha'

@admin.register(Sintoma)
class SintomaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

@admin.register(RegistroSintoma)
class RegistroSintomaAdmin(admin.ModelAdmin):
    list_display = ('sintoma', 'registro_diario', 'intensidad')
    list_filter = ('sintoma', 'intensidad')
    search_fields = ('sintoma__nombre', 'registro_diario__usuario__username')

@admin.register(Recordatorio)
class RecordatorioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'tipo', 'fecha_inicio', 'frecuencia', 'activo')
    list_filter = ('tipo', 'frecuencia', 'activo')
    search_fields = ('titulo', 'descripcion', 'usuario__username')
    date_hierarchy = 'fecha_inicio'

@admin.register(NivelHormonal)
class NivelHormonalAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_hormona', 'valor', 'unidad', 'fecha')
    list_filter = ('tipo_hormona',)
    search_fields = ('usuario__username', 'tipo_hormona', 'nombre_personalizado')
    date_hierarchy = 'fecha'
