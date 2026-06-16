from django.contrib.auth.hashers import make_password
from django.db import migrations

NOMBRES = [
    "Lucía", "Martín", "Valentina", "Santiago", "Camila",
    "Nicolás", "Sofía", "Agustín", "Florencia", "Tomás",
]

APELLIDOS = [
    "González", "Rodríguez", "Fernández", "López", "Martínez",
    "Pérez", "García", "Sánchez", "Romero", "Torres",
]

CARRERAS = [
    "Ingeniería Informática",
    "Licenciatura en Sistemas",
    "Ingeniería Electrónica",
    "Ingeniería Industrial",
    "Licenciatura en Matemática",
]

ANIOS_INGRESO = [2020, 2021, 2022, 2023, 2024]

PASSWORD = make_password("estudiante123")


def crear_estudiantes(apps, schema_editor):
    Usuario = apps.get_model("acceso", "Usuario")
    PerfilEstudiante = apps.get_model("acceso", "PerfilEstudiante")
    Group = apps.get_model("auth", "Group")

    grupo_est, _ = Group.objects.get_or_create(name="Estudiante")

    usuarios_nuevos = []
    for i in range(4, 104):
        email = f"estudiante{i:03d}@becas.com"
        if Usuario.objects.filter(email=email).exists():
            continue

        idx = i - 4  # 0-based index dentro del lote
        nombre = NOMBRES[idx % len(NOMBRES)]
        apellido = APELLIDOS[(idx // len(NOMBRES)) % len(APELLIDOS)]

        usuario = Usuario(
            email=email,
            first_name=nombre,
            last_name=apellido,
            password=PASSWORD,
            is_active=True,
        )
        usuarios_nuevos.append(usuario)

    creados = Usuario.objects.bulk_create(usuarios_nuevos)

    # Perfiles y grupo (bulk_create no dispara signals, los hacemos manualmente)
    perfiles = []
    for i, usuario in enumerate(creados):
        idx = i  # ya es 0-based respecto al lote creado
        num_global = idx + 4
        perfiles.append(
            PerfilEstudiante(
                usuario=usuario,
                legajo=f"EST-{num_global:04d}",
                carrera=CARRERAS[idx % len(CARRERAS)],
                anio_ingreso=ANIOS_INGRESO[idx % len(ANIOS_INGRESO)],
            )
        )

    PerfilEstudiante.objects.bulk_create(perfiles)

    # Asignar grupo (M2M, no soporta bulk_create directamente)
    grupo_est.user_set.add(*creados)


def eliminar_estudiantes(apps, schema_editor):
    Usuario = apps.get_model("acceso", "Usuario")
    emails = [f"estudiante{i:03d}@becas.com" for i in range(4, 104)]
    Usuario.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("acceso", "0003_crear_grupos"),
    ]

    operations = [
        migrations.RunPython(crear_estudiantes, eliminar_estudiantes),
    ]
