import pytest

from apps.acceso.models import Usuario
from apps.configuracion.models import FormularioSocioeconomico
from apps.convocatorias.models import Beca, Convocatoria, TipoDocumento
from apps.postulaciones.services import PostulacionService as services
from apps.postulaciones.exceptions import (
    ConstanciaNoDisponibleError,
    ConvocatoriaNoVigenteError,
    DocumentoNoAprobadoError,
    DocumentoNoPendienteError,
    FormularioIncompletoError,
    PostulacionActivaExistenteError,
    TransicionEstadoInvalidaError,
)
from apps.postulaciones.models import DocumentoPostulacion, Postulacion


@pytest.fixture
def superusuario(db):
    return Usuario.objects.create_superuser(email="su@test.com", password="pass")


@pytest.fixture
def estudiante(db):
    return Usuario.objects.create_user(
        email="est@test.com", password="pass", first_name="Ana", last_name="Gómez"
    )


@pytest.fixture
def formulario(db, estudiante):
    return FormularioSocioeconomico.objects.create(
        usuario=estudiante,
        cantidad_familiares=3,
        tiene_beca_previa=False,
        completado=True,
    )


@pytest.fixture
def beca(db):
    return Beca.objects.create(nombre="Beca Excelencia", activa=True)


@pytest.fixture
def convocatoria(db, superusuario, beca):
    import datetime

    from django.utils import timezone

    c = Convocatoria.objects.create(
        nombre="Conv 2026",
        fecha_apertura=timezone.now() - datetime.timedelta(days=1),
        fecha_cierre=timezone.now() + datetime.timedelta(days=30),
        estado=Convocatoria.Estado.PUBLICADA,
        creada_por=superusuario,
    )
    c.becas.add(beca)
    return c


@pytest.fixture
def postulacion_borrador(db, estudiante, convocatoria, beca, formulario):
    return Postulacion.objects.create(
        estudiante=estudiante,
        convocatoria=convocatoria,
        beca=beca,
        formulario=formulario,
        estado=Postulacion.Estado.BORRADOR,
    )


@pytest.mark.django_db
def test_iniciar_postulacion_ok(estudiante, convocatoria, beca, formulario):
    p = services.iniciar_postulacion(estudiante=estudiante, convocatoria=convocatoria, beca=beca)
    assert p.estado == Postulacion.Estado.BORRADOR
    assert p.estudiante == estudiante


@pytest.mark.django_db
def test_iniciar_postulacion_sin_formulario(db, estudiante, convocatoria, beca):
    with pytest.raises(FormularioIncompletoError):
        services.iniciar_postulacion(estudiante=estudiante, convocatoria=convocatoria, beca=beca)


@pytest.mark.django_db
def test_iniciar_postulacion_ya_activa(
    estudiante, convocatoria, beca, formulario, postulacion_borrador
):
    with pytest.raises(PostulacionActivaExistenteError):
        services.iniciar_postulacion(estudiante=estudiante, convocatoria=convocatoria, beca=beca)


@pytest.mark.django_db
def test_iniciar_postulacion_convocatoria_cerrada(estudiante, beca, formulario, superusuario):
    import datetime

    from django.utils import timezone

    c = Convocatoria.objects.create(
        nombre="Cerrada",
        fecha_apertura=timezone.now() - datetime.timedelta(days=10),
        fecha_cierre=timezone.now() - datetime.timedelta(days=1),
        estado=Convocatoria.Estado.CERRADA,
        creada_por=superusuario,
    )
    c.becas.add(beca)
    with pytest.raises(ConvocatoriaNoVigenteError):
        services.iniciar_postulacion(estudiante=estudiante, convocatoria=c, beca=beca)


@pytest.mark.django_db
def test_enviar_postulacion_ok(postulacion_borrador, convocatoria):
    tipo = TipoDocumento.objects.create(nombre="DNI", activo=True)
    convocatoria.documentos_requeridos.add(tipo)

    p = services.enviar_postulacion(postulacion=postulacion_borrador)
    assert p.estado == Postulacion.Estado.ENVIADA
    assert p.fecha_envio is not None
    assert p.numero_referencia is not None and p.numero_referencia > 0
    assert DocumentoPostulacion.objects.filter(postulacion=p).count() == 1


@pytest.mark.django_db
def test_enviar_postulacion_numero_referencia_secuencial(
    estudiante, convocatoria, beca, formulario
):
    p1 = services.iniciar_postulacion(estudiante=estudiante, convocatoria=convocatoria, beca=beca)
    services.enviar_postulacion(postulacion=p1)

    estudiante2 = Usuario.objects.create_user(email="est2@test.com", password="pass")
    formulario2 = FormularioSocioeconomico.objects.create(
        usuario=estudiante2,
        cantidad_familiares=2,
        tiene_beca_previa=False,
        completado=True,
    )
    p2 = services.iniciar_postulacion(estudiante=estudiante2, convocatoria=convocatoria, beca=beca)
    services.enviar_postulacion(postulacion=p2)

    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p2.numero_referencia == p1.numero_referencia + 1
    assert formulario2.usuario == estudiante2


