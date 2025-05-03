from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, login
from moiraflow.models import Perfil, RegistroDiario, TratamientoHormonal, CicloMenstrual, Articulo, Mascota
from moiraflow.forms import RegistroCompletoForm, RegistroDiarioForm, TratamientoHormonalForm, CicloMenstrualForm, ArticuloForm
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, FormView, View, DetailView, ListView
from django.shortcuts import redirect
from django.contrib import messages
import calendar
from datetime import datetime, date, timedelta
from django.urls import reverse_lazy
from django.views.generic import View
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import render
from .models import Mascota

class PaginaPrincipalView(LoginRequiredMixin, TemplateView):
    template_name = 'moiraflow/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['perfil'] = self.request.user.perfil
        return context


class LoginUserView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        return reverse_lazy('moiraflow:index')


class RegistroUsuarioView(CreateView):
    template_name = 'moiraflow/registro.html'
    form_class = RegistroCompletoForm
    success_url = reverse_lazy('moiraflow:index')

    def form_valid(self, form):
        # Guardamos el usuario primero
        user = form.save()

        # Autenticamos al usuario automáticamente
        login(self.request, user)

        # Mostramos mensaje de éxito
        messages.success(self.request, '¡Registro completado con éxito! Bienvenid@ a MoiraFlow')

        # Redirigimos a la página principal
        return redirect(self.success_url)

    def form_invalid(self, form):
        """Maneja los errores del formulario"""
        messages.error(self.request, 'Por favor corrige los errores en el formulario')
        return super().form_invalid(form)


class LogoutUserView(TemplateView):
    template_name = 'registration/logged_out.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, 'Sesión cerrada correctamente.')
        return super().dispatch(request, *args, **kwargs)


class EditarPerfilView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "moiraflow/editar_perfil.html"
    model = Perfil
    fields = ['foto_perfil', 'fecha_nacimiento', 'genero',
              'duracion_ciclo_promedio', 'duracion_periodo_promedio', 'tipo_perfil']
    success_url = reverse_lazy('moiraflow:mi_perfil')

    def test_func(self):
        perfil = self.get_object()
        user = self.request.user
        # Permite edición si: es el dueño del perfil O es administrador
        return user == perfil.usuario or (hasattr(user, 'perfil') and user.perfil.es_administrador)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        perfil = self.get_object()

        # Si no es administrador, deshabilita el campo tipo_perfil
        if not (hasattr(user, 'perfil') and user.perfil.es_administrador):
            form.fields['tipo_perfil'].disabled = True
            form.fields['tipo_perfil'].help_text = "Solo los administradores pueden modificar este campo"

        return form


class EliminarPerfilView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    template_name = "moiraflow/eliminar_perfil.html"
    model = Perfil
    success_url = reverse_lazy('moiraflow:index')

    def test_func(self):
        perfil = self.get_object()
        user = self.request.user
        # Permite eliminar si: es el dueño del perfil O es administrador
        return user == perfil.usuario or (hasattr(user, 'perfil') and user.perfil.es_administrador)

    def delete(self, request, *args, **kwargs):
        perfil = self.get_object()
        usuario = perfil.usuario
        es_autoeliminacion = request.user == usuario

        messages.success(request, f'¡Perfil de {usuario.username} eliminado permanentemente!')
        usuario.delete()  # Elimina el usuario (y el perfil en cascada)

        if es_autoeliminacion:
            logout(request)
            return redirect(self.success_url)
        return super().delete(request, *args, **kwargs)


class MiPerfilView(LoginRequiredMixin, DetailView):
    template_name = "moiraflow/mi_perfil.html"
    model = Perfil

    def get_object(self):
        return self.request.user.perfil

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mostrar_datos_ciclo'] = self.object.genero in ['femenino', 'masculino trans']
        return context

class ListaPerfilesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'moiraflow/lista_perfiles.html'
    model = Perfil
    context_object_name = 'perfiles'

    def test_func(self):
        return self.request.user.perfil.es_administrador

class AdminEditarPerfilView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'moiraflow/admin_editar_perfil.html'
    model = Perfil
    fields = '__all__'
    success_url = reverse_lazy('moiraflow:lista_perfiles')

    def test_func(self):
        return self.request.user.perfil.es_administrador

class AdminEliminarPerfilView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    template_name = 'moiraflow/admin_eliminar_perfil.html'
    model = Perfil
    success_url = reverse_lazy('moiraflow:lista_perfiles')

    def test_func(self):
        return self.request.user.perfil.es_administrador


