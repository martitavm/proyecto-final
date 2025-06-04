from django.core.management.base import BaseCommand
import random
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from moiraflow.models import (
    User, Perfil, CicloMenstrual, TratamientoHormonal, RegistroDiario,
    Recordatorio, EfectoTratamiento, Articulo, Mascota, Notificacion
)

# Configuración inicial
NUM_USUARIOS = 50
NUM_ARTICULOS = 30
FECHA_INICIO = (timezone.now() - timedelta(days=365)).date()
FECHA_FIN = timezone.now().date()

# Listas de nombres y apellidos para generar usuarios
NOMBRES = ['Ana', 'María', 'Sofía', 'Laura', 'Elena', 'Carmen', 'Isabel', 'Patricia', 'Lucía', 'Paula',
           'Andrea', 'Claudia', 'Sara', 'Julia', 'Valeria', 'Martina', 'Alba', 'Noa', 'Vega', 'Daniela',
           'Alex', 'Sam', 'Taylor', 'Jordan', 'Casey', 'Jamie', 'Riley', 'Quinn', 'Avery', 'Peyton']
APELLIDOS = ['García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez', 'Pérez',
             'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno', 'Álvarez', 'Muñoz',
             'Romero', 'Alonso', 'Gutiérrez', 'Navarro', 'Torres', 'Domínguez', 'Vázquez', 'Ramos',
             'Gil', 'Ramírez', 'Serrano', 'Blanco', 'Suárez']


# Función para generar fechas aleatorias
def random_date(start, end):
    """Genera una fecha aleatoria entre start y end (ambos objetos date)"""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


# Crear usuarios y perfiles
def crear_usuarios_y_perfiles():
    print("Creando usuarios y perfiles...")
    usuarios = []

    for i in range(NUM_USUARIOS):
        # Generar datos aleatorios
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        username = f"{nombre.lower()}{apellido.lower()}{random.randint(1, 99)}"
        email = f"{username}@example.com"
        fecha_nacimiento = random_date(
            datetime(1970, 1, 1).date(),
            datetime(2005, 12, 31).date()
        )

        # Elegir género y tipo de seguimiento
        genero = random.choice([
            Perfil.Genero.FEMENINO,
            Perfil.Genero.MASCULINO_TRANS,
            Perfil.Genero.FEMENINO_TRANS
        ])

        # Crear usuario
        user = User.objects.create(
            username=username,
            first_name=nombre,
            last_name=apellido,
            email=email,
            password=make_password('password123')
        )

        # Crear perfil
        perfil = Perfil.objects.create(
            usuario=user,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            es_premium=random.choice([True, False]),
            tipo_perfil=random.choice([
                Perfil.TipoPerfil.USUARIO,
                Perfil.TipoPerfil.AUTOR,
                Perfil.TipoPerfil.ADMIN
            ]),
            tipo_seguimiento=Perfil.TipoSeguimiento.MENSTRUAL if genero in [
                Perfil.Genero.FEMENINO, Perfil.Genero.MASCULINO_TRANS
            ] else Perfil.TipoSeguimiento.HORMONAL,
            duracion_ciclo_promedio=random.randint(25, 35) if genero in [
                Perfil.Genero.FEMENINO, Perfil.Genero.MASCULINO_TRANS
            ] else None,
            duracion_periodo_promedio=random.randint(3, 7) if genero in [
                Perfil.Genero.FEMENINO, Perfil.Genero.MASCULINO_TRANS
            ] else None
        )

        usuarios.append(user)
        print(f"Creado usuario: {username}")

    return usuarios


