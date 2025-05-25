from collections import defaultdict
from django.db import transaction, IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth import logout, login
from moiraflow.models import Perfil, RegistroDiario, TratamientoHormonal, CicloMenstrual, Articulo, Mascota, \
    EfectoTratamiento, Recordatorio
from moiraflow.forms import RegistroCompletoForm, RegistroDiarioForm, TratamientoHormonalForm, CicloMenstrualForm, \
    ArticuloForm, EditarPerfilForm
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, FormView, View, DetailView, ListView
from django.shortcuts import redirect
from django.contrib import messages
import calendar
from datetime import datetime, date, timedelta
from django.urls import reverse_lazy, reverse
from django.views.generic import View
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import F, Func, Value, IntegerField
from django.db.models.functions import Mod

class PaginaPrincipalView(TemplateView):
    template_name = 'moiraflow/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['perfil'] = self.request.user.perfil
        return context


class RegistroUsuarioView(CreateView):
    template_name = 'moiraflow/registro.html'
    form_class = RegistroCompletoForm
    success_url = reverse_lazy('moiraflow:index')

    def form_valid(self, form):
        # Forzar cierre de sesión previa
        if self.request.user.is_authenticated:
            from django.contrib.auth import logout
            logout(self.request)
            # Limpiar cookies de sesión
            response = redirect('moiraflow:registro')
            response.delete_cookie('sessionid')
            return response

        # Crear usuario y perfil
        try:
            user = form.save()  # Llama al save() modificado del formulario
            login(self.request, user)
            messages.success(self.request, '¡Registro exitoso!')
            return redirect(self.success_url)
        except IntegrityError:
            messages.error(self.request, 'Error al crear el perfil. Por favor intente nuevamente.')
        # Redirigimos a la página principal
        return redirect(self.success_url)

    def form_invalid(self, form):
        """Maneja los errores del formulario"""
        messages.error(self.request, 'Por favor corrige los errores en el formulario')
        return super().form_invalid(form)


@require_POST
@csrf_exempt
def ajax_login(request):
    from django.contrib.auth import authenticate, login
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('moiraflow:index')  # Añade esta línea
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': 'Usuario o contraseña incorrectos'
        })


@require_POST
@csrf_exempt
def ajax_logout(request):
    from django.contrib.auth import logout
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('moiraflow:index')
        })
    return JsonResponse({'success': False})


