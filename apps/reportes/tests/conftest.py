import datetime

import pytest
from django.utils import timezone

from apps.acceso.models import PerfilEstudiante, Usuario
from apps.configuracion.models import FormularioSocioeconomico
from apps.convocatorias.models import Beca, Convocatoria, TipoDocumento


@pytest.fixture
def director(db):
    return Usuario.objects.create_superuser(email="dir@test.com", password="pass")


@pytest.fixture
def beca(db):
    return Beca.objects.create(nombre="Beca Test", activa=True)


@pytest.fixture
def convocatoria(db, director, beca):
    c = Convocatoria.objects.create(
        nombre="Conv Test",
        fecha_apertura=timezone.now() - datetime.timedelta(days=5),
        fecha_cierre=timezone.now() + datetime.timedelta(days=30),
        estado=Convocatoria.Estado.PUBLICADA,
        creada_por=director,
    )
    c.becas.add(beca)
    return c


@pytest.fixture
def tipo_documento(db):
    return TipoDocumento.objects.create(nombre="Cédula de Identidad", activo=True)


@pytest.fixture
def crear_estudiante(db):
    """Factory fixture: crea un Usuario + FormularioSocioeconomico con valores razonables."""
    contador = {"n": 0}

    def _crear(
        *,
        familiares=3,
        rango_ingreso=None,
        beca_previa=False,
        carrera=None,
        anio_ingreso=None,
        **extra_formulario,
    ):
        contador["n"] += 1
        n = contador["n"]
        usuario = Usuario.objects.create_user(
            email=f"estudiante{n}@test.com", password="pass", first_name="Ana", last_name=f"Test{n}"
        )
        if carrera is not None or anio_ingreso is not None:
            import datetime

            PerfilEstudiante.objects.create(
                usuario=usuario,
                nro_registro=f"{anio_ingreso or 2020}{n:05d}",
                carrera=carrera or "Ingeniería de Sistemas",
                anio_ingreso=anio_ingreso or 2020,
                fecha_nacimiento=datetime.date(2000, 1, 1),
            )
        formulario = FormularioSocioeconomico.objects.create(
            usuario=usuario,
            cantidad_familiares=familiares,
            rango_ingreso=rango_ingreso,
            tiene_beca_previa=beca_previa,
            completado=True,
            **extra_formulario,
        )
        return usuario, formulario

    return _crear
