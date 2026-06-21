from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from .exceptions import (
    ConvocatoriaNoModificableError,
    ConvocatoriaYaCerradaError,
    FechaInvalidaError,
    NombreDuplicadoError,
    PonderacionInvalidaError,
)
from .models import Beca, Convocatoria, TipoDocumento
from .signals import convocatoria_cerrada

# ---------------------------------------------------------------------------
# Convocatorias
# ---------------------------------------------------------------------------


def _validar_fechas(fecha_apertura, fecha_cierre):
    if fecha_cierre <= fecha_apertura:
        raise FechaInvalidaError("La fecha de cierre debe ser posterior a la fecha de apertura.")


@transaction.atomic
def crear_convocatoria(
    *, nombre, descripcion, fecha_apertura, fecha_cierre, becas_ids, documentos_ids, creada_por
):
    """Crea una convocatoria en estado Borrador.

    Args:
        nombre: Nombre de la convocatoria.
        descripcion: Descripción opcional.
        fecha_apertura: Datetime de apertura.
        fecha_cierre: Datetime de cierre (debe ser posterior a apertura).
        becas_ids: Lista de PKs de Beca a asociar.
        documentos_ids: Lista de PKs de TipoDocumento a asociar.
        creada_por: Instancia de Usuario que crea la convocatoria.

    Returns:
        La Convocatoria creada.

    Raises:
        FechaInvalidaError: Si fecha_cierre <= fecha_apertura.
    """
    _validar_fechas(fecha_apertura, fecha_cierre)
    convocatoria = Convocatoria.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        fecha_apertura=fecha_apertura,
        fecha_cierre=fecha_cierre,
        creada_por=creada_por,
    )
    convocatoria.becas.set(becas_ids)
    convocatoria.documentos_requeridos.set(documentos_ids)
    return convocatoria


@transaction.atomic
def editar_convocatoria(
    *, convocatoria, nombre, descripcion, fecha_apertura, fecha_cierre, becas_ids, documentos_ids
):
    """Edita una convocatoria en estado Borrador.

    Raises:
        ConvocatoriaNoModificableError: Si no está en estado Borrador.
        FechaInvalidaError: Si fecha_cierre <= fecha_apertura.
    """
    if convocatoria.estado != Convocatoria.Estado.BORRADOR:
        raise ConvocatoriaNoModificableError(
            "Solo se pueden editar convocatorias en estado Borrador."
        )
    _validar_fechas(fecha_apertura, fecha_cierre)
    convocatoria.nombre = nombre
    convocatoria.descripcion = descripcion
    convocatoria.fecha_apertura = fecha_apertura
    convocatoria.fecha_cierre = fecha_cierre
    convocatoria.save(update_fields=["nombre", "descripcion", "fecha_apertura", "fecha_cierre"])
    convocatoria.becas.set(becas_ids)
    convocatoria.documentos_requeridos.set(documentos_ids)
    return convocatoria


@transaction.atomic
def publicar_convocatoria(*, convocatoria):
    """Pasa la convocatoria de Borrador a Publicada.

    Raises:
        ConvocatoriaNoModificableError: Si no está en Borrador.
    """
    if convocatoria.estado != Convocatoria.Estado.BORRADOR:
        raise ConvocatoriaNoModificableError(
            "Solo se pueden publicar convocatorias en estado Borrador."
        )
    convocatoria.estado = Convocatoria.Estado.PUBLICADA
    convocatoria.save(update_fields=["estado"])
    return convocatoria


@transaction.atomic
def cerrar_convocatoria(*, convocatoria):
    """Cierra una convocatoria y emite la señal convocatoria_cerrada.

    Raises:
        ConvocatoriaYaCerradaError: Si ya está Cerrada.
    """
    if convocatoria.estado == Convocatoria.Estado.CERRADA:
        raise ConvocatoriaYaCerradaError(f"La convocatoria '{convocatoria}' ya está cerrada.")
    convocatoria.estado = Convocatoria.Estado.CERRADA
    convocatoria.save(update_fields=["estado"])
    convocatoria_cerrada.send(sender=Convocatoria, convocatoria=convocatoria)
    return convocatoria


def cerrar_convocatorias_vencidas():
    """Cierra todas las convocatorias publicadas cuya fecha_cierre ya pasó.

    Llamado por la tarea Celery Beat (CU11).

    Returns:
        Cantidad de convocatorias cerradas.
    """
    vencidas = Convocatoria.objects.filter(
        estado=Convocatoria.Estado.PUBLICADA,
        fecha_cierre__lt=timezone.now(),
    )
    count = 0
    for convocatoria in vencidas:
        cerrar_convocatoria(convocatoria=convocatoria)
        count += 1
    return count


