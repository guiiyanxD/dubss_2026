from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from apps.configuracion.models import FormularioSocioeconomico
from apps.convocatorias.models import Beca, Convocatoria  # noqa: F401

from .exceptions import (
    BecaNoDisponibleError,
    ConstanciaNoDisponibleError,
    ConvocatoriaNoVigenteError,
    DocumentoNoAprobadoError,
    DocumentoNoPendienteError,
    FormularioIncompletoError,
    PostulacionActivaExistenteError,
    TransicionEstadoInvalidaError,
)
from .models import ContadorReferencia, DocumentoPostulacion, Postulacion
from .signals import (
    documentacion_procesada,
    identidad_verificada,
    postulacion_enviada,
)

CODIGO_FORMULARIO = "FORMULARIO DUBS 002"


@transaction.atomic
def iniciar_postulacion(*, estudiante, convocatoria, beca):
    """CU16 — Crea una postulación en estado Borrador.

    Args:
        estudiante: Usuario con rol Estudiante.
        convocatoria: Instancia de Convocatoria.
        beca: Instancia de Beca.

    Returns:
        La Postulacion creada.

    Raises:
        ConvocatoriaNoVigenteError: Si la convocatoria no está publicada y vigente.
        BecaNoDisponibleError: Si la beca no pertenece a la convocatoria.
        PostulacionActivaExistenteError: Si el estudiante ya tiene una postulación activa.
        FormularioIncompletoError: Si el formulario socioeconómico no está completo.
    """
    if not convocatoria.esta_vigente():
        raise ConvocatoriaNoVigenteError("La convocatoria no está vigente.")

    if not convocatoria.becas.filter(pk=beca.pk).exists():
        raise BecaNoDisponibleError("La beca no pertenece a esta convocatoria.")

    if Postulacion.objects.filter(
        estudiante=estudiante, estado__in=Postulacion.ESTADOS_ACTIVOS
    ).exists():
        raise PostulacionActivaExistenteError(
            "Ya tenés una postulación activa. Debés finalizarla antes de postularte nuevamente."
        )

    try:
        formulario = FormularioSocioeconomico.objects.get(usuario=estudiante)
        if not formulario.completado:
            raise FormularioIncompletoError(
                "Debés completar tu formulario socioeconómico antes de postularte."
            )
    except FormularioSocioeconomico.DoesNotExist:
        raise FormularioIncompletoError(
            "Debés completar tu formulario socioeconómico antes de postularte."
        )

    return Postulacion.objects.create(
        estudiante=estudiante,
        convocatoria=convocatoria,
        beca=beca,
        formulario=formulario,
        estado=Postulacion.Estado.BORRADOR,
    )


@transaction.atomic
def enviar_postulacion(*, postulacion):
    """CU17 — Envía la postulación: BORRADOR → ENVIADA. Crea registros de documentos.

    Args:
        postulacion: Instancia de Postulacion en estado BORRADOR.

    Returns:
        La postulacion actualizada.

    Raises:
        TransicionEstadoInvalidaError: Si no está en estado BORRADOR.
    """
    if postulacion.estado != Postulacion.Estado.BORRADOR:
        raise TransicionEstadoInvalidaError(
            "Solo se pueden enviar postulaciones en estado Borrador."
        )

    postulacion.estado = Postulacion.Estado.ENVIADA
    postulacion.fecha_envio = timezone.now()
    postulacion.numero_referencia = ContadorReferencia.siguiente()
    postulacion.save(update_fields=["estado", "fecha_envio", "numero_referencia"])

    for tipo_doc in postulacion.convocatoria.documentos_requeridos.all():
        DocumentoPostulacion.objects.get_or_create(
            postulacion=postulacion,
            tipo_documento=tipo_doc,
        )

    transaction.on_commit(
        lambda: postulacion_enviada.send(sender=Postulacion, postulacion=postulacion)
    )
    return postulacion


@transaction.atomic
def verificar_identidad(*, postulacion, aprobar, observaciones=""):
    """CU18 — Verifica la identidad presencial del postulante.

    Si aprueba y hay documentos requeridos → EN_REVISION.
    Si aprueba sin documentos requeridos → APROBADA directamente.
    Si rechaza → RECHAZADA_IDENTIDAD.

    Args:
        postulacion: Instancia de Postulacion en estado ENVIADA.
        aprobar: Bool indicando si la identidad es válida.
        observaciones: Notas del operador (opcional).

    Raises:
        TransicionEstadoInvalidaError: Si no está en estado ENVIADA.
    """
    if postulacion.estado != Postulacion.Estado.ENVIADA:
        raise TransicionEstadoInvalidaError("La verificación de identidad requiere estado ENVIADA.")

    postulacion.observaciones_identidad = observaciones

    if aprobar:
        tiene_documentos = postulacion.documentos.exists()
        postulacion.estado = (
            Postulacion.Estado.EN_REVISION if tiene_documentos else Postulacion.Estado.APROBADA
        )
    else:
        postulacion.estado = Postulacion.Estado.RECHAZADA_IDENTIDAD

    postulacion.save(update_fields=["estado", "observaciones_identidad"])

    transaction.on_commit(
        lambda: identidad_verificada.send(
            sender=Postulacion, postulacion=postulacion, aprobada=aprobar
        )
    )
    return postulacion