class EditarPerfilView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "moiraflow/editar_perfil.html"
    model = Perfil
    form_class = EditarPerfilForm  # Usamos el nuevo formulario
    success_url = reverse_lazy('moiraflow:mi_perfil')  # Asegúrate que esta URL existe

    def test_func(self):
        perfil = self.get_object()
        user = self.request.user
        # Permite edición si: es el dueño del perfil O es administrador
        return user == perfil.usuario or (hasattr(user, 'perfil') and user.perfil.es_administrador)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        perfil = self.get_object()

        # Si el usuario no es administrador, ocultamos el campo tipo_perfil (si está en el formulario)
        if 'tipo_perfil' in form.fields and not (hasattr(user, 'perfil') and user.perfil.es_administrador):
            form.fields['tipo_perfil'].disabled = True
            form.fields['tipo_perfil'].help_text = "Solo los administradores pueden modificar este campo"

        return form

    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado correctamente')
        return super().form_valid(form)

    def get_success_url(self):
        # Alternativa: redirigir al perfil editado usando su PK
        # return reverse('moiraflow:mi_perfil', kwargs={'pk': self.object.pk})
        return super().get_success_url()


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
    template_name = 'moiraflow/calendario.html'

    def get(self, request, *args, **kwargs):
        # Si no vienen parámetros, redirigir al mes actual
        if 'year' not in kwargs or 'month' not in kwargs:
            today = date.today()
            return redirect(reverse('moiraflow:calendario_mes', kwargs={
                'year': today.year,
                'month': today.month
            }))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = int(self.kwargs['year'])
        month = int(self.kwargs['month'])

        # Validación de mes
        if month < 1 or month > 12:
            month = date.today().month

        # Cálculo de meses anterior/siguiente
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year

        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        # Resto de tu lógica para el calendario...
        cal = calendar.monthcalendar(year, month)
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        # Obtener registros del mes
        registros = RegistroDiario.objects.filter(
            usuario=self.request.user,
            fecha__gte=first_day,
            fecha__lte=last_day
        ).order_by('fecha')

        # Obtener todos los recordatorios del usuario
        recordatorios = Recordatorio.objects.filter(
            usuario=self.request.user,
            activo=True
        )

        # Organizar registros por día
        registros_dict = defaultdict(list)
        for registro in registros:
            registros_dict[registro.fecha.day].append(registro)

        # Organizar recordatorios por día
        recordatorios_dict = defaultdict(list)
        for recordatorio in recordatorios:
            if recordatorio.es_recurrente:
                # Para recordatorios recurrentes
                current_date = recordatorio.fecha_inicio
                while current_date <= last_day:
                    if first_day <= current_date <= last_day:
                        recordatorios_dict[current_date.day].append(recordatorio)
                    current_date += timedelta(days=recordatorio.dias_frecuencia)
            else:
                # Para recordatorios no recurrentes
                if first_day <= recordatorio.fecha_inicio <= last_day:
                    recordatorios_dict[recordatorio.fecha_inicio.day].append(recordatorio)

        # Preparar datos para el template
        weeks = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append(None)
                else:
                    week_data.append({
                        'day': day,
                        'date': date(year, month, day),
                        'registros': registros_dict.get(day, []),
                        'recordatorios': recordatorios_dict.get(day, [])
                    })
            weeks.append(week_data)

        context.update({
            'weeks': weeks,
            'month_name': first_day.strftime('%B'),
            'year': year,
            'month': month,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'url_anterior': reverse('moiraflow:calendario_mes', kwargs={
                'year': prev_year,
                'month': prev_month
            }),
            'url_siguiente': reverse('moiraflow:calendario_mes', kwargs={
                'year': next_year,
                'month': next_month
            }),
        })

        return context


class RegistrosDiaView(LoginRequiredMixin, TemplateView):
    template_name = 'moiraflow/registros_dia.html'

    def get_context_data(self, year, month, day, **kwargs):
        context = super().get_context_data(**kwargs)
        fecha = date(year, month, day)
        perfil = self.request.user.perfil

        registro = RegistroDiario.objects.filter(
            usuario=self.request.user,
            fecha=fecha
        ).first()

        # Obtener recordatorios para esta fecha
        recordatorios = Recordatorio.objects.filter(
            usuario=self.request.user,
            activo=True
        ).filter(
            Q(fecha_inicio=fecha) |  # Recordatorios no recurrentes (dias_frecuencia = 0)
            Q(dias_frecuencia__gt=0,  # Recordatorios recurrentes
              fecha_inicio__lte=fecha)
        )

        # Filtrar recordatorios recurrentes que caen en esta fecha
        recordatorios_validos = []
        for recordatorio in recordatorios:
            if recordatorio.dias_frecuencia > 0:  # Es recurrente
                # Calcular si esta fecha está en la secuencia recurrente
                delta = (fecha - recordatorio.fecha_inicio).days
                if delta >= 0 and delta % recordatorio.dias_frecuencia == 0:
                    recordatorios_validos.append(recordatorio)
            else:  # No es recurrente
                recordatorios_validos.append(recordatorio)

        ciclo = None
        tratamiento_activo = None

        if perfil.tipo_seguimiento == 'ciclo_menstrual':
            # Buscar ciclo activo para esta fecha
            ciclo = CicloMenstrual.objects.filter(
                usuario=self.request.user,
                fecha_inicio__lte=fecha,
                fecha_fin__gte=fecha
            ).first()

            # Si no hay ciclo activo, crear uno automáticamente
            if not ciclo and perfil.duracion_ciclo_promedio:
                fecha_inicio = fecha - timedelta(days=perfil.duracion_ciclo_promedio - 1)
                fecha_fin = fecha_inicio + timedelta(days=perfil.duracion_ciclo_promedio - 1)

                ciclo = CicloMenstrual.objects.create(
                    usuario=self.request.user,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )

        elif perfil.tipo_seguimiento == 'tratamiento_hormonal':
            tratamiento_activo = TratamientoHormonal.objects.filter(
                usuario=self.request.user,
                activo=True,
                fecha_inicio__lte=fecha,
                fecha_fin__gte=fecha
            ).first()

        form_kwargs = {
            'usuario': self.request.user,
            'fecha': fecha,
            'tipo_seguimiento': perfil.tipo_seguimiento,
            'instance': registro
        }

        if perfil.tipo_seguimiento == 'ciclo_menstrual' and ciclo:
            form_kwargs['ciclo'] = ciclo
        elif perfil.tipo_seguimiento == 'tratamiento_hormonal' and tratamiento_activo:
            form_kwargs['tratamiento'] = tratamiento_activo

        context.update({
            'fecha': fecha,
            'registro': registro,
            'recordatorios': recordatorios,
            'ciclo': ciclo,
            'tratamiento_activo': tratamiento_activo,
            'perfil': perfil,
            'form': RegistroDiarioForm(**form_kwargs)
        })
        return context


