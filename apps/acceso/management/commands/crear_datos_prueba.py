from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.acceso.models import Usuario
from apps.acceso.services import autorregistrar_estudiante
from apps.configuracion.models import FormularioSocioeconomico
from apps.convocatorias.models import Beca, Convocatoria, TipoDocumento
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
        "nro_registro": "EST-001",
        "carrera": "Ingeniería Informática",
        "anio_ingreso": 2022,
    },
    {
        "email": "estudiante2@becas.com",
        "first_name": "Martín",
        "last_name": "López",
        "password1": "estudiante123",
        "password2": "estudiante123",
        "nro_registro": "EST-002",
        "carrera": "Licenciatura en Sistemas",
        "anio_ingreso": 2021,
    },
    {
        "email": "estudiante3@becas.com",
        "first_name": "Valentina",
        "last_name": "Ríos",
        "password1": "estudiante123",
        "password2": "estudiante123",
        "nro_registro": "EST-003",
        "carrera": "Ingeniería Electrónica",
        "anio_ingreso": 2023,
    },
]


class Command(BaseCommand):
    help = "Crea usuarios, catálogos y datos de prueba para desarrollo."

    def handle(self, *args, **options):
        self._crear_superuser()
        self._crear_usuarios_internos()
        self._crear_estudiantes()
        becas = self._crear_becas()
        tipos_doc = self._crear_tipos_documento()
        self._crear_convocatorias(becas, tipos_doc)
        self._crear_formularios()
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

    def _crear_becas(self):
        definiciones = [
            ("Beca Excelencia Académica", "Para estudiantes con promedio superior a 8."),
            ("Beca Socioeconómica", "Para estudiantes en situación de vulnerabilidad económica."),
            ("Beca de Transporte", "Subsidio de movilidad para estudiantes de zonas alejadas."),
        ]
        becas = []
        for nombre, desc in definiciones:
            beca, created = Beca.objects.get_or_create(
                nombre=nombre, defaults={"descripcion": desc}
            )
            estado = "[creada]" if created else "[existía]"
            self.stdout.write(f"  {estado}  Beca: {nombre}")
            becas.append(beca)
        return becas

    def _crear_tipos_documento(self):
        definiciones = [
            ("DNI (frente y dorso)", "Documento Nacional de Identidad, ambas caras."),
            ("Certificado de ingresos familiares", "Recibo de sueldo o constancia de AFIP."),
            ("Certificado de regularidad", "Emitido por la oficina de alumnos."),
            ("Declaración jurada de domicilio", "Formulario provisto por la institución."),
        ]
        tipos = []
        for nombre, desc in definiciones:
            tipo, created = TipoDocumento.objects.get_or_create(
                nombre=nombre, defaults={"descripcion": desc}
            )
            estado = "[creado]" if created else "[existía]"
            self.stdout.write(f"  {estado}  TipoDocumento: {nombre}")
            tipos.append(tipo)
        return tipos

    def _crear_convocatorias(self, becas, tipos_doc):
        director = Usuario.objects.filter(email="director@becas.com").first()
        if not director:
            self.stdout.write("  [omitido] convocatorias (director no existe aún)")
            return

        ahora = timezone.now()

        convocatorias_def = [
            {
                "nombre": "Convocatoria Becas 2026 — Primer Semestre",
                "descripcion": "Convocatoria vigente para el primer semestre 2026.",
                "fecha_apertura": ahora.replace(month=1, day=1),
                "fecha_cierre": ahora.replace(month=12, day=31),
                "estado": Convocatoria.Estado.PUBLICADA,
                "becas": becas[:2],
                "docs": tipos_doc[:3],
            },
            {
                "nombre": "Convocatoria Becas de Transporte 2026",
                "descripcion": "Subsidio de movilidad anual.",
                "fecha_apertura": ahora.replace(month=3, day=1),
                "fecha_cierre": ahora.replace(month=11, day=30),
                "estado": Convocatoria.Estado.PUBLICADA,
                "becas": [becas[2]],
                "docs": tipos_doc[:1],
            },
        ]

        for defn in convocatorias_def:
            if Convocatoria.objects.filter(nombre=defn["nombre"]).exists():
                self.stdout.write(f"  [omitida] Convocatoria: {defn['nombre']}")
                continue
            c = Convocatoria.objects.create(
                nombre=defn["nombre"],
                descripcion=defn["descripcion"],
                fecha_apertura=defn["fecha_apertura"],
                fecha_cierre=defn["fecha_cierre"],
                estado=defn["estado"],
                creada_por=director,
            )
            c.becas.set(defn["becas"])
            c.documentos_requeridos.set(defn["docs"])
            self.stdout.write(self.style.SUCCESS(f"  [creada]  Convocatoria: {defn['nombre']}"))

    def _crear_formularios(self):
        formularios_def = [
            {
                "email": "estudiante1@becas.com",
                "situacion_laboral": FormularioSocioeconomico.SituacionLaboral.DESEMPLEADO,
                "ingreso_mensual_familiar": Decimal("45000"),
                "cantidad_familiares": 4,
                "situacion_habitacional": FormularioSocioeconomico.SituacionHabitacional.ALQUILANDO,
                "tiene_beca_previa": False,
            },
            {
                "email": "estudiante2@becas.com",
                "situacion_laboral": FormularioSocioeconomico.SituacionLaboral.EMPLEADO,
                "ingreso_mensual_familiar": Decimal("120000"),
                "cantidad_familiares": 2,
                "situacion_habitacional": FormularioSocioeconomico.SituacionHabitacional.PROPIETARIO,
                "tiene_beca_previa": True,
            },
        ]
        for defn in formularios_def:
            usuario = Usuario.objects.filter(email=defn["email"]).first()
            if not usuario:
                continue
            if FormularioSocioeconomico.objects.filter(usuario=usuario).exists():
                self.stdout.write(f"  [omitido] Formulario de {defn['email']}")
                continue
            FormularioSocioeconomico.objects.create(
                usuario=usuario,
                situacion_laboral=defn["situacion_laboral"],
                ingreso_mensual_familiar=defn["ingreso_mensual_familiar"],
                cantidad_familiares=defn["cantidad_familiares"],
                situacion_habitacional=defn["situacion_habitacional"],
                tiene_beca_previa=defn["tiene_beca_previa"],
                completado=True,
            )
            self.stdout.write(self.style.SUCCESS(f"  [creado]  Formulario de {defn['email']}"))

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
