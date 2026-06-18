from django.contrib.auth.hashers import make_password
from django.db import migrations

PASSWORD_ADMIN = make_password("admin123")
PASSWORD_DIRECTOR = make_password("director123")
PASSWORD_OPERADOR = make_password("operador123")

ADMIN = {"email": "admin@becas.com", "first_name": "Admin", "last_name": "Sistema"}

DIRECTORES = [
    {"email": "director@becas.com", "first_name": "Carlos", "last_name": "Mendoza"},
    {"email": "director2@becas.com", "first_name": "Patricia", "last_name": "Salazar"},
]

OPERADORES = [
    {"email": "operador@becas.com", "first_name": "Laura", "last_name": "Suárez"},
    {"email": "operador2@becas.com", "first_name": "Jorge", "last_name": "Quispe"},
    {"email": "operador3@becas.com", "first_name": "Daniela", "last_name": "Flores"},
    {"email": "operador4@becas.com", "first_name": "Ricardo", "last_name": "Vargas"},
    {"email": "operador5@becas.com", "first_name": "Mariana", "last_name": "Choque"},
    {"email": "operador6@becas.com", "first_name": "Sebastián", "last_name": "Mamani"},
    {"email": "operador7@becas.com", "first_name": "Carolina", "last_name": "Rojas"},
    {"email": "operador8@becas.com", "first_name": "Fernando", "last_name": "Paredes"},
    {"email": "operador9@becas.com", "first_name": "Gabriela", "last_name": "Aguilar"},
    {"email": "operador10@becas.com", "first_name": "Pablo", "last_name": "Cardozo"},
]


def crear_usuarios_internos(apps, schema_editor):
    Usuario = apps.get_model("acceso", "Usuario")
    Group = apps.get_model("auth", "Group")

    grupo_director = Group.objects.get(name="Director")
    grupo_operador = Group.objects.get(name="Operador")

    Usuario.objects.get_or_create(
        email=ADMIN["email"],
        defaults={
            "first_name": ADMIN["first_name"],
            "last_name": ADMIN["last_name"],
            "password": PASSWORD_ADMIN,
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
        },
    )

    for datos in DIRECTORES:
        usuario, _ = Usuario.objects.get_or_create(
            email=datos["email"],
            defaults={
                "first_name": datos["first_name"],
                "last_name": datos["last_name"],
                "password": PASSWORD_DIRECTOR,
                "is_active": True,
            },
        )
        usuario.groups.add(grupo_director)

    for datos in OPERADORES:
        usuario, _ = Usuario.objects.get_or_create(
            email=datos["email"],
            defaults={
                "first_name": datos["first_name"],
                "last_name": datos["last_name"],
                "password": PASSWORD_OPERADOR,
                "is_active": True,
            },
        )
        usuario.groups.add(grupo_operador)


def eliminar_usuarios_internos(apps, schema_editor):
    Usuario = apps.get_model("acceso", "Usuario")
    emails = (
        [ADMIN["email"]]
        + [d["email"] for d in DIRECTORES]
        + [o["email"] for o in OPERADORES]
    )
    Usuario.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("acceso", "0004_datos_100_estudiantes"),
    ]

    operations = [
        migrations.RunPython(crear_usuarios_internos, eliminar_usuarios_internos),
    ]