class CalendarioView(LoginRequiredMixin, TemplateView):
    """
    Vista principal del calendario interactivo para seguimiento menstrual y hormonal
    """
    template_name = 'moiraflow/calendario_interactivo_circular.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            perfil = self.request.user.perfil
        except:
            # Si el usuario no tiene perfil, redirigir a completar perfil
            messages.warning(self.request, "Por favor completa tu perfil primero")
            return context

        # Obtener año y mes actuales o del parámetro
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))

        # Crear calendario del mes
        cal = calendar.monthcalendar(year, month)

        # Obtener nombre del mes y días de la semana
        month_name = calendar.month_name[month]
        weekdays = [day for day in calendar.day_name]

        # Obtener registros del mes actual
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        # Obtener el ciclo menstrual actual si existe
        ciclo_actual = None
        if perfil.tipo_seguimiento in ['ciclo_menstrual', 'ambos']:
            ciclos = CicloMenstrual.objects.filter(
                usuario=self.request.user,
                fecha_inicio__lte=last_day
            ).order_by('-fecha_inicio')

            if ciclos.exists():
                ciclo_actual = ciclos.first()

        # Obtener tratamiento hormonal activo si existe
        tratamiento_activo = None
        if perfil.tipo_seguimiento in ['tratamiento_hormonal', 'ambos']:
            tratamientos = TratamientoHormonal.objects.filter(
                usuario=self.request.user,
                activo=True
            ).order_by('-fecha_inicio')

            if tratamientos.exists():
                tratamiento_activo = tratamientos.first()

        # Obtener registros diarios del mes
        registros = RegistroDiario.objects.filter(
            usuario=self.request.user,
            fecha__gte=first_day,
            fecha__lte=last_day
        )

        # Crear diccionario de registros por día
        registros_por_dia = {}
        for registro in registros:
            registros_por_dia[registro.fecha.day] = {
                'id': registro.id,
                'es_dia_periodo': registro.es_dia_periodo,
                'flujo_menstrual': registro.flujo_menstrual,
                'medicacion_tomada': registro.medicacion_tomada,
                'estados_animo': registro.estados_animo,
                'dolor': registro.dolor
            }

        # Crear formularios
        registro_form = RegistroDiarioForm(tipo_seguimiento=perfil.tipo_seguimiento)
        ciclo_form = CicloMenstrualForm()
        tratamiento_form = TratamientoHormonalForm()

        # Calcular mes anterior y siguiente
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        context.update({
            'year': year,
            'month': month,
            'month_name': month_name,
            'cal': cal,
            'weekdays': weekdays,
            'perfil': perfil,
            'registros_por_dia': registros_por_dia,
            'registro_form': registro_form,
            'ciclo_form': ciclo_form,
            'tratamiento_form': tratamiento_form,
            'ciclo_actual': ciclo_actual,
            'tratamiento_activo': tratamiento_activo,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
        })

        return context


class RegistroDiarioCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un nuevo registro diario
    """
    model = RegistroDiario
    form_class = RegistroDiarioForm
    success_url = reverse_lazy('moiraflow:calendario')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tipo_seguimiento'] = self.request.user.perfil.tipo_seguimiento
        return kwargs

    def form_valid(self, form):
        fecha_str = self.request.POST.get('fecha')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # Verificar si ya existe un registro para esta fecha
        registro_existente = RegistroDiario.objects.filter(
            usuario=self.request.user,
            fecha=fecha
        ).first()

        if registro_existente:
            messages.warning(self.request, f"Ya existe un registro para el {fecha}. Por favor edítelo.")
            return redirect(self.success_url)

        nuevo_registro = form.save(commit=False)
        nuevo_registro.usuario = self.request.user
        nuevo_registro.fecha = fecha

        # Asignar ciclo o tratamiento si corresponde
        perfil = self.request.user.perfil

        if perfil.tipo_seguimiento in ['ciclo_menstrual', 'ambos']:
            ciclo_actual = CicloMenstrual.objects.filter(
                usuario=self.request.user,
                fecha_inicio__lte=fecha
            ).order_by('-fecha_inicio').first()

            if ciclo_actual and (not ciclo_actual.fecha_fin or fecha <= ciclo_actual.fecha_fin):
                nuevo_registro.ciclo = ciclo_actual

        if perfil.tipo_seguimiento in ['tratamiento_hormonal', 'ambos']:
            tratamiento_activo = TratamientoHormonal.objects.filter(
                usuario=self.request.user,
                activo=True
            ).first()

            if tratamiento_activo:
                nuevo_registro.tratamiento = tratamiento_activo

        nuevo_registro.save()
        messages.success(self.request, f"Registro del {fecha} creado correctamente")
        return redirect(self.success_url)


class RegistroDiarioUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para actualizar un registro diario existente
    """
    model = RegistroDiario
    form_class = RegistroDiarioForm
    template_name = 'moiraflow/registro_diario.html'
    success_url = reverse_lazy('moiraflow:calendario')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tipo_seguimiento'] = self.request.user.perfil.tipo_seguimiento
        return kwargs

    def get_queryset(self):
        return RegistroDiario.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Registro actualizado correctamente")
        return redirect(self.success_url)


