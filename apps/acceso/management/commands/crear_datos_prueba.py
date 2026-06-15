from django.core.management.base import BaseCommand

from apps.acceso.models import Usuario
from apps.acceso.services import autorregistrar_estudiante
from apps.usuarios.services import registrar_usuario

USUARIOS_PRUEBA = [
    {
        "rol": "Director",
        "email": "director@becas.com",
        "first_name": "Carlos",
        "last_name": "Mendoza",
        "password": "director123",
    },
    {
        "rol": "Operador",
        "email": "operador@becas.com",
        "first_name": "Laura",
        "last_name": "Suárez",
        "password": "operador123",
    },
]

ESTUDIANTES_PRUEBA = [
    {
        "email": "estudiante1@becas.com",
        "first_name": "Ana",
        "last_name": "García",
        "password1": "estudiante123",
        "password2": "estudiante123",
        "legajo": "EST-001",
        "carrera": "Ingeniería Informática",
        "anio_ingreso": 2022,
    },
    {
        "email": "estudiante2@becas.com",
        "first_name": "Martín",
        "last_name": "López",
        "password1": "estudiante123",
        "password2": "estudiante123",
        "legajo": "EST-002",
        "carrera": "Licenciatura en Sistemas",
        "anio_ingreso": 2021,
    },
    {
        "email": "estudiante3@becas.com",
        "first_name": "Valentina",
        "last_name": "Ríos",
        "password1": "estudiante123",
        "password2": "estudiante123",
        "legajo": "EST-003",
        "carrera": "Ingeniería Electrónica",
        "anio_ingreso": 2023,
    },
]


class Command(BaseCommand):
    help = "Crea usuarios de prueba para desarrollo (Director, Operador, Estudiantes)."

    def handle(self, *args, **options):
        self._crear_superuser()
        self._crear_usuarios_internos()
        self._crear_estudiantes()
        self.stdout.write(self.style.SUCCESS("\nDatos de prueba creados exitosamente."))
        self._imprimir_resumen()

    def _crear_superuser(self):
        email = "admin@becas.com"
        if Usuario.objects.filter(email=email).exists():
            self.stdout.write(f"  [omitido] superuser {email} ya existe")
            return
        Usuario.objects.create_superuser(email=email, password="admin123")
        self.stdout.write(self.style.SUCCESS(f"  [creado]  superuser {email}"))

    def _crear_usuarios_internos(self):
        for datos in USUARIOS_PRUEBA:
            email = datos["email"]
            if Usuario.objects.filter(email=email).exists():
                self.stdout.write(f'  [omitido] {datos["rol"]} {email} ya existe')
                continue
            usuario = registrar_usuario(
                email=email,
                first_name=datos["first_name"],
                last_name=datos["last_name"],
                rol=datos["rol"],
            )
            usuario.set_password(datos["password"])
            usuario.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f'  [creado]  {datos["rol"]} {email}'))

    def _crear_estudiantes(self):
        for datos in ESTUDIANTES_PRUEBA:
            email = datos["email"]
            if Usuario.objects.filter(email=email).exists():
                self.stdout.write(f"  [omitido] Estudiante {email} ya existe")
                continue
            autorregistrar_estudiante(**datos)
            self.stdout.write(self.style.SUCCESS(f"  [creado]  Estudiante {email}"))

    def _imprimir_resumen(self):
        self.stdout.write("\n" + "─" * 50)
        self.stdout.write("  Credenciales de acceso:")
        self.stdout.write("─" * 50)
        self.stdout.write("  Superuser  → admin@becas.com        / admin123")
        self.stdout.write("  Director   → director@becas.com     / director123")
        self.stdout.write("  Operador   → operador@becas.com     / operador123")
        self.stdout.write("  Estudiante → estudiante1@becas.com  / estudiante123")
        self.stdout.write("  Estudiante → estudiante2@becas.com  / estudiante123")
        self.stdout.write("  Estudiante → estudiante3@becas.com  / estudiante123")
        self.stdout.write("─" * 50)