def crear_ciclos_menstruales(usuarios):
    print("Creando ciclos menstruales...")
    ciclos = []

    for user in usuarios:
        perfil = user.perfil
        if perfil.tipo_seguimiento != Perfil.TipoSeguimiento.MENSTRUAL:
            continue

        # Usar directamente FECHA_INICIO que ahora es date
        fecha_actual = FECHA_INICIO

        while fecha_actual < FECHA_FIN:
            duracion_ciclo = random.randint(
                perfil.duracion_ciclo_promedio - 3,
                perfil.duracion_ciclo_promedio + 3
            )
            fecha_fin = fecha_actual + timedelta(days=duracion_ciclo - 1)

            ciclo = CicloMenstrual.objects.create(
                usuario=user,
                fecha_inicio=fecha_actual,
                fecha_fin=fecha_fin,
                notas=random.choice([
                    "Ciclo normal",
                    "Algo de dolor",
                    "Sin síntomas importantes",
                    "Flujo abundante",
                    "Ciclo más corto de lo normal",
                    ""
                ])
            )
            ciclos.append(ciclo)

            # Avanzar al siguiente ciclo
            fecha_actual = fecha_fin + timedelta(days=1)

    return ciclos


# Crear tratamientos hormonales
def crear_tratamientos_hormonales(usuarios):
    print("Creando tratamientos hormonales...")
    tratamientos = []

    for user in usuarios:
        perfil = user.perfil
        if perfil.tipo_seguimiento != Perfil.TipoSeguimiento.HORMONAL:
            continue

        # Crear 1-3 tratamientos por usuario
        for _ in range(random.randint(1, 3)):
            fecha_inicio = random_date(
                FECHA_INICIO,
                FECHA_FIN - timedelta(days=90)
            )
            fecha_fin = random_date(
                fecha_inicio + timedelta(days=30),
                min(fecha_inicio + timedelta(days=365), FECHA_FIN)
            ) if random.choice([True, False]) else None

            tratamiento = TratamientoHormonal.objects.create(
                usuario=user,
                nombre_tratamiento=random.choice([
                    "Terapia de estrógenos",
                    "Bloqueadores de testosterona",
                    "Progesterona micronizada",
                    "Testosterona inyectable",
                    "Parches de estradiol",
                    "Gel de testosterona"
                ]),
                tipo_hormona=random.choice([
                    TratamientoHormonal.TipoHormona.ESTROGENO,
                    TratamientoHormonal.TipoHormona.PROGESTERONA,
                    TratamientoHormonal.TipoHormona.TESTOSTERONA,
                    TratamientoHormonal.TipoHormona.COMBINADO
                ]),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                dosis=random.uniform(0.5, 5.0),
                frecuencia=random.randint(1, 3),
                frecuencia_tipo=random.choice(['diario', 'semanal']),
                activo=fecha_fin is None or fecha_fin > timezone.now().date(),
                notas=random.choice([
                    "Buena tolerancia",
                    "Algunos efectos secundarios",
                    "Resultados visibles",
                    "Ajustar dosis si es necesario",
                    ""
                ])
            )
            tratamientos.append(tratamiento)

    return tratamientos


# Crear efectos de tratamientos
def crear_efectos_tratamientos(tratamientos):
    print("Creando efectos de tratamientos...")
    efectos = []

    efectos_posibles = [
        ('aumento_energia', 'fisico', 'deseado'),
        ('cambios_humor', 'emocional', 'secundario'),
        ('sensibilidad_pechos', 'fisico', 'secundario'),
        ('nauseas', 'fisico', 'secundario'),
        ('aumento_peso', 'fisico', 'secundario'),
        ('dolor_cabeza', 'fisico', 'secundario'),
        ('sofocos', 'fisico', 'secundario'),
        ('libido_aumentada', 'emocional', 'deseado'),
        ('libido_disminuida', 'emocional', 'secundario')
    ]

    for tratamiento in tratamientos:
        # Crear 2-5 efectos por tratamiento
        for _ in range(random.randint(2, 5)):
            efecto_data = random.choice(efectos_posibles)
            fecha_inicio = random_date(
                tratamiento.fecha_inicio,
                tratamiento.fecha_fin if tratamiento.fecha_fin else FECHA_FIN
            )
            fecha_fin = random_date(
                fecha_inicio,
                tratamiento.fecha_fin if tratamiento.fecha_fin else FECHA_FIN
            ) if random.choice([True, False]) else None

            efecto = EfectoTratamiento.objects.create(
                usuario=tratamiento.usuario,
                tratamiento=tratamiento,
                nombre_efecto=efecto_data[0],
                tipo_efecto=efecto_data[1],
                descripcion=random.choice([
                    "Efecto notable",
                    "Leve molestia",
                    "Impacto significativo",
                    "Poco perceptible",
                    "Varía con el tiempo"
                ]),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                intensidad=random.randint(1, 5),
                notas=random.choice([
                    "Consultar con médico",
                    "Monitorizar cambios",
                    "Posible ajuste de dosis",
                    ""
                ])
            )
            efectos.append(efecto)

    return efectos


