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
    AdminEliminarPerfilView
)

app_name = 'moiraflow'

urlpatterns = [
    path('', PaginaPrincipalView.as_view(), name='index'),
    path('accounts/login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('perfil/mi-perfil/', login_required(MiPerfilView.as_view()), name='mi_perfil'),
    path('perfil/editar/<int:pk>/', login_required(EditarPerfilView.as_view()), name='editar_perfil'),
    path('perfil/eliminar/<int:pk>/', login_required(EliminarPerfilView.as_view()), name='eliminar_perfil'),
    path('admin-perfiles/', login_required(ListaPerfilesView.as_view()), name='lista_perfiles'),
    path('admin-perfiles/editar/<int:pk>/', login_required(AdminEditarPerfilView.as_view()), name='admin_editar_perfil'),
    path('admin-perfiles/eliminar/<int:pk>/', login_required(AdminEliminarPerfilView.as_view()), name='admin_eliminar_perfil'),
]