from calendar import calendar

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from moiraflow.models import Perfil, RegistroDiario, CicloMenstrual, TratamientoHormonal, Articulo, Mascota, Recordatorio, Notificacion
from moiraflow.forms import RegistroCompletoForm, RegistroDiarioForm
import json

class PaginaPrincipalViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(usuario=self.user, genero='femenino')
        self.url = reverse('moiraflow:index')

    def test_acceso_no_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/index.html')
        self.assertNotIn('perfil', response.context)

    def test_acceso_autenticado(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/index.html')
        self.assertEqual(response.context['perfil'], self.perfil)


class RegistroUsuarioViewTest(TestCase):
    def setUp(self):
        self.url = reverse('moiraflow:registro')
        self.success_url = reverse('moiraflow:index')
        self.valid_data = {
            'username': 'nuevousuario',
            'email': 'nuevo@ejemplo.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'genero': 'femenino',
            'fecha_nacimiento': '1990-01-01',
        }

    def test_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/registro.html')
        self.assertIsInstance(response.context['form'], RegistroCompletoForm)

    def test_registro_exitoso(self):
        response = self.client.post(self.url, data=self.valid_data)

        # Verificar que el usuario quedó autenticado
        user = User.objects.get(username='nuevousuario')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), '¡Registro exitoso!')


    def test_registro_invalido(self):
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'diferentepassword'
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuevousuario').exists())

        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Por favor corrige los errores en el formulario')


class EditarPerfilViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(usuario=self.user, genero='femenino')
        self.client.login(username='testuser', password='12345')
        self.url = reverse('moiraflow:editar_perfil', kwargs={'pk': self.perfil.pk})

    def test_acceso_propietario(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/editar_perfil.html')
        self.assertEqual(response.context['object'], self.perfil)

    def test_acceso_no_autorizado(self):
        otro_user = User.objects.create_user(username='otrouser', password='12345')
        otro_perfil = Perfil.objects.create(usuario=otro_user, genero='masculino')
        self.client.login(username='otrouser', password='12345')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_edicion_exitosa(self):
        data = {
            'genero': 'masculino trans',
            'fecha_nacimiento': '1995-05-15',
            'tipo_perfil': 'normal',  # Campo que solo admin puede modificar
        }
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, reverse('moiraflow:mi_perfil'))

        # Verificar cambios
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.genero, 'masculino trans')
        self.assertEqual(str(self.perfil.fecha_nacimiento), '1995-05-15')

        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Perfil actualizado correctamente')

    def test_admin_puede_editar_cualquier_perfil(self):
        admin_user = User.objects.create_user(username='admin', password='12345')
        Perfil.objects.create(usuario=admin_user, genero='femenino', es_administrador=True)
        self.client.login(username='admin', password='12345')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class MiPerfilViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(usuario=self.user, genero='femenino')
        self.url = reverse('moiraflow:mi_perfil')
        self.client.login(username='testuser', password='12345')

    def test_acceso_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/mi_perfil.html')
        self.assertEqual(response.context['object'], self.perfil)

    def test_contexto_ciclo_menstrual(self):
        # Para género femenino debe mostrar datos de ciclo
        response = self.client.get(self.url)
        self.assertTrue(response.context['mostrar_datos_ciclo'])

        # Cambiar a género que no muestra ciclo
        self.perfil.genero = 'masculino'
        self.perfil.save()
        response = self.client.get(self.url)
        self.assertFalse(response.context['mostrar_datos_ciclo'])


class CalendarioViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(usuario=self.user, genero='femenino')
        self.client.login(username='testuser', password='12345')
        self.today = date.today()
        self.url = reverse('moiraflow:calendario_mes', kwargs={
            'year': self.today.year,
            'month': self.today.month
        })

    def test_redireccion_sin_parametros(self):
        url = reverse('moiraflow:calendario')
        response = self.client.get(url)
        expected_url = reverse('moiraflow:calendario_mes', kwargs={
            'year': self.today.year,
            'month': self.today.month
        })
        self.assertRedirects(response, expected_url)

    def test_contexto_calendario(self):
        # Crear algunos registros para probar
        RegistroDiario.objects.create(
            usuario=self.user,
            fecha=self.today,
            sintomas_comunes=['dolor_cabeza']
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/calendario.html')

        # Verificar datos del calendario
        context = response.context
        self.assertEqual(context['month'], self.today.month)
        self.assertEqual(context['year'], self.today.year)

        # Verificar que los registros aparecen en el día correcto
        day_data = None
        for week in context['weeks']:
            for day in week:
                if day and day['day'] == self.today.day:
                    day_data = day
                    break
        self.assertIsNotNone(day_data)
        self.assertEqual(len(day_data['registros']), 1)


class RegistrosDiaViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user,
            genero='femenino',
            tipo_seguimiento='ciclo_menstrual',
            duracion_ciclo_promedio=28
        )
        self.client.login(username='testuser', password='12345')
        self.today = date.today()
        self.url = reverse('moiraflow:registros_dia', kwargs={
            'year': self.today.year,
            'month': self.today.month,
            'day': self.today.day
        })

    def test_acceso_dia_actual(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/registros_dia.html')

        context = response.context
        self.assertEqual(context['fecha'], self.today)
        self.assertIsNone(context['registro'])  # No hay registro creado aún
        self.assertIsInstance(context['form'], RegistroDiarioForm)

    def test_creacion_ciclo_automatica(self):
        # Verificar que se crea un ciclo automáticamente
        self.assertFalse(CicloMenstrual.objects.exists())

        response = self.client.get(self.url)
        self.assertTrue(CicloMenstrual.objects.exists())

        ciclo = CicloMenstrual.objects.first()
        self.assertEqual(ciclo.usuario, self.user)
        self.assertEqual(ciclo.fecha_fin - ciclo.fecha_inicio, timedelta(days=27))  # 28 días de duración

    def test_con_registro_existente(self):
        registro = RegistroDiario.objects.create(
            usuario=self.user,
            fecha=self.today,
            sintomas_comunes=['dolor_cabeza']
        )

        response = self.client.get(self.url)
        self.assertEqual(response.context['registro'], registro)
        self.assertEqual(response.context['form'].instance, registro)


class RegistroDiarioCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user,
            genero='femenino',
            tipo_seguimiento='ciclo_menstrual'
        )
        self.client.login(username='testuser', password='12345')
        self.today = date.today()
        self.url = reverse('moiraflow:registro_diario_crear', kwargs={
            'year': self.today.year,
            'month': self.today.month,
            'day': self.today.day
        })
        self.valid_data = {
            'fecha': str(self.today),
            'sintomas_comunes': ['dolor_cabeza'],
            'es_dia_periodo': False,
            'medicacion_tomada': True
        }

    def test_creacion_registro(self):
        response = self.client.post(self.url, data=self.valid_data)
        self.assertEqual(RegistroDiario.objects.count(), 1)

        registro = RegistroDiario.objects.first()
        self.assertEqual(registro.usuario, self.user)
        self.assertEqual(registro.fecha, self.today)
        self.assertEqual(registro.sintomas_comunes, ['dolor_cabeza'])

        # Verificar redirección
        self.assertRedirects(response, reverse('moiraflow:calendario_mes', kwargs={
            'year': self.today.year,
            'month': self.today.month
        }))

        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Registro creado correctamente")

    def test_creacion_invalida(self):
        invalid_data = self.valid_data.copy()
        invalid_data['sintomas_comunes'] = ['sintoma_inexistente']  # Sintoma no válido

        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RegistroDiario.objects.count(), 0)
        self.assertFormError(response, 'form', 'sintomas_comunes',
                             'Seleccione una opción válida. sintoma_inexistente no es una de las opciones disponibles.')


class NotificacionesAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(usuario=self.user, genero='femenino')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Crear recordatorio y notificaciones
        self.recordatorio = Recordatorio.objects.create(
            usuario=self.user,
            titulo='Test recordatorio',
            fecha_inicio=date.today()
        )
        self.notificacion1 = Notificacion.objects.create(
            usuario=self.user,
            recordatorio=self.recordatorio,
            mensaje='Notificación 1',
            leida=False
        )
        self.notificacion2 = Notificacion.objects.create(
            usuario=self.user,
            recordatorio=self.recordatorio,
            mensaje='Notificación 2',
            leida=False
        )

    def test_obtener_notificaciones(self):
        url = reverse('moiraflow:obtener_notificaciones')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notificaciones'][0]['id'], self.notificacion2.id)  # Orden descendente

    def test_marcar_notificacion_leida(self):
        url = reverse('moiraflow:marcar_notificacion_leida', kwargs={'notificacion_id': self.notificacion1.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        self.notificacion1.refresh_from_db()
        self.assertTrue(self.notificacion1.leida)

    def test_marcar_todas_leidas(self):
        url = reverse('moiraflow:marcar_todas_leidas')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Verificar que todas las notificaciones están marcadas como leídas
        self.assertEqual(Notificacion.objects.filter(usuario=self.user, leida=False).count(), 0)


class MascotaAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(usuario=self.user, genero='femenino')
        self.mascota = Mascota.objects.create(usuario=self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_alimentar_mascota(self):
        url = reverse('moiraflow:alimentar_mascota')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_finalizar_alimentacion(self):
        url = reverse('moiraflow:finalizar_alimentacion')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_consejo_mascota(self):
        # Primero alimentamos la mascota para que esté satisfecha
        self.mascota.nivel_hambre = 0
        self.mascota.save()

        url = reverse('moiraflow:consejo_mascota')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

class EstadisticasViewSetTest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='12345')
        Perfil.objects.create(usuario=self.admin_user, es_administrador=True)

        self.normal_user = User.objects.create_user(username='normal', password='12345')
        Perfil.objects.create(usuario=self.normal_user)

        self.client = APIClient()

    def test_acceso_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('moiraflow:estadisticas-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_usuarios', response.data)
        self.assertIn('endpoints', response.data)

    def test_acceso_no_admin(self):
        self.client.force_authenticate(user=self.normal_user)
        url = reverse('moiraflow:estadisticas-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ListaArticulosViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='autor', password='12345')
        self.perfil = Perfil.objects.create(usuario=self.user, es_autor=True)

        self.articulo1 = Articulo.objects.create(
            titulo="Artículo 1",
            contenido="Contenido 1",
            autor=self.user,
            estado='publicado',
            categoria='salud'
        )
        self.articulo2 = Articulo.objects.create(
            titulo="Artículo 2",
            contenido="Contenido 2",
            autor=self.user,
            estado='publicado',
            categoria='bienestar'
        )
        self.url = reverse('moiraflow:lista_articulos')

    def test_lista_articulos(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/articulos/lista_articulos.html')
        self.assertEqual(len(response.context['articulos']), 2)

        # Verificar filtros
        response = self.client.get(self.url + '?categoria=salud')
        self.assertEqual(len(response.context['articulos']), 1)
        self.assertEqual(response.context['articulos'][0], self.articulo1)

    def test_context_data(self):
        response = self.client.get(self.url)

        self.assertIn('autores_disponibles', response.context)
        self.assertIn('categorias', response.context)
        self.assertEqual(len(response.context['categorias']), len(Articulo.CATEGORIA_CHOICES))


class AdminDashboardViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='12345')
        Perfil.objects.create(usuario=self.admin_user, es_administrador=True)

        self.normal_user = User.objects.create_user(username='normal', password='12345')
        Perfil.objects.create(usuario=self.normal_user)

        self.url = reverse('moiraflow:admin_dashboard')

    def test_acceso_admin(self):
        self.client.login(username='admin', password='12345')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moiraflow/admin_dashboard.html')

    def test_acceso_no_admin(self):
        self.client.login(username='normal', password='12345')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)