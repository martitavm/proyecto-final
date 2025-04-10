from django.urls import path
from django.contrib.auth.decorators import login_required
from moiraflow.views import (
    PaginaPrincipalView,
    LoginUserView,
    LogoutUserView,
    RegistroUsuarioView,
    EditarPerfilView,
    MiPerfilView,
    EliminarPerfilView,
    ListaPerfilesView,
    AdminEditarPerfilView,
    AdminEliminarPerfilView,
    CalendarioView,
    RegistroDiarioCreateView,
    RegistroDiarioUpdateView,
    RegistroDiarioDeleteView,
    RegistroDiarioDetailView,
    CicloMenstrualCreateView,
    TratamientoHormonalCreateView
)

app_name = 'moiraflow'

urlpatterns = [
    path('', PaginaPrincipalView.as_view(), name='index'),
    path('accounts/login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('perfil/mi-perfil/', MiPerfilView.as_view(), name='mi_perfil'),
    path('perfil/editar/<int:pk>/', EditarPerfilView.as_view(), name='editar_perfil'),
    path('perfil/eliminar/<int:pk>/', EliminarPerfilView.as_view(), name='eliminar_perfil'),
    path('admin-perfiles/', ListaPerfilesView.as_view(), name='lista_perfiles'),
    path('admin-perfiles/editar/<int:pk>/', AdminEditarPerfilView.as_view(), name='admin_editar_perfil'),
    path('admin-perfiles/eliminar/<int:pk>/', AdminEliminarPerfilView.as_view(), name='admin_eliminar_perfil'),
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    path('calendario/registro/crear/', RegistroDiarioCreateView.as_view(), name='crear_registro'),
    path('calendario/registro/editar/<int:pk>/', RegistroDiarioUpdateView.as_view(), name='editar_registro'),
    path('calendario/registro/eliminar/<int:pk>/', RegistroDiarioDeleteView.as_view(), name='eliminar_registro'),
    path('calendario/registro/<int:anio>/<int:mes>/<int:dia>/', RegistroDiarioDetailView.as_view(), name='detalle_registro'),
    path('calendario/ciclo/crear/', CicloMenstrualCreateView.as_view(), name='crear_ciclo'),
    path('calendario/tratamiento/crear/', TratamientoHormonalCreateView.as_view(), name='crear_tratamiento'),
]