def crear_registros_diarios(usuarios, ciclos, tratamientos):
    print("Creando registros diarios...")
    registros = []
    max_intentos = 5  # Máximo de intentos para encontrar fecha única por usuario

    for user in usuarios:
        perfil = user.perfil
        dias_a_crear = random.randint(30, 180)  # Entre 1 y 6 meses de registros
        fechas_usadas = set()  # Para trackear fechas ya usadas para este usuario

        # Determinar el ciclo activo para usuarios con seguimiento menstrual
        ciclo_activo = None
        if perfil.tipo_seguimiento == Perfil.TipoSeguimiento.MENSTRUAL:
            ciclo_activo = CicloMenstrual.objects.filter(
                usuario=user,
                fecha_inicio__lte=FECHA_FIN,
                fecha_fin__gte=FECHA_INICIO
            ).first()

        for _ in range(dias_a_crear):
            # Buscar una fecha única para este usuario
            intentos = 0
            while intentos < max_intentos:
                fecha = random_date(FECHA_INICIO, FECHA_FIN)
                if (fecha not in fechas_usadas and
                        not RegistroDiario.objects.filter(usuario=user, fecha=fecha).exists()):
                    fechas_usadas.add(fecha)
                    break
                intentos += 1
            else:
                continue  # Saltar si no encontramos fecha única después de max_intentos

            # Crear el registro base
            registro_data = {
                'usuario': user,
                'fecha': fecha,
                'estados_animo': random.sample([
                    'feliz', 'triste', 'irritable', 'ansioso', 'neutral', 'cansado', 'energico'
                ], random.randint(1, 3)),
                'sintomas_comunes': random.sample([
                    'dolor_cabeza', 'dolor_espalda', 'fatiga', 'cambios_apetito', 'insomnio'
                ], random.randint(0, 2)),
                'notas': random.choice([
                    "Día normal", "Algo de estrés", "Buen día en general",
                    "Problemas para dormir", "Más energía de lo habitual", ""
                ])
            }

            # Campos específicos según tipo de seguimiento
            if perfil.tipo_seguimiento == Perfil.TipoSeguimiento.MENSTRUAL and ciclo_activo:
                registro_data.update({
                    'ciclo': ciclo_activo,
                    'es_dia_periodo': random.choice([True, False]),
                    'senos_sensibles': random.choice([True, False]),
                    'retencion_liquidos': random.choice([True, False]),
                    'antojos': random.choice([True, False]),
                    'acne': random.choice([True, False])
                })

                if registro_data['es_dia_periodo']:
                    registro_data.update({
                        'flujo_menstrual': random.choice([
                            'nulo', 'ligero', 'moderado', 'abundante', 'muy_abundante'
                        ]),
                        'coagulos': random.choice([True, False]),
                        'color_flujo': random.choice(['rojo', 'oscuro', 'marron', 'rosado'])
                    })

            elif perfil.tipo_seguimiento == Perfil.TipoSeguimiento.HORMONAL:
                tratamiento_activo = TratamientoHormonal.objects.filter(
                    usuario=user,
                    fecha_inicio__lte=fecha,
                    fecha_fin__gte=fecha if fecha else True
                ).first()

                if tratamiento_activo:
                    registro_data.update({
                        'tratamiento': tratamiento_activo,
                        'medicacion_tomada': random.choice([True, False]),
                        'sensibilidad_pezon': random.choice([True, False]),
                        'cambios_libido': random.choice(['aumento', 'disminucion', 'normal', None]),
                        'sofocos': random.choice([True, False]),
                        'cambios_piel': random.choice(["Piel más seca", "Piel más grasa", "Mejoría del acné", ""]),
                        'crecimiento_mamario': random.choice([True, False])
                    })

                    if registro_data['medicacion_tomada']:
                        registro_data['hora_medicacion'] = datetime.strptime(
                            f"{random.randint(8, 22)}:{random.randint(0, 59)}", "%H:%M"
                        ).time()

            # Crear el registro usando get_or_create para mayor seguridad
            registro, created = RegistroDiario.objects.get_or_create(
                usuario=user,
                fecha=fecha,
                defaults=registro_data
            )

            if created:
                registros.append(registro)
            else:
                # Si por alguna razón ya existía, actualizamos los campos
                for key, value in registro_data.items():
                    if key not in ['usuario', 'fecha']:  # No actualizamos estos campos
                        setattr(registro, key, value)
                registro.save()
                registros.append(registro)

    return registros


