from django.urls import path
from django.contrib.auth.decorators import login_required
from moiraflow.views import (PaginaPrincipalView, LoginUserView, LogoutUserView, CrearPerfilView, EditarPerfilView, MiPerfilView, EliminarPerfilView)

app_name = 'moiraflow'

urlpatterns = [
    path('', PaginaPrincipalView.as_view(), name='index'),
    path('accounts/login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
    path('perfil/crear/', CrearPerfilView.as_view(), name='crear_perfil'),
    path('perfil/editar/<int:pk>/', login_required(EditarPerfilView.as_view()), name='editar_perfil'),
    path('perfil/mi-perfil/', login_required(MiPerfilView.as_view()), name='mi_perfil'),
    path('perfil/eliminar/<int:pk>/', login_required(EliminarPerfilView.as_view()), name='eliminar_perfil'),
]