@pytest.mark.django_db
def test_generar_constancia_pdf_sin_enviar(postulacion_borrador):
    with pytest.raises(ConstanciaNoDisponibleError):
        services.generar_constancia_pdf(postulacion=postulacion_borrador)


@pytest.mark.django_db
def test_generar_constancia_pdf_ok(postulacion_borrador):
    p = services.enviar_postulacion(postulacion=postulacion_borrador)
    pdf_bytes = services.generar_constancia_pdf(postulacion=p)
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.django_db
def test_enviar_postulacion_invalida(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.ENVIADA
    postulacion_borrador.save()
    with pytest.raises(TransicionEstadoInvalidaError):
        services.enviar_postulacion(postulacion=postulacion_borrador)


@pytest.mark.django_db
def test_verificar_identidad_aprobada_sin_docs(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.ENVIADA
    postulacion_borrador.save()

    p = services.verificar_identidad(postulacion=postulacion_borrador, aprobar=True)
    assert p.estado == Postulacion.Estado.APROBADA


@pytest.mark.django_db
def test_verificar_identidad_rechazada(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.ENVIADA
    postulacion_borrador.save()

    p = services.verificar_identidad(
        postulacion=postulacion_borrador, aprobar=False, observaciones="DNI vencido"
    )
    assert p.estado == Postulacion.Estado.RECHAZADA_IDENTIDAD
    assert p.observaciones_identidad == "DNI vencido"


@pytest.mark.django_db
def test_validar_documento_aprueba_ultimo_y_cierra(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.EN_REVISION
    postulacion_borrador.save()
    tipo = TipoDocumento.objects.create(nombre="Cert. Ingresos", activo=True)
    doc = DocumentoPostulacion.objects.create(postulacion=postulacion_borrador, tipo_documento=tipo)

    services.validar_documento(documento=doc, aprobar=True)
    postulacion_borrador.refresh_from_db()
    assert postulacion_borrador.estado == Postulacion.Estado.APROBADA


@pytest.mark.django_db
def test_validar_documento_rechaza_y_cierra(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.EN_REVISION
    postulacion_borrador.save()
    tipo = TipoDocumento.objects.create(nombre="Cert. Ingresos", activo=True)
    doc = DocumentoPostulacion.objects.create(postulacion=postulacion_borrador, tipo_documento=tipo)

    services.validar_documento(documento=doc, aprobar=False)
    postulacion_borrador.refresh_from_db()
    assert postulacion_borrador.estado == Postulacion.Estado.RECHAZADA_DOCUMENTACION


@pytest.mark.django_db
def test_validar_documento_ya_validado(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.EN_REVISION
    postulacion_borrador.save()
    tipo = TipoDocumento.objects.create(nombre="DNI", activo=True)
    doc = DocumentoPostulacion.objects.create(
        postulacion=postulacion_borrador, tipo_documento=tipo, validado=True
    )
    with pytest.raises(DocumentoNoPendienteError):
        services.validar_documento(documento=doc, aprobar=True)


@pytest.mark.django_db
def test_digitalizar_documento_no_aprobado(postulacion_borrador):
    tipo = TipoDocumento.objects.create(nombre="DNI", activo=True)
    doc = DocumentoPostulacion.objects.create(
        postulacion=postulacion_borrador, tipo_documento=tipo, validado=False
    )
    with pytest.raises(DocumentoNoAprobadoError):
        services.digitalizar_documento(documento=doc, archivo=None)


@pytest.mark.django_db
def test_marcar_rechazadas_por_cierre(postulacion_borrador, convocatoria):
    postulacion_borrador.estado = Postulacion.Estado.ENVIADA
    postulacion_borrador.save()

    services.marcar_rechazadas_por_cierre(convocatoria=convocatoria)
    postulacion_borrador.refresh_from_db()
    assert postulacion_borrador.estado == Postulacion.Estado.RECHAZADA_NO_PRESENTACION


@pytest.mark.django_db
def test_listar_cola_revision_incluye_aprobada(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.APROBADA
    postulacion_borrador.save()

    resultado = services.listar_cola_revision()
    assert postulacion_borrador in resultado


@pytest.mark.django_db
def test_listar_cola_revision_excluye_estados_terminales(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.PROCESADA
    postulacion_borrador.save()

    resultado = services.listar_cola_revision()
    assert postulacion_borrador not in resultado


@pytest.mark.django_db
def test_listar_cola_revision_filtro_por_estado_aprobada(postulacion_borrador):
    postulacion_borrador.estado = Postulacion.Estado.APROBADA
    postulacion_borrador.save()

    resultado = services.listar_cola_revision(estado=Postulacion.Estado.APROBADA)
    assert postulacion_borrador in resultado

    resultado_enviada = services.listar_cola_revision(estado=Postulacion.Estado.ENVIADA)
    assert postulacion_borrador not in resultado_enviada
