
# Register your models here.
from django.contrib import admin

from moiraflow.models import Perfil, Articulo, EfectoTratamiento, Mascota, TratamientoHormonal, CicloMenstrual, Recordatorio, EstadisticaUsuario, RegistroDiario

admin.site.register(Perfil)
admin.site.register(Articulo)
admin.site.register(EfectoTratamiento)
admin.site.register(Mascota)
admin.site.register(RegistroDiario)
admin.site.register(TratamientoHormonal)
admin.site.register(CicloMenstrual)
admin.site.register(Recordatorio)
admin.site.register(EstadisticaUsuario)
