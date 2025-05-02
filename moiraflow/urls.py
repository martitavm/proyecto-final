from django.urls import path
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
    CalendarioInteractivoCirularView,
    RegistroDiarioCreateView,
    RegistroDiarioUpdateView,
    RegistroDiarioDeleteView,
    RegistroDiarioDetailView,
    CicloMenstrualCreateView,
    TratamientoHormonalCreateView,
    ListaArticulosView,
    DetalleArticuloView,
    CrearArticuloView,
    EditarArticuloView,
    EliminarArticuloView,
    MascotaPanelView,
    AlimentarMascotaView,
    VerificarEstadoMascotaView,
    ResetearEstadoMascotaView,
    ConsejoMascotaView,
)

app_name = 'moiraflow'

urlpatterns = [
    # URLs básicas y de autenticación
    path('', PaginaPrincipalView.as_view(), name='index'),
    path('accounts/login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),

    # URLs de perfil
    path('perfil/mi-perfil/', MiPerfilView.as_view(), name='mi_perfil'),
    path('perfil/editar/<int:pk>/', EditarPerfilView.as_view(), name='editar_perfil'),
    path('perfil/eliminar/<int:pk>/', EliminarPerfilView.as_view(), name='eliminar_perfil'),

    # URLs de administración
    path('admin-perfiles/', ListaPerfilesView.as_view(), name='lista_perfiles'),
    path('admin-perfiles/editar/<int:pk>/', AdminEditarPerfilView.as_view(), name='admin_editar_perfil'),
    path('admin-perfiles/eliminar/<int:pk>/', AdminEliminarPerfilView.as_view(), name='admin_eliminar_perfil'),

    # URLs de calendario
    path('calendario/', CalendarioInteractivoCirularView.as_view(), name='calendario'),
    path('calendario/tradicional/', CalendarioView.as_view(), name='calendario_tradicional'),


    # URLs de registros diarios
    path('calendario/registro/crear/', RegistroDiarioCreateView.as_view(), name='crear_registro'),
    path('calendario/registro/editar/<int:pk>/', RegistroDiarioUpdateView.as_view(), name='editar_registro'),
    path('calendario/registro/eliminar/<int:pk>/', RegistroDiarioDeleteView.as_view(), name='eliminar_registro'),
    path('calendario/registro/<int:anio>/<int:mes>/<int:dia>/', RegistroDiarioDetailView.as_view(), name='detalle_registro'),
    path('calendario/registro/dia/<int:year>/<int:month>/<int:day>/', RegistroDiarioCreateView.as_view(), name='registro_diario'),

    # URLs de ciclos y tratamientos
    path('calendario/ciclo/crear/', CicloMenstrualCreateView.as_view(), name='crear_ciclo'),
    path('calendario/tratamiento/crear/', TratamientoHormonalCreateView.as_view(), name='crear_tratamiento'),

    #URLs de articulos
    path('articulos/', ListaArticulosView.as_view(), name='lista_articulos'),
    path('articulo/crear/', CrearArticuloView.as_view(), name='crear_articulo'),
    path('articulo/<int:pk>/', DetalleArticuloView.as_view(), name='detalle_articulo'),
    path('articulo/editar/<int:pk>/', EditarArticuloView.as_view(), name='editar_articulo'),
    path('articulo/eliminar/<int:pk>/', EliminarArticuloView.as_view(), name='eliminar_articulo'),

    #URLs de mascota
    path('mascota/panel/', MascotaPanelView.as_view(), name='mascota_panel'),
    path('mascota/alimentar/', AlimentarMascotaView.as_view(), name='alimentar_mascota'),
    path('mascota/verificar-estado/', VerificarEstadoMascotaView.as_view(), name='verificar_estado_mascota'),
    path('mascota/resetear-estado/', ResetearEstadoMascotaView.as_view(), name='resetear_estado_mascota'),
    path('mascota/consejo/', ConsejoMascotaView.as_view(), name='consejo_mascota'),

]