class RegistroDiarioDeleteView(LoginRequiredMixin, DeleteView):
    """
    Vista para eliminar un registro diario
    """
    model = RegistroDiario
    template_name = 'moiraflow/registrodiario_confirm_delete.html'
    success_url = reverse_lazy('moiraflow:calendario')

    def get_queryset(self):
        return RegistroDiario.objects.filter(usuario=self.request.user)

    def delete(self, request, *args, **kwargs):
        registro = self.get_object()
        fecha = registro.fecha
        registro.delete()
        messages.success(request, f"Registro del {fecha} eliminado correctamente")
        return redirect(self.success_url)


class RegistroDiarioDetailView(LoginRequiredMixin, View):
    """
    Vista para obtener detalles de un registro específico via AJAX
    """

    def get(self, request, *args, **kwargs):
        dia = kwargs.get('dia')
        mes = kwargs.get('mes')
        anio = kwargs.get('anio')
        fecha = date(anio, mes, dia)

        try:
            registro = RegistroDiario.objects.get(usuario=request.user, fecha=fecha)
            data = {
                'id': registro.id,
                'es_dia_periodo': registro.es_dia_periodo,
                'flujo_menstrual': registro.get_flujo_menstrual_display() if registro.flujo_menstrual else '',
                'medicacion_tomada': registro.medicacion_tomada,
                'hora_medicacion': registro.hora_medicacion.strftime('%H:%M') if registro.hora_medicacion else '',
                'estados_animo': registro.estados_animo,
                'dolor': registro.dolor,
                'medicamentos': registro.medicamentos,
                'notas': registro.notas,
                'existe': True
            }
        except RegistroDiario.DoesNotExist:
            data = {'existe': False}

        return JsonResponse(data)


class CicloMenstrualCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un nuevo ciclo menstrual
    """
    model = CicloMenstrual
    form_class = CicloMenstrualForm
    success_url = reverse_lazy('moiraflow:calendario')

    def form_valid(self, form):
        nuevo_ciclo = form.save(commit=False)
        nuevo_ciclo.usuario = self.request.user
        nuevo_ciclo.save()
        messages.success(self.request, "Nuevo ciclo registrado correctamente")
        return redirect(self.success_url)


class TratamientoHormonalCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un nuevo tratamiento hormonal
    """
    model = TratamientoHormonal
    form_class = TratamientoHormonalForm
    success_url = reverse_lazy('moiraflow:calendario')

    def form_valid(self, form):
        nuevo_tratamiento = form.save(commit=False)
        nuevo_tratamiento.usuario = self.request.user
        nuevo_tratamiento.activo = True

        # Si se marca como activo, desactivar otros tratamientos activos
        if nuevo_tratamiento.activo:
            TratamientoHormonal.objects.filter(
                usuario=self.request.user,
                activo=True
            ).update(activo=False)

        nuevo_tratamiento.save()
        messages.success(self.request, "Nuevo tratamiento hormonal registrado correctamente")
        return redirect(self.success_url)

class CalendarioInteractivoCirularView(LoginRequiredMixin, TemplateView):
        template_name = 'moiraflow/calendario_interactivo_circular.html'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            perfil = self.request.user.perfil

            # Obtener año y mes actuales o del parámetro
            year = int(self.request.GET.get('year', timezone.now().year))
            month = int(self.request.GET.get('month', timezone.now().month))

            # Calcular días del mes
            _, num_days = calendar.monthrange(year, month)
            days_of_month = list(range(1, num_days + 1))

            # Obtener día actual
            today = timezone.now().date()
            current_day = today.day if today.year == year and today.month == month else None
            current_day_name = calendar.day_name[today.weekday()]

            # Obtener registros del mes
            first_day = date(year, month, 1)
            last_day = date(year, month, num_days)

            registros = RegistroDiario.objects.filter(
                usuario=self.request.user,
                fecha__gte=first_day,
                fecha__lte=last_day
            )

            # Crear diccionario de registros por día
            registros_por_dia = {}
            dias_periodo = 0
            dias_medicacion = 0

            for registro in registros:
                day = registro.fecha.day
                registros_por_dia[day] = {
                    'es_dia_periodo': registro.es_dia_periodo,
                    'medicacion_tomada': registro.medicacion_tomada,
                    'id': registro.id  # Añadido para poder editar/eliminar
                }

                if registro.es_dia_periodo:
                    dias_periodo += 1
                if registro.medicacion_tomada:
                    dias_medicacion += 1

            # Calcular meses anterior/siguiente
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1

            # Añadir todo al contexto
            context.update({
                'year': year,
                'month': month,
                'month_name': calendar.month_name[month],
                'total_days': num_days,
                'current_day': current_day,
                'current_day_name': current_day_name,
                'registros_por_dia': registros_por_dia,
                'prev_year': prev_year,
                'prev_month': prev_month,
                'next_year': next_year,
                'next_month': next_month,
                'dias_periodo': dias_periodo,
                'dias_medicacion': dias_medicacion,
                'dias_registrados': len(registros_por_dia),
                'ESTADO_ANIMO_CHOICES': RegistroDiario.ESTADO_ANIMO_CHOICES,
                'quick_form': RegistroDiarioForm(
                    tipo_seguimiento=perfil.tipo_seguimiento
                )
            })

            return context


