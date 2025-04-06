from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, AccessMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Perfil
from .forms import PerfilForm


class PaginaPrincipalView(TemplateView):
    template_name = 'moiraflow/index.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('moiraflow:login')

        # Verificar perfil aquí en lugar de en get_context_data
        if hasattr(request.user, 'perfil'):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.info(request, 'Por favor completa tu perfil primero')
            return redirect('moiraflow:crear_perfil')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ahora podemos asumir que el usuario está autenticado y tiene perfil
        context['perfil'] = self.request.user.perfil
        return context

class LoginUserView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()

        # Verifica si el usuario tiene perfil
        if not hasattr(user, 'perfil'):
            messages.info(self.request, 'Por favor completa tu perfil')
            return redirect('moiraflow:crear_perfil')

        messages.success(self.request, f'¡Bienvenid@ {user.username}!')
        return response

    def get_success_url(self):
        if not hasattr(self.request.user, 'perfil'):
            return reverse_lazy('moiraflow:crear_perfil')
        return reverse_lazy('moiraflow:index')


class LogoutUserView(TemplateView):
    template_name = 'registration/logged_out.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, 'Has cerrado sesión correctamente.')
        return super().dispatch(request, *args, **kwargs)


class CrearPerfilView(CreateView):
    template_name = "moiraflow/crear_perfil.html"
    form_class = PerfilForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['creating'] = True  # Indicamos que es creación
        return kwargs

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, '¡Perfil creado exitosamente!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('moiraflow:mi_perfil')


class EditarPerfilView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "moiraflow/editar_perfil.html"
    form_class = PerfilForm
    model = Perfil

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['creating'] = False  # No es creación
        return kwargs

    def test_func(self):
        perfil = self.get_object()
        return (self.request.user == perfil.usuario) or (self.request.user.perfil.es_administrador)

    def get_success_url(self):
        return reverse_lazy('moiraflow:mi_perfil')


class EliminarPerfilView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    template_name = "moiraflow/eliminar_perfil.html"
    model = Perfil
    success_url = reverse_lazy('moiraflow:index')  # Cambiado a 'index' que es tu URL principal

    def test_func(self):
        perfil = self.get_object()
        # Solo el dueño del perfil o un administrador puede eliminar
        return (self.request.user == perfil.usuario) or (self.request.user.perfil.es_administrador)

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para eliminar este perfil")
        return redirect('moiraflow:index')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Perfil eliminado correctamente")
        return super().delete(request, *args, **kwargs)


class MiPerfilView(LoginRequiredMixin, DetailView):
    template_name = "moiraflow/mi_perfil.html"
    model = Perfil

    def get_object(self):
        return get_object_or_404(Perfil, usuario=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'perfil'):
            messages.info(request, 'Por favor crea tu perfil primero')
            return redirect('moiraflow:crear_perfil')
        return super().dispatch(request, *args, **kwargs)