# Crear recordatorios
def crear_recordatorios(usuarios):
    print("Creando recordatorios...")
    recordatorios = []

    for user in usuarios:
        # Crear 3-8 recordatorios por usuario
        for _ in range(random.randint(3, 8)):
            fecha_inicio = random_date(FECHA_INICIO, FECHA_FIN)

            recordatorio = Recordatorio.objects.create(
                usuario=user,
                titulo=random.choice([
                    "Tomar medicación",
                    "Cita con endocrino",
                    "Revisar síntomas",
                    "Comprar suministros",
                    "Ejercicio diario",
                    "Registro diario",
                    "Control de peso"
                ]),
                descripcion=random.choice([
                    "No olvidar tomar con comida",
                    "Llevar informes médicos",
                    "Anotar cualquier síntoma nuevo",
                    "Comprar en la farmacia de siempre",
                    "30 minutos de ejercicio",
                    "Completar antes de dormir",
                    ""
                ]),
                tipo=random.choice([
                    'medicacion', 'medicacion_hormonal', 'cita_medica', 'otro'
                ]),
                fecha_inicio=fecha_inicio,
                hora=datetime.strptime(
                    f"{random.randint(8, 22)}:{random.randint(0, 59)}", "%H:%M"
                ).time(),
                dias_frecuencia=random.choice([0, 1, 7, 30]),
                activo=random.choice([True, False]),
                notificar=random.choice([True, False]),
                dias_antelacion=random.randint(1, 3),
                visto=random.choice([True, False])
            )
            recordatorios.append(recordatorio)

    return recordatorios