class ListaArticulosView(ListView):
    model = Articulo
    template_name = 'moiraflow/articulos/lista_articulos.html'
    context_object_name = 'articulos'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(estado='publicado')

        # Filtro por categoría
        categoria = self.request.GET.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        # Filtro por autor (usando username directamente)
        autor = self.request.GET.get('autor')
        if autor:
            queryset = queryset.filter(autor__username=autor)

        return queryset.order_by('-fecha_publicacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener lista de autores con artículos publicados
        context['autores_disponibles'] = User.objects.filter(
            articulos__estado='publicado'
        ).distinct().order_by('username')

        context['categorias'] = Articulo.CATEGORIA_CHOICES
        return context


class DetalleArticuloView(DetailView):
    model = Articulo
    template_name = 'moiraflow/articulos/detalle_articulo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_editar'] = self.object.puede_editar(self.request.user)
        return context

class CrearArticuloView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Articulo
    form_class = ArticuloForm
    template_name = 'moiraflow/articulos/crear_articulo.html'
    success_url = reverse_lazy('moiraflow:lista_articulos')

    def test_func(self):
        return self.request.user.perfil.es_autor or self.request.user.perfil.es_administrador

    def form_valid(self, form):
        form.instance.autor = self.request.user
        messages.success(self.request, 'Artículo creado exitosamente!')
        return super().form_valid(form)

class EditarArticuloView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Articulo
    form_class = ArticuloForm
    template_name = 'moiraflow/articulos/editar_articulo.html'

    def test_func(self):
        articulo = self.get_object()
        return articulo.puede_editar(self.request.user)

    def get_success_url(self):
        return reverse_lazy('moiraflow:detalle_articulo', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Artículo actualizado exitosamente!')
        return super().form_valid(form)

class EliminarArticuloView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Articulo
    template_name = 'moiraflow/articulos/eliminar_articulo.html'
    success_url = reverse_lazy('moiraflow:lista_articulos')

    def test_func(self):
        articulo = self.get_object()
        return articulo.puede_editar(self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Artículo eliminado exitosamente!')
        return super().delete(request, *args, **kwargs)


class MascotaPanelView(LoginRequiredMixin, TemplateView):
    template_name = 'moiraflow/mascota_panel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mascota'] = self.request.user.mascota
        return context


from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@require_POST
@csrf_exempt
def alimentar_mascota(request):
    try:
        mascota = request.user.mascota

        # Primero devolvemos la imagen de comiendo
        response_data = {
            'success': True,
            'imagen_temporal': '/static/images/mascota_comiendo.gif',
            'nivel_hambre': mascota.nivel_hambre
        }

        # Luego procesamos la alimentación (con retraso en frontend)
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
@csrf_exempt
def finalizar_alimentacion(request):
    try:
        mascota = request.user.mascota
        mascota.alimentar()
        return JsonResponse({
            'success': True,
            'estado': mascota.estado,
            'estado_display': mascota.get_estado_display(),
            'nivel_hambre': mascota.nivel_hambre,
            'imagen_estado': mascota.imagen_estado,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
@csrf_exempt
def consejo_mascota(request):
    try:
        mascota = request.user.mascota
        consejo = mascota.dar_consejo()

        if consejo:
            return JsonResponse({
                'success': True,
                'consejo': consejo,
                'estado': mascota.estado,
                'estado_display': mascota.get_estado_display(),
                'nivel_hambre': mascota.nivel_hambre,
                'imagen_estado': mascota.imagen_estado,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'La mascota no está lo suficientemente satisfecha para dar consejos'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})