@transaction.atomic
def validar_documento(*, documento, aprobar):
    """CU19 — Valida o rechaza un documento físico presentado.

    Si se rechaza → postulación pasa a RECHAZADA_DOCUMENTACION.
    Si se aprueba el último pendiente → postulación pasa a APROBADA.

    Args:
        documento: Instancia de DocumentoPostulacion con validado=None.
        aprobar: Bool indicando si el documento es válido.

    Raises:
        DocumentoNoPendienteError: Si el documento ya fue validado.
        TransicionEstadoInvalidaError: Si la postulación no está EN_REVISION.
    """
    if documento.validado is not None:
        raise DocumentoNoPendienteError("Este documento ya fue validado.")

    postulacion = documento.postulacion
    if postulacion.estado != Postulacion.Estado.EN_REVISION:
        raise TransicionEstadoInvalidaError(
            "La validación de documentos requiere estado EN_REVISION."
        )

    documento.validado = aprobar
    documento.fecha_validacion = timezone.now()
    documento.save(update_fields=["validado", "fecha_validacion"])

    estado_final = None
    if not aprobar:
        postulacion.estado = Postulacion.Estado.RECHAZADA_DOCUMENTACION
        postulacion.save(update_fields=["estado"])
        estado_final = False
    else:
        pendientes = postulacion.documentos.filter(validado__isnull=True).exists()
        if not pendientes:
            postulacion.estado = Postulacion.Estado.APROBADA
            postulacion.save(update_fields=["estado"])
            estado_final = True

    if estado_final is not None:
        _aprobada = estado_final
        _post = postulacion
        transaction.on_commit(
            lambda: documentacion_procesada.send(
                sender=Postulacion, postulacion=_post, aprobada=_aprobada
            )
        )

    return documento


@transaction.atomic
def digitalizar_documento(*, documento, archivo):
    """CU20 — Adjunta el archivo digitalizado de un documento aprobado.

    Args:
        documento: Instancia de DocumentoPostulacion con validado=True.
        archivo: Objeto de archivo (InMemoryUploadedFile).

    Raises:
        DocumentoNoAprobadoError: Si el documento no fue aprobado.
    """
    if not documento.validado:
        raise DocumentoNoAprobadoError("Solo se pueden digitalizar documentos aprobados.")

    documento.archivo = archivo
    documento.save(update_fields=["archivo"])
    return documento


def listar_postulaciones_estudiante(*, estudiante):
    """Retorna todas las postulaciones del estudiante, más recientes primero."""
    return (
        Postulacion.objects.filter(estudiante=estudiante)
        .select_related("convocatoria", "beca")
        .order_by("-fecha_creacion")
    )


def listar_cola_revision(*, estado=None, convocatoria_id=None, beca_id=None, busqueda=None):
    """Retorna postulaciones pendientes de revisión (ENVIADA o EN_REVISION), con filtros opcionales."""
    qs = (
        Postulacion.objects.filter(
            estado__in=[Postulacion.Estado.ENVIADA, Postulacion.Estado.EN_REVISION]
        )
        .select_related("estudiante__perfil_estudiante", "convocatoria", "beca")
        .order_by("fecha_envio")
    )
    if estado:
        qs = qs.filter(estado=estado)
    if convocatoria_id:
        qs = qs.filter(convocatoria_id=convocatoria_id)
    if beca_id:
        qs = qs.filter(beca_id=beca_id)
    if busqueda:
        qs = qs.filter(
            Q(estudiante__first_name__icontains=busqueda)
            | Q(estudiante__last_name__icontains=busqueda)
            | Q(estudiante__perfil_estudiante__nro_registro__icontains=busqueda)
        )
    return qs


def marcar_rechazadas_por_cierre(*, convocatoria):
    """Marca como RECHAZADA_NO_PRESENTACION las postulaciones activas de una convocatoria cerrada."""
    Postulacion.objects.filter(
        convocatoria=convocatoria,
        estado__in=[Postulacion.Estado.BORRADOR, Postulacion.Estado.ENVIADA],
    ).update(estado=Postulacion.Estado.RECHAZADA_NO_PRESENTACION)


def generar_constancia_pdf(*, postulacion):
    """Genera el PDF de la constancia del formulario socioeconómico (FORMULARIO DUBS 002).

    Reproduce el formulario socioeconómico oficial en papel con los datos de la
    postulación enviada, incluyendo el número de referencia asignado en CU17.

    Args:
        postulacion: Instancia de Postulacion ya enviada (numero_referencia asignado).

    Returns:
        Bytes del archivo .pdf.

    Raises:
        ConstanciaNoDisponibleError: Si la postulación todavía no fue enviada.
    """
    from weasyprint import HTML

    if postulacion.numero_referencia is None:
        raise ConstanciaNoDisponibleError(
            "La constancia solo está disponible para postulaciones enviadas."
        )

    formulario = postulacion.formulario
    contexto = {
        "postulacion": postulacion,
        "estudiante": postulacion.estudiante,
        "perfil_estudiante": getattr(postulacion.estudiante, "perfil_estudiante", None),
        "formulario": formulario,
        "integrantes_familiares": formulario.integrantes_familiares.all(),
        "beca": postulacion.beca,
        "convocatoria": postulacion.convocatoria,
        "codigo_formulario": CODIGO_FORMULARIO,
    }

    html_str = render_to_string("postulaciones/constancia_pdf.html", contexto)
    return HTML(string=html_str).write_pdf()