class RegistroDiarioCreateView(LoginRequiredMixin, CreateView):
    model = RegistroDiario
    form_class = RegistroDiarioForm
    template_name = 'moiraflow/registro_diario_crear.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['usuario'] = self.request.user
        kwargs['fecha'] = date(
            year=int(self.kwargs['year']),
            month=int(self.kwargs['month']),
            day=int(self.kwargs['day'])
        )
        # Añadir tipo_seguimiento del perfil del usuario
        kwargs['tipo_seguimiento'] = self.request.user.perfil.tipo_seguimiento
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['fecha'] = date(
            year=int(self.kwargs['year']),
            month=int(self.kwargs['month']),
            day=int(self.kwargs['day'])
        )
        return initial

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.fecha = date(
            year=int(self.kwargs['year']),
            month=int(self.kwargs['month']),
            day=int(self.kwargs['day'])
        )

        # Verifica si el formulario es válido
        if not form.is_valid():
            return self.form_invalid(form)

        try:
            self.object = form.save()
            messages.success(self.request, "Registro creado correctamente")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error al crear el registro: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('moiraflow:calendario_mes', kwargs={
            'year': self.object.fecha.year,
            'month': self.object.fecha.month
        })


class RegistroDiarioUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para actualizar un registro diario existente
    """
    model = RegistroDiario
    form_class = RegistroDiarioForm
    template_name = 'moiraflow/registro_diario_crear.html'
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
    template_name = 'moiraflow/registro_diario_confirm_delete.html'
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
        mascota, created = Mascota.objects.get_or_create(usuario=self.request.user)
        context['mascota'] = mascota
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
            # Asegurarnos de actualizar el estado después de dar el consejo
            mascota.actualizar_estado()
            return JsonResponse({
                'success': True,
                'consejo': consejo,
                'estado': mascota.estado,
                'estado_display': mascota.get_estado_display(),
                'nivel_hambre': mascota.nivel_hambre,
                'imagen_estado': mascota.imagen_estado,
                'nuevo_estado': mascota.estado,  # Añadido para claridad
                'nueva_imagen': mascota.imagen_estado  # Añadido para claridad
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'La mascota no está lo suficientemente satisfecha para dar consejos'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from django.db.models import Q, Func, F, IntegerField
from .models import RegistroDiario


class SintomasViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            year = int(request.GET.get('year', datetime.now().year))
            month = int(request.GET.get('month', datetime.now().month))

            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month + 1, 1).date()

            sintomas_a_analizar = [
                RegistroDiario.SintomasComunes.DOLOR_CABEZA,
                RegistroDiario.SintomasComunes.DOLOR_ESPALDA,
                RegistroDiario.SintomasComunes.FATIGA,
                # ... añade aquí el resto de los síntomas de SintomasComunes que quieras analizar
            ]

            registros_base = RegistroDiario.objects.filter(
                usuario=request.user,
                fecha__gte=start_date,
                fecha__lt=end_date
            )

            resultados = []
            for sintoma_clave in sintomas_a_analizar:
                conteo = registros_base.filter(Q(sintomas_comunes__contains=[sintoma_clave])).count()
                if conteo > 0:
                    resultados.append({
                        'nombre': RegistroDiario.SintomasComunes(sintoma_clave).label,
                        'dias_presente': conteo,
                        'intensidad_promedio': 1
                    })

            return Response({
                'year': year,
                'month': month,
                'sintomas': resultados
            })

        except Exception as e:
            return Response({'error': str(e)}, status=400)


@require_GET
@login_required
def obtener_notificaciones(request):
    """
    Vista para obtener notificaciones no leídas del usuario
    """
    hoy = timezone.now().date()

    # Recordatorios pendientes
    recordatorios = request.user.recordatorios.filter(
        activo=True,
        notificar=True,
        visto=False,
        fecha_notificacion__lte=hoy,
        proxima_fecha__gte=hoy
    ).order_by('proxima_fecha')[:10]

    notificaciones = []
    for r in recordatorios:
        notificaciones.append({
            'id': r.id,
            'titulo': r.titulo,
            'descripcion': r.descripcion,
            'tipo': r.tipo,
            'fecha_evento': r.proxima_fecha.strftime('%d/%m/%Y'),
            'hora_evento': r.hora.strftime('%H:%M') if r.hora else '',
            'dias_restantes': (r.proxima_fecha - hoy).days,
            'es_hoy': r.proxima_fecha == hoy,
            'tipo_icono': 'alarm' if r.tipo == 'medicacion' else 'event'
        })

    return JsonResponse({'notificaciones': notificaciones})


@require_GET
@login_required
def marcar_notificacion_vista(request, recordatorio_id):
    """
    Marca una notificación como vista
    """
    try:
        recordatorio = request.user.recordatorios.get(id=recordatorio_id)
        recordatorio.marcar_como_visto()
        return JsonResponse({'success': True})
    except Recordatorio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Recordatorio no encontrado'}, status=404)


class ListaRecordatoriosView(LoginRequiredMixin, ListView):
    model = Recordatorio
    template_name = 'moiraflow/recordatorios/lista_recordatorios.html'
    context_object_name = 'recordatorios'

    def get_queryset(self):
        # Ordenar por fecha_inicio en lugar de proxima_fecha
        return Recordatorio.objects.filter(
            usuario=self.request.user
        ).order_by('fecha_inicio', 'dias_frecuencia')

class CrearRecordatorioView(LoginRequiredMixin, CreateView):
    model = Recordatorio
    template_name = 'moiraflow/recordatorios/crear_editar_recordatorio.html'
    fields = ['titulo', 'descripcion', 'tipo', 'fecha_inicio', 'hora',
              'dias_frecuencia', 'activo', 'notificar', 'dias_antelacion']
    success_url = reverse_lazy('moiraflow:lista_recordatorios')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, 'Recordatorio creado exitosamente!')
        return super().form_valid(form)


class EditarRecordatorioView(LoginRequiredMixin, UpdateView):
    model = Recordatorio
    template_name = 'moiraflow/recordatorios/crear_editar_recordatorio.html'
    fields = ['titulo', 'descripcion', 'tipo', 'fecha_inicio', 'hora',
              'dias_frecuencia', 'activo', 'notificar', 'dias_antelacion']
    success_url = reverse_lazy('moiraflow:lista_recordatorios')

    def get_queryset(self):
        return Recordatorio.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Recordatorio actualizado exitosamente!')
        return super().form_valid(form)


class EliminarRecordatorioView(LoginRequiredMixin, DeleteView):
    model = Recordatorio
    template_name = 'moiraflow/recordatorios/eliminar_recordatorio.html'
    success_url = reverse_lazy('moiraflow:lista_recordatorios')

    def get_queryset(self):
        return Recordatorio.objects.filter(usuario=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Recordatorio eliminado exitosamente!')
        return super().delete(request, *args, **kwargs)
