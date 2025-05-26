from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView
from django.urls import path
from rest_framework.routers import DefaultRouter

from moiraflow.views import (
    PaginaPrincipalView,
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
    TratamientoHormonalCreateView,
    ListaArticulosView,
    DetalleArticuloView,
    CrearArticuloView,
    EditarArticuloView,
    EliminarArticuloView,
    alimentar_mascota,
    consejo_mascota,
    MascotaPanelView,
    finalizar_alimentacion, RegistrosDiaView, SintomasViewSet, ajax_login,
    ajax_logout, ListaRecordatoriosView, CrearRecordatorioView,
    EditarRecordatorioView, EliminarRecordatorioView, AdminDashboardView,
)

app_name = 'moiraflow'

urlpatterns = [
    # URLs básicas y de autenticación
    path('', PaginaPrincipalView.as_view(), name='index'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('ajax/login/', ajax_login, name='ajax_login'),
    path('ajax/logout/', ajax_logout, name='ajax_logout'),

    #URLs de mailpit
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # URLs de perfil
    path('perfil/mi-perfil/', MiPerfilView.as_view(), name='mi_perfil'),
    path('perfil/editar/<int:pk>/', EditarPerfilView.as_view(), name='editar_perfil'),
    path('perfil/eliminar/<int:pk>/', EliminarPerfilView.as_view(), name='eliminar_perfil'),

    # URLs de administración
    path('admin-perfiles/', ListaPerfilesView.as_view(), name='lista_perfiles'),
    path('admin-perfiles/editar/<int:pk>/', AdminEditarPerfilView.as_view(), name='admin_editar_perfil'),
    path('admin-perfiles/eliminar/<int:pk>/', AdminEliminarPerfilView.as_view(), name='admin_eliminar_perfil'),

    # URLs de calendario
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    path('calendario/<int:year>/<int:month>/', CalendarioView.as_view(), name='calendario_mes'),

    # URLs de registros diarios
    # Registros por día
    path('registros/<int:year>/<int:month>/<int:day>/', RegistrosDiaView.as_view(), name='registros_dia'),

    # CRUD Registros
    path('registro/crear/<int:year>/<int:month>/<int:day>/', RegistroDiarioCreateView.as_view(), name='crear_registro'),
    path('registro/editar/<int:pk>/', RegistroDiarioUpdateView.as_view(), name='editar_registro'),
    path('registro/eliminar/<int:pk>/', RegistroDiarioDeleteView.as_view(), name='eliminar_registro'),

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
    path('mascota/', MascotaPanelView.as_view(), name='mascota_panel'),
    path('mascota/alimentar/', alimentar_mascota, name='alimentar_mascota'),
    path('mascota/finalizar-alimentacion/', finalizar_alimentacion, name='finalizar_alimentacion'),
    path('mascota/consejo/', consejo_mascota, name='consejo_mascota'),


    #URLs de notificaciones

    path('recordatorios/', ListaRecordatoriosView.as_view(), name='lista_recordatorios'),
    path('recordatorios/crear/', CrearRecordatorioView.as_view(), name='crear_recordatorio'),
    path('recordatorios/editar/<int:pk>/', EditarRecordatorioView.as_view(), name='editar_recordatorio'),
    path('recordatorios/eliminar/<int:pk>/', EliminarRecordatorioView.as_view(), name='eliminar_recordatorio'),

    #URLs de Panel estadísticas admin
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),

]