# moiraflow/tests/test_models.py

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta, time
import random
from moiraflow.models import (
    Perfil, CicloMenstrual, TratamientoHormonal, RegistroDiario,
    Recordatorio, EfectoTratamiento, Articulo, Mascota, Notificacion
)


class PerfilModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user2 = User.objects.create_user(username='testuser2', password='12345')
        self.user3 = User.objects.create_user(username='testuser3', password='12345')

    def test_creacion_perfil(self):
        perfil = Perfil.objects.create(
            usuario=self.user,
            genero=Perfil.Genero.FEMENINO,
            tipo_seguimiento=Perfil.TipoSeguimiento.MENSTRUAL,
            tipo_perfil=Perfil.TipoPerfil.USUARIO
        )

        self.assertEqual(perfil.usuario.username, 'testuser')
        self.assertEqual(perfil.genero, 'femenino')
        self.assertEqual(perfil.tipo_seguimiento, 'ciclo_menstrual')
        self.assertEqual(perfil.tipo_perfil, 'usuario')
        self.assertFalse(perfil.es_premium)

    def test_asignacion_automatica_tipo_seguimiento(self):
        # Para género femenino
        perfil_femenino = Perfil.objects.create(
            usuario=self.user,
            genero=Perfil.Genero.FEMENINO,
            tipo_perfil=Perfil.TipoPerfil.USUARIO
        )
        self.assertEqual(perfil_femenino.tipo_seguimiento, 'ciclo_menstrual')

        # Para género femenino trans
        perfil_trans = Perfil.objects.create(
            usuario=self.user2,
            genero=Perfil.Genero.FEMENINO_TRANS,
            tipo_perfil=Perfil.TipoPerfil.USUARIO
        )
        self.assertEqual(perfil_trans.tipo_seguimiento, 'tratamiento_hormonal')

    def test_limpieza_campos_no_relevantes(self):
        perfil = Perfil.objects.create(
            usuario=self.user3,
            genero=Perfil.Genero.FEMENINO_TRANS,
            tipo_perfil=Perfil.TipoPerfil.USUARIO,
            duracion_ciclo_promedio=28,
            duracion_periodo_promedio=5
        )
        self.assertIsNone(perfil.duracion_ciclo_promedio)
        self.assertIsNone(perfil.duracion_periodo_promedio)

    def test_propiedades_es_autor_es_administrador(self):
        perfil_usuario = Perfil.objects.create(
            usuario=self.user,
            genero=Perfil.Genero.FEMENINO,
            tipo_perfil=Perfil.TipoPerfil.USUARIO
        )
        self.assertFalse(perfil_usuario.es_autor)
        self.assertFalse(perfil_usuario.es_administrador)

        # Usar user2 para evitar conflicto de usuario único
        perfil_autor = Perfil.objects.create(
            usuario=self.user2,
            genero=Perfil.Genero.FEMENINO,
            tipo_perfil=Perfil.TipoPerfil.AUTOR
        )
        self.assertTrue(perfil_autor.es_autor)
        self.assertFalse(perfil_autor.es_administrador)

        # Usar user3 para evitar conflicto de usuario único
        perfil_admin = Perfil.objects.create(
            usuario=self.user3,
            genero=Perfil.Genero.FEMENINO,
            tipo_perfil=Perfil.TipoPerfil.ADMIN
        )
        self.assertFalse(perfil_admin.es_autor)
        self.assertTrue(perfil_admin.es_administrador)


class CicloMenstrualModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user,
            genero=Perfil.Genero.FEMENINO,
            tipo_seguimiento=Perfil.TipoSeguimiento.MENSTRUAL
        )

    def test_creacion_ciclo(self):
        ciclo = CicloMenstrual.objects.create(
            usuario=self.user,
            fecha_inicio=date(2023, 1, 1),
            fecha_fin=date(2023, 1, 28)
        )
        # Forzar cálculo de fase actual
        ciclo.fase_actual = ciclo.determinar_fase(date(2023, 1, 28))
        ciclo.save()

        self.assertEqual(ciclo.usuario.username, 'testuser')
        self.assertEqual(ciclo.duracion, 28)

    def test_ciclo_sin_fecha_fin(self):
        ciclo = CicloMenstrual.objects.create(
            usuario=self.user,
            fecha_inicio=date(2023, 1, 1)
        )

        self.assertIsNone(ciclo.duracion)
        self.assertIsNone(ciclo.fase_actual)


class TratamientoHormonalModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_creacion_tratamiento(self):
        tratamiento = TratamientoHormonal.objects.create(
            usuario=self.user,
            nombre_tratamiento="Terapia de estrógenos",
            tipo_hormona=TratamientoHormonal.TipoHormona.ESTROGENO,
            fecha_inicio=date(2023, 1, 1),
            fecha_fin=date(2023, 12, 31),
            dosis=2.5,
            frecuencia=1,
            frecuencia_tipo='diario',
            activo=True
        )

        self.assertEqual(tratamiento.usuario.username, 'testuser')
        self.assertEqual(tratamiento.nombre_tratamiento, "Terapia de estrógenos")
        self.assertEqual(tratamiento.dosis_diaria, 2.5)

    def test_dosis_diaria_calculo(self):
        # Tratamiento diario
        tratamiento_diario = TratamientoHormonal.objects.create(
            usuario=self.user,
            nombre_tratamiento="Test Diario",
            tipo_hormona=TratamientoHormonal.TipoHormona.ESTROGENO,
            fecha_inicio=date(2023, 1, 1),
            dosis=7.0,
            frecuencia=7,
            frecuencia_tipo='diario'
        )
        self.assertEqual(tratamiento_diario.dosis_diaria, 1.0)

        # Tratamiento semanal
        tratamiento_semanal = TratamientoHormonal.objects.create(
            usuario=self.user,
            nombre_tratamiento="Test Semanal",
            tipo_hormona=TratamientoHormonal.TipoHormona.ESTROGENO,
            fecha_inicio=date(2023, 1, 1),
            dosis=14.0,
            frecuencia=2,
            frecuencia_tipo='semanal'
        )
        self.assertAlmostEqual(tratamiento_semanal.dosis_diaria, 1.0, places=2)

    def test_esta_activo_en_fecha(self):
        hoy = date.today()
        tratamiento = TratamientoHormonal.objects.create(
            usuario=self.user,
            nombre_tratamiento="Test Activo",
            tipo_hormona=TratamientoHormonal.TipoHormona.ESTROGENO,
            fecha_inicio=hoy - timedelta(days=1),
            fecha_fin=hoy + timedelta(days=1),
            dosis=2.5,
            frecuencia=1,
            frecuencia_tipo='diario',
            activo=True
        )

        self.assertTrue(tratamiento.esta_activo_en_fecha(hoy))
        self.assertFalse(tratamiento.esta_activo_en_fecha(hoy + timedelta(days=2)))
        self.assertTrue(tratamiento.esta_activo_en_fecha())  # Fecha actual

    def test_progreso_tratamiento(self):
        hoy = date.today()
        inicio = hoy - timedelta(days=90)
        fin = hoy + timedelta(days=90)

        tratamiento = TratamientoHormonal.objects.create(
            usuario=self.user,
            nombre_tratamiento="Test Progreso",
            tipo_hormona=TratamientoHormonal.TipoHormona.ESTROGENO,
            fecha_inicio=inicio,
            fecha_fin=fin,
            dosis=2.5,
            frecuencia=1,
            frecuencia_tipo='diario',
            activo=True
        )

        self.assertAlmostEqual(tratamiento.progreso, 50, delta=5)  # Aprox 50%


class RegistroDiarioModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.perfil = Perfil.objects.create(
            usuario=self.user,
            genero=Perfil.Genero.FEMENINO,
            tipo_seguimiento=Perfil.TipoSeguimiento.MENSTRUAL
        )
        self.ciclo = CicloMenstrual.objects.create(
            usuario=self.user,
            fecha_inicio=date(2023, 1, 1),
            fecha_fin=date(2023, 1, 28)
        )

    def test_creacion_registro_menstrual(self):
        registro = RegistroDiario.objects.create(
            usuario=self.user,
            fecha=date(2023, 1, 5),
            ciclo=self.ciclo,
            es_dia_periodo=True,
            flujo_menstrual=RegistroDiario.FlujoMenstrual.MODERADO,
            estados_animo=['feliz', 'cansado'],
            sintomas_comunes=['dolor_cabeza']
        )

        self.assertEqual(registro.usuario.username, 'testuser')
        self.assertEqual(registro.tipo_seguimiento, 'ciclo_menstrual')
        self.assertEqual(registro.fase_ciclo, 'menstrual')
        self.assertEqual(registro.flujo_menstrual, 'moderado')
        self.assertIn('feliz', registro.estados_animo)

    def test_creacion_registro_hormonal(self):
        # Cambiamos el perfil a hormonal
        self.perfil.genero = Perfil.Genero.FEMENINO_TRANS
        self.perfil.tipo_seguimiento = Perfil.TipoSeguimiento.HORMONAL
        self.perfil.save()

        tratamiento = TratamientoHormonal.objects.create(
            usuario=self.user,
            nombre_tratamiento="Test Hormonal",
            tipo_hormona=TratamientoHormonal.TipoHormona.ESTROGENO,
            fecha_inicio=date(2023, 1, 1),
            dosis=2.5,
            frecuencia=1,
            frecuencia_tipo='diario',
            activo=True
        )

        registro = RegistroDiario.objects.create(
            usuario=self.user,
            fecha=date(2023, 1, 5),
            tratamiento=tratamiento,
            medicacion_tomada=True,
            hora_medicacion=time(8, 0),  # Usar time en lugar de string
            estados_animo=['feliz'],
            sintomas_comunes=[]
        )

        self.assertEqual(registro.tipo_seguimiento, 'tratamiento_hormonal')
        self.assertTrue(registro.medicacion_tomada)
        self.assertEqual(registro.hora_medicacion.hour, 8)

    def test_validacion_campos_menstruales(self):
        # Intento crear registro menstrual sin ciclo
        with self.assertRaises(ValidationError):
            registro = RegistroDiario(
                usuario=self.user,
                fecha=date(2023, 1, 5),
                es_dia_periodo=True,
                flujo_menstrual=RegistroDiario.FlujoMenstrual.MODERADO,
                estados_animo=['feliz'],
                sintomas_comunes=[]
            )
            registro.full_clean()

        # Intento crear registro con detalles menstruales pero no es día de periodo
        with self.assertRaises(ValidationError):
            registro = RegistroDiario(
                usuario=self.user,
                fecha=date(2023, 1, 5),
                ciclo=self.ciclo,
                es_dia_periodo=False,
                flujo_menstrual=RegistroDiario.FlujoMenstrual.MODERADO,
                estados_animo=['feliz'],
                sintomas_comunes=[]
            )
            registro.full_clean()

    def test_limpieza_campos_no_correspondientes(self):
        registro = RegistroDiario(
            usuario=self.user,
            fecha=date(2023, 1, 5),
            ciclo=self.ciclo,
            es_dia_periodo=True,
            tratamiento=TratamientoHormonal.objects.create(
                usuario=self.user,
                nombre_tratamiento="Test",
                tipo_hormona=TratamientoHormonal.TipoHormona.ESTROGENO,
                fecha_inicio=date(2023, 1, 1),
                dosis=2.5,
                frecuencia=1,
                frecuencia_tipo='diario'
            ),
            medicacion_tomada=True,
            estados_animo=['feliz'],
            sintomas_comunes=['dolor_cabeza']
        )
        registro.full_clean()

        self.assertIsNone(registro.tratamiento)
        self.assertFalse(registro.medicacion_tomada)


class RecordatorioModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.hoy = date(2023, 6, 3)  # Fecha fija para pruebas

    def test_creacion_recordatorio(self):
        recordatorio = Recordatorio.objects.create(
            usuario=self.user,
            titulo="Tomar medicación",
            tipo="medicacion",
            fecha_inicio=self.hoy,
            dias_frecuencia=1,
            notificar=True
        )

        self.assertEqual(recordatorio.usuario.username, 'testuser')
        self.assertTrue(recordatorio.es_recurrente)

    def test_marcar_como_visto(self):
        recordatorio = Recordatorio.objects.create(
            usuario=self.user,
            titulo="Test Visto",
            tipo="medicacion",
            fecha_inicio=self.hoy,
            notificar=True
        )

        self.assertFalse(recordatorio.visto)
        recordatorio.marcar_como_visto()
        self.assertTrue(recordatorio.visto)


class EfectoTratamientoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.tratamiento = TratamientoHormonal.objects.create(
            usuario=self.user,
            nombre_tratamiento="Test Tratamiento",
            tipo_hormona=TratamientoHormonal.TipoHormona.ESTROGENO,
            fecha_inicio=date(2023, 1, 1),
            dosis=2.5,
            frecuencia=1,
            frecuencia_tipo='diario'
        )

    def test_creacion_efecto(self):
        efecto = EfectoTratamiento.objects.create(
            usuario=self.user,
            tratamiento=self.tratamiento,
            nombre_efecto='aumento_energia',
            tipo_efecto='deseado',
            fecha_inicio=date(2023, 1, 15),
            intensidad=3,
            notas="Notas de prueba"
        )

        self.assertEqual(efecto.usuario.username, 'testuser')
        self.assertEqual(efecto.tratamiento.nombre_tratamiento, "Test Tratamiento")
        self.assertEqual(efecto.nombre_efecto, "aumento_energia")
        self.assertEqual(efecto.intensidad, 3)


class ArticuloModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='autor', password='12345')
        self.admin = User.objects.create_user(username='admin', password='12345')
        self.otro_usuario = User.objects.create_user(username='otro', password='12345')

        # Crear perfiles para evitar el error RelatedObjectDoesNotExist
        Perfil.objects.create(
            usuario=self.user,
            genero=Perfil.Genero.FEMENINO,
            tipo_perfil=Perfil.TipoPerfil.AUTOR
        )
        Perfil.objects.create(
            usuario=self.admin,
            genero=Perfil.Genero.FEMENINO,
            tipo_perfil=Perfil.TipoPerfil.ADMIN
        )
        Perfil.objects.create(
            usuario=self.otro_usuario,
            genero=Perfil.Genero.FEMENINO,
            tipo_perfil=Perfil.TipoPerfil.USUARIO
        )

    def test_creacion_articulo(self):
        articulo = Articulo.objects.create(
            autor=self.user,
            titulo="Test Artículo",
            contenido="Contenido de prueba",
            estado='borrador',
            categoria='salud_menstrual'
        )

        self.assertEqual(articulo.autor.username, 'autor')
        self.assertEqual(articulo.titulo, "Test Artículo")
        self.assertEqual(articulo.estado, "borrador")
        self.assertIsNone(articulo.fecha_publicacion)

    def test_publicacion_articulo(self):
        articulo = Articulo.objects.create(
            autor=self.user,
            titulo="Test Publicación",
            contenido="Contenido de prueba",
            estado='publicado',
            categoria='salud_menstrual'
        )

        self.assertIsNotNone(articulo.fecha_publicacion)
        self.assertTrue(articulo.fecha_publicacion <= timezone.now())

    def test_puede_editar(self):
        articulo = Articulo.objects.create(
            autor=self.user,
            titulo="Test Edición",
            contenido="Contenido de prueba",
            estado='borrador',
            categoria='salud_menstrual'
        )

        self.assertTrue(articulo.puede_editar(self.user))
        self.assertTrue(articulo.puede_editar(self.admin))
        self.assertFalse(articulo.puede_editar(self.otro_usuario))


class MascotaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_creacion_mascota(self):
        mascota = Mascota.objects.create(
            usuario=self.user,
            nivel_hambre=50
        )

        self.assertEqual(mascota.usuario.username, 'testuser')
        self.assertEqual(mascota.estado, 'normal')
        self.assertEqual(mascota.nivel_hambre, 50)

    def test_alimentar_mascota(self):
        mascota = Mascota.objects.create(
            usuario=self.user,
            nivel_hambre=30
        )

        mascota.alimentar()
        self.assertGreater(mascota.nivel_hambre, 30)

    def test_dar_consejo(self):
        mascota = Mascota.objects.create(
            usuario=self.user,
            nivel_hambre=50
        )

        consejo = mascota.dar_consejo()
        self.assertIsNotNone(consejo)
        self.assertLess(mascota.nivel_hambre, 50)
        self.assertIn(consejo, Mascota.CONSEJOS)

    def test_actualizar_estado(self):
        mascota = Mascota.objects.create(
            usuario=self.user,
            nivel_hambre=20
        )
        mascota.actualizar_estado()
        self.assertEqual(mascota.estado, 'hambrienta')

        mascota.nivel_hambre = 80
        mascota.actualizar_estado()
        self.assertEqual(mascota.estado, 'feliz')

        mascota.nivel_hambre = 50
        mascota.actualizar_estado()
        self.assertEqual(mascota.estado, 'normal')


class NotificacionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.recordatorio = Recordatorio.objects.create(
            usuario=self.user,
            titulo="Test Notificación",
            tipo="medicacion",
            fecha_inicio=date.today(),
            notificar=True
        )

    def test_creacion_notificacion(self):
        notificacion = Notificacion.objects.create(
            usuario=self.user,
            recordatorio=self.recordatorio,
            mensaje="Este es un mensaje de prueba"
        )

        self.assertEqual(notificacion.usuario.username, 'testuser')
        self.assertEqual(notificacion.recordatorio.titulo, "Test Notificación")
        self.assertFalse(notificacion.leida)