def listar_convocatorias(*, para_estudiante=False, estado=None, busqueda=None):
    """Retorna convocatorias. Estudiantes solo ven las Publicadas.

    Args:
        para_estudiante: Si True, filtra solo las PUBLICADAS.
        estado: Valor de Convocatoria.Estado a filtrar (solo aplica para staff).
        busqueda: Texto a buscar en el nombre.

    Returns:
        QuerySet de Convocatoria ordenado por fecha de cierre descendente.
    """
    qs = (
        Convocatoria.objects.prefetch_related("becas", "documentos_requeridos")
        .select_related("creada_por")
        .order_by("-fecha_cierre")
    )
    if para_estudiante:
        qs = qs.filter(estado=Convocatoria.Estado.PUBLICADA)
    elif estado:
        qs = qs.filter(estado=estado)
    if busqueda:
        qs = qs.filter(nombre__icontains=busqueda)
    return qs


# ---------------------------------------------------------------------------
# Becas (catálogo)
# ---------------------------------------------------------------------------


def _pesos_default():
    return {
        "peso_ingreso": 40,
        "peso_desempleo": 20,
        "peso_familiares": 20,
        "peso_no_propietario": 10,
        "peso_sin_beca_previa": 10,
    }


@transaction.atomic
def crear_beca(*, nombre, descripcion="", **pesos):
    """Crea un tipo de beca.

    Args:
        pesos: peso_ingreso/peso_desempleo/peso_familiares/peso_no_propietario/
            peso_sin_beca_previa (CU15); por defecto reproducen la fórmula original.

    Raises:
        NombreDuplicadoError: Si ya existe una beca con ese nombre.
        PonderacionInvalidaError: Si los pesos no suman 100.
    """
    if Beca.objects.filter(nombre=nombre).exists():
        raise NombreDuplicadoError(f"Ya existe una beca con el nombre '{nombre}'.")
    valores = {**_pesos_default(), **pesos}
    beca = Beca(nombre=nombre, descripcion=descripcion, **valores)
    try:
        beca.full_clean()
    except DjangoValidationError as exc:
        raise PonderacionInvalidaError("; ".join(exc.messages)) from exc
    beca.save()
    return beca


@transaction.atomic
def editar_beca(*, beca, nombre, descripcion, activa, **pesos):
    """Actualiza los datos de una beca existente.

    Args:
        pesos: peso_ingreso/peso_desempleo/peso_familiares/peso_no_propietario/
            peso_sin_beca_previa (CU15); si no se pasan, se conservan los actuales.

    Raises:
        NombreDuplicadoError: Si el nuevo nombre ya está en uso por otra beca.
        PonderacionInvalidaError: Si los pesos no suman 100.
    """
    if Beca.objects.filter(nombre=nombre).exclude(pk=beca.pk).exists():
        raise NombreDuplicadoError(f"Ya existe una beca con el nombre '{nombre}'.")
    beca.nombre = nombre
    beca.descripcion = descripcion
    beca.activa = activa
    for campo, valor in pesos.items():
        setattr(beca, campo, valor)
    try:
        beca.full_clean()
    except DjangoValidationError as exc:
        raise PonderacionInvalidaError("; ".join(exc.messages)) from exc
    beca.save()
    return beca


# ---------------------------------------------------------------------------
# Tipos de documento (catálogo)
# ---------------------------------------------------------------------------


@transaction.atomic
def crear_tipo_documento(*, nombre, descripcion=""):
    """Crea un tipo de documento requerido.

    Raises:
        NombreDuplicadoError: Si ya existe un tipo con ese nombre.
    """
    if TipoDocumento.objects.filter(nombre=nombre).exists():
        raise NombreDuplicadoError(f"Ya existe un tipo de documento con el nombre '{nombre}'.")
    return TipoDocumento.objects.create(nombre=nombre, descripcion=descripcion)


@transaction.atomic
def editar_tipo_documento(*, tipo_documento, nombre, descripcion, activo):
    """Actualiza los datos de un tipo de documento.

    Raises:
        NombreDuplicadoError: Si el nuevo nombre ya está en uso.
    """
    if TipoDocumento.objects.filter(nombre=nombre).exclude(pk=tipo_documento.pk).exists():
        raise NombreDuplicadoError(f"Ya existe un tipo de documento con el nombre '{nombre}'.")
    tipo_documento.nombre = nombre
    tipo_documento.descripcion = descripcion
    tipo_documento.activo = activo
    tipo_documento.save(update_fields=["nombre", "descripcion", "activo"])
    return tipo_documento
