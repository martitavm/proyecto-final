from django.urls import path

from . import views

app_name = 'moiraflow'

urlpatterns = [
    path("", views.index, name="index"),
]