# Crear artículos
def crear_articulos(usuarios):
    print("Creando artículos...")
    articulos = []
    autores = [user for user in usuarios if user.perfil.tipo_perfil in ['autor', 'administracion']]

    for _ in range(NUM_ARTICULOS):
        autor = random.choice(autores)
        fecha_publicacion = random_date(FECHA_INICIO, FECHA_FIN) if random.choice([True, False]) else None

        articulo = Articulo.objects.create(
            autor=autor,
            titulo=random.choice([
                "Consejos para manejar el síndrome premenstrual",
                "Guía completa sobre tratamientos hormonales",
                "Cómo llevar un registro menstrual efectivo",
                "Los beneficios del ejercicio durante el ciclo",
                "Mitos y verdades sobre la terapia hormonal",
                "Alimentación y ciclo menstrual",
                "Cambios emocionales durante la transición",
                "Cómo hablar con tu médico sobre tus síntomas",
                "Técnicas de relajación para días difíciles",
                "Historias reales: mi experiencia con la terapia"
            ]),
            contenido="\n\n".join([
                "Este es un párrafo introductorio sobre el tema.",
                "Aquí se desarrolla el contenido principal con más detalles.",
                "Finalmente, se concluye con recomendaciones prácticas."
            ]),
            estado='publicado' if fecha_publicacion else random.choice(['borrador', 'publicado', 'archivado']),
            categoria=random.choice([
                'salud_menstrual',
                'tratamientos_hormonales',
                'bienestar',
                'consejos',
                'investigacion',
                'historias'
            ]),
            fecha_publicacion=fecha_publicacion,
            destacado=random.choice([True, False])
        )
        articulos.append(articulo)

    return articulos


# Crear mascotas
def crear_mascotas(usuarios):
    print("Creando mascotas...")
    mascotas = []

    for user in usuarios:
        mascota = Mascota.objects.create(
            usuario=user,
            estado=random.choice(['normal', 'hambrienta', 'feliz']),
            nivel_hambre=random.randint(0, 100),
            ultimo_cambio_estado=random_date(FECHA_INICIO, FECHA_FIN)
        )
        mascotas.append(mascota)

    return mascotas


# Crear notificaciones
def crear_notificaciones(usuarios, recordatorios):
    print("Creando notificaciones...")
    notificaciones = []

    for user in usuarios:
        user_recordatorios = [r for r in recordatorios if r.usuario == user]

        for _ in range(random.randint(2, 10)):
            recordatorio = random.choice(user_recordatorios)

            notificacion = Notificacion.objects.create(
                usuario=user,
                recordatorio=recordatorio,
                mensaje=random.choice([
                    f"Recordatorio: {recordatorio.titulo}",
                    f"No olvides: {recordatorio.titulo}",
                    f"Próximo evento: {recordatorio.titulo}",
                    f"Tienes pendiente: {recordatorio.titulo}"
                ]),
                leida=random.choice([True, False])
            )
            notificaciones.append(notificacion)

    return notificaciones


# Función principal para poblar la base de datos
def poblar_base_datos():
    print("Iniciando poblamiento de la base de datos...")

    # Limpiar datos existentes (opcional, ten cuidado)
    # print("Eliminando datos existentes...")
    # User.objects.all().delete()

    # Crear datos
    usuarios = crear_usuarios_y_perfiles()
    ciclos = crear_ciclos_menstruales(usuarios)
    tratamientos = crear_tratamientos_hormonales(usuarios)
    efectos = crear_efectos_tratamientos(tratamientos)
    registros = crear_registros_diarios(usuarios, ciclos, tratamientos)
    recordatorios = crear_recordatorios(usuarios)
    articulos = crear_articulos(usuarios)
    mascotas = crear_mascotas(usuarios)
    notificaciones = crear_notificaciones(usuarios, recordatorios)

    print("\nResumen de datos creados:")
    print(f"- Usuarios: {len(usuarios)}")
    print(f"- Perfiles: {len(usuarios)}")
    print(f"- Ciclos menstruales: {len(ciclos)}")
    print(f"- Tratamientos hormonales: {len(tratamientos)}")
    print(f"- Efectos de tratamientos: {len(efectos)}")
    print(f"- Registros diarios: {len(registros)}")
    print(f"- Recordatorios: {len(recordatorios)}")
    print(f"- Artículos: {len(articulos)}")
    print(f"- Mascotas: {len(mascotas)}")
    print(f"- Notificaciones: {len(notificaciones)}")

    print("\n¡Base de datos poblada exitosamente!")


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba'

    def handle(self, *args, **options):
        poblar_base_datos()
        self.stdout.write(self.style.SUCCESS('Base de datos poblada exitosamente!'))