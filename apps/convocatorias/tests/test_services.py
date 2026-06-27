import pytest
from django.utils import timezone

from apps.acceso.models import Usuario
from apps.convocatorias.exceptions import (
    ConvocatoriaNoModificableError,
    ConvocatoriaYaCerradaError,
    FechaInvalidaError,
    NombreDuplicadoError,
    PonderacionInvalidaError,
)
from apps.convocatorias.models import Convocatoria
from apps.convocatorias.services import (
    cerrar_convocatoria,
    cerrar_convocatorias_vencidas,
    crear_beca,
    crear_convocatoria,
    crear_tipo_documento,
    editar_beca,
    editar_convocatoria,
    publicar_convocatoria,
)


@pytest.fixture
def director(db):
    return Usuario.objects.create_user(email="dir@test.com", password="x")


def _fechas(delta_apertura=0, delta_cierre=10):
    now = timezone.now()
    return (
        now + timezone.timedelta(days=delta_apertura),
        now + timezone.timedelta(days=delta_cierre),
    )


def _crear(director, **kwargs):
    apertura, cierre = _fechas()
    defaults = dict(
        nombre="Conv Test",
        descripcion="",
        fecha_apertura=apertura,
        fecha_cierre=cierre,
        becas_ids=[],
        documentos_ids=[],
        creada_por=director,
    )
    defaults.update(kwargs)
    return crear_convocatoria(**defaults)


# ---------------------------------------------------------------------------
# Convocatorias
# ---------------------------------------------------------------------------


def test_crear_convocatoria_exitosa(db, director):
    conv = _crear(director)
    assert conv.pk is not None
    assert conv.estado == Convocatoria.Estado.BORRADOR


def test_crear_convocatoria_fechas_invalidas(db, director):
    apertura, cierre = _fechas()
    with pytest.raises(FechaInvalidaError):
        crear_convocatoria(
            nombre="X",
            descripcion="",
            fecha_apertura=cierre,
            fecha_cierre=apertura,
            becas_ids=[],
            documentos_ids=[],
            creada_por=director,
        )


def test_publicar_convocatoria(db, director):
    conv = _crear(director)
    publicar_convocatoria(convocatoria=conv)
    assert conv.estado == Convocatoria.Estado.PUBLICADA


def test_no_editar_convocatoria_publicada(db, director):
    conv = _crear(director)
    publicar_convocatoria(convocatoria=conv)
    apertura, cierre = _fechas()
    with pytest.raises(ConvocatoriaNoModificableError):
        editar_convocatoria(
            convocatoria=conv,
            nombre="Nuevo",
            descripcion="",
            fecha_apertura=apertura,
            fecha_cierre=cierre,
            becas_ids=[],
            documentos_ids=[],
        )


def test_cerrar_convocatoria(db, director):
    conv = _crear(director)
    publicar_convocatoria(convocatoria=conv)
    cerrar_convocatoria(convocatoria=conv)
    assert conv.estado == Convocatoria.Estado.CERRADA


def test_cerrar_convocatoria_ya_cerrada(db, director):
    conv = _crear(director)
    cerrar_convocatoria(convocatoria=conv)
    with pytest.raises(ConvocatoriaYaCerradaError):
        cerrar_convocatoria(convocatoria=conv)


def test_cerrar_convocatorias_vencidas(db, director):
    apertura, _ = _fechas(delta_apertura=-5)
    cierre_pasado = timezone.now() - timezone.timedelta(hours=1)
    conv = crear_convocatoria(
        nombre="Vencida",
        descripcion="",
        fecha_apertura=apertura,
        fecha_cierre=cierre_pasado,
        becas_ids=[],
        documentos_ids=[],
        creada_por=director,
    )
    publicar_convocatoria(convocatoria=conv)
    count = cerrar_convocatorias_vencidas()
    assert count == 1
    conv.refresh_from_db()
    assert conv.estado == Convocatoria.Estado.CERRADA


# ---------------------------------------------------------------------------
# Becas
# ---------------------------------------------------------------------------


def test_crear_beca(db):
    beca = crear_beca(nombre="Beca Socioeconómica")
    assert beca.pk is not None
    assert beca.activa is True


def test_crear_beca_nombre_duplicado(db):
    crear_beca(nombre="Única")
    with pytest.raises(NombreDuplicadoError):
        crear_beca(nombre="Única")


def test_editar_beca(db):
    beca = crear_beca(nombre="Original")
    editar_beca(beca=beca, nombre="Modificada", descripcion="Desc", activa=False)
    assert beca.nombre == "Modificada"
    assert beca.activa is False


def test_crear_beca_pesos_personalizados(db):
    beca = crear_beca(
        nombre="Beca Pesos",
        peso_dependencia_economica=40,
        peso_grupo_familiar=20,
        peso_procedencia=5,
        peso_tenencia_vivienda=15,
        peso_infraestructura=10,
        peso_otro_beneficio=5,
        peso_discapacidad=5,
    )
    assert beca.peso_dependencia_economica == 40
    assert beca.peso_grupo_familiar == 20


def test_crear_beca_pesos_no_suman_100(db):
    with pytest.raises(PonderacionInvalidaError):
        crear_beca(
            nombre="Beca Inválida",
            peso_dependencia_economica=50,
            peso_grupo_familiar=20,
        )


def test_editar_beca_pesos_no_suman_100(db):
    beca = crear_beca(nombre="Otra Beca")
    with pytest.raises(PonderacionInvalidaError):
        editar_beca(
            beca=beca,
            nombre="Otra Beca",
            descripcion="",
            activa=True,
            peso_dependencia_economica=90,
            peso_grupo_familiar=90,
        )


# ---------------------------------------------------------------------------
# Tipos de documento
# ---------------------------------------------------------------------------


def test_crear_tipo_documento(db):
    tipo = crear_tipo_documento(nombre="DNI")
    assert tipo.pk is not None


def test_crear_tipo_documento_duplicado(db):
    crear_tipo_documento(nombre="DNI")
    with pytest.raises(NombreDuplicadoError):
        crear_tipo_documento(nombre="DNI")
