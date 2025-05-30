"""
URL configuration for proyecto_control_menstrual_hormonal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from moiraflow.views import SintomasViewSet, EstadisticasViewSet, EstadisticasGeneroViewSet, \
    EstadisticasSintomasViewSet, EstadisticasSeguimientoViewSet, EstadisticasEdadesViewSet

router = DefaultRouter()
router.register(r'sintomas', SintomasViewSet, basename='sintomas')
router.register(r'estadisticas', EstadisticasViewSet, basename='estadisticas')
router.register(r'estadisticas/genero', EstadisticasGeneroViewSet, basename='estadisticas-genero')
router.register(r'estadisticas/sintomas', EstadisticasSintomasViewSet, basename='estadisticas-sintomas')
router.register(r'estadisticas/edades', EstadisticasEdadesViewSet, basename='estadisticas-edades')
router.register(r'estadisticas/seguimiento', EstadisticasSeguimientoViewSet, basename='estadisticas-seguimiento')

urlpatterns = [
    path("moiraflow/", include("moiraflow.urls")),
    path("admin/", admin.site.urls),

    path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
