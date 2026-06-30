"""Catálogo acotado de tools (function calling) para el chat con el LLM local.

Solo expone consultas agregadas de `selectors.py` — nunca registros individuales de
estudiantes — para reducir el riesgo de exponer datos personales vía prompt injection.
El modelo no puede ejecutar nada fuera de `CATALOGO` (lista blanca).
"""

from apps.convocatorias.models import Convocatoria
from apps.postulaciones.models import Postulacion

from . import selectors


def _convocatoria_por_id(convocatoria_id=None):
    if not convocatoria_id:
        return None
    return Convocatoria.objects.filter(pk=convocatoria_id).first()


def _listar_convocatorias(**_kwargs):
    return {
        "convocatorias": [
            {"id": c.pk, "nombre": c.nombre, "estado": c.estado}
            for c in Convocatoria.objects.order_by("-fecha_apertura")
        ]
    }


def _embudo_postulaciones(convocatoria_id=None, **_kwargs):
    return selectors.embudo_estados(convocatoria=_convocatoria_por_id(convocatoria_id))


def _postulaciones_por_beca(convocatoria_id=None, **_kwargs):
    return selectors.postulaciones_por_beca(convocatoria=_convocatoria_por_id(convocatoria_id))


def _motivos_de_rechazo(convocatoria_id=None, **_kwargs):
    return selectors.desglose_rechazos(convocatoria=_convocatoria_por_id(convocatoria_id))


def _indicadores_socioeconomicos(convocatoria_id=None, **_kwargs):
    return selectors.indicadores_generales(convocatoria=_convocatoria_por_id(convocatoria_id))


def _tasa_adjudicacion_por_convocatoria(**_kwargs):
    return selectors.tasa_adjudicacion_por_convocatoria()


def _validacion_documental(**_kwargs):
    return selectors.validacion_por_tipo_documento()


def _postulantes_por_carrera(convocatoria_id=None, **_kwargs):
    return selectors.postulantes_por_carrera(convocatoria=_convocatoria_por_id(convocatoria_id))


def _tasa_entrega_notificaciones(**_kwargs):
    return selectors.tasa_entrega_notificaciones()


def _generar_reporte_postulantes(
    convocatoria_id=None,
    carrera=None,
    anio_ingreso_min=None,
    anio_ingreso_max=None,
    cantidad_familiares_min=None,
    cantidad_familiares_max=None,
    tiene_discapacidad=None,
    tiene_hijos=None,
    estado_postulacion=None,
    formato="excel",
    **_kwargs,
):
    """Genera un archivo descargable (Excel o PDF) con los postulantes que cumplen los
    filtros. El LLM nunca recibe las filas ni el archivo — solo la cantidad encontrada.
    El archivo real viaja en claves internas (`_archivo_bytes`/`_archivo_nombre`) que
    `services.py` intercepta y adjunta al mensaje del asistente antes de serializar el
    resultado de vuelta al modelo."""
    from .services import ReporteService

    filas = selectors.buscar_postulantes(
        convocatoria=_convocatoria_por_id(convocatoria_id),
        carrera=carrera,
        anio_ingreso_min=anio_ingreso_min,
        anio_ingreso_max=anio_ingreso_max,
        cantidad_familiares_min=cantidad_familiares_min,
        cantidad_familiares_max=cantidad_familiares_max,
        tiene_discapacidad=tiene_discapacidad,
        tiene_hijos=tiene_hijos,
        estado_postulacion=estado_postulacion,
    )
    formato = formato if formato in ("excel", "pdf") else "excel"
    nombre_archivo, contenido_bytes = ReporteService.generar_archivo_postulantes(
        filas=filas, formato=formato
    )
    return {
        "filas_encontradas": len(filas),
        "formato": formato,
        "_archivo_bytes": contenido_bytes,
        "_archivo_nombre": nombre_archivo,
    }


_SIN_ARGUMENTOS = {"type": "object", "properties": {}, "required": []}

_CONVOCATORIA_OPCIONAL = {
    "type": "object",
    "properties": {
        "convocatoria_id": {
            "type": "integer",
            "description": "ID de la convocatoria a consultar (ver listar_convocatorias). Omitir para incluir todas.",
        },
    },
    "required": [],
}

_REPORTE_POSTULANTES_PARAMS = {
    "type": "object",
    "properties": {
        "convocatoria_id": {
            "type": "integer",
            "description": "ID de la convocatoria a filtrar (ver listar_convocatorias). Omitir para todas.",
        },
        "carrera": {
            "type": "string",
            "description": "Filtra por carrera del postulante (coincidencia parcial, ej. 'Sistemas').",
        },
        "anio_ingreso_min": {
            "type": "integer",
            "description": "Año de ingreso a la carrera, mínimo.",
        },
        "anio_ingreso_max": {
            "type": "integer",
            "description": "Año de ingreso a la carrera, máximo.",
        },
        "cantidad_familiares_min": {
            "type": "integer",
            "description": "Cantidad mínima de integrantes del grupo familiar.",
        },
        "cantidad_familiares_max": {
            "type": "integer",
            "description": "Cantidad máxima de integrantes del grupo familiar.",
        },
        "tiene_discapacidad": {
            "type": "boolean",
            "description": "Filtra por presencia de discapacidad.",
        },
        "tiene_hijos": {
            "type": "boolean",
            "description": "Filtra por si el postulante tiene hijos.",
        },
        "estado_postulacion": {
            "type": "string",
            "enum": list(Postulacion.Estado.values),
            "description": "Estado actual de la postulación.",
        },
        "formato": {
            "type": "string",
            "enum": ["excel", "pdf"],
            "description": "Formato del archivo a generar. Por defecto 'excel'.",
        },
    },
    "required": [],
}

CATALOGO = {
    "listar_convocatorias": {
        "descripcion": "Lista todas las convocatorias de becas con su id, nombre y estado.",
        "parametros": _SIN_ARGUMENTOS,
        "funcion": _listar_convocatorias,
    },
    "embudo_postulaciones": {
        "descripcion": "Cantidad de postulaciones agrupadas por estado actual (embudo del proceso).",
        "parametros": _CONVOCATORIA_OPCIONAL,
        "funcion": _embudo_postulaciones,
    },
    "postulaciones_por_beca": {
        "descripcion": "Cantidad de postulaciones agrupadas por beca.",
        "parametros": _CONVOCATORIA_OPCIONAL,
        "funcion": _postulaciones_por_beca,
    },
    "motivos_de_rechazo": {
        "descripcion": "Cantidad de postulaciones rechazadas, desglosadas por motivo.",
        "parametros": _CONVOCATORIA_OPCIONAL,
        "funcion": _motivos_de_rechazo,
    },
    "indicadores_socioeconomicos": {
        "descripcion": (
            "Indicadores agregados del perfil socioeconómico de los postulantes: "
            "promedio de familiares/hijos, % con discapacidad, % de formularios completos."
        ),
        "parametros": _CONVOCATORIA_OPCIONAL,
        "funcion": _indicadores_socioeconomicos,
    },
    "tasa_adjudicacion_por_convocatoria": {
        "descripcion": (
            "Porcentaje de postulaciones adjudicadas sobre el total con resultado final, por convocatoria."
        ),
        "parametros": _SIN_ARGUMENTOS,
        "funcion": _tasa_adjudicacion_por_convocatoria,
    },
    "validacion_documental": {
        "descripcion": "Cantidad de documentos aprobados/rechazados/pendientes, por tipo de documento.",
        "parametros": _SIN_ARGUMENTOS,
        "funcion": _validacion_documental,
    },
    "postulantes_por_carrera": {
        "descripcion": "Cantidad de postulaciones agrupadas por carrera del postulante (top 10).",
        "parametros": _CONVOCATORIA_OPCIONAL,
        "funcion": _postulantes_por_carrera,
    },
    "tasa_entrega_notificaciones": {
        "descripcion": "Cantidad de notificaciones por estado de entrega (pendiente/enviada/error).",
        "parametros": _SIN_ARGUMENTOS,
        "funcion": _tasa_entrega_notificaciones,
    },
    "generar_reporte_postulantes": {
        "descripcion": (
            "Genera un archivo descargable (Excel o PDF) con la lista de postulantes que "
            "cumplen los filtros indicados. Usar esta tool cuando se pida una tabla, "
            "listado o reporte exportable — nunca intentar escribir la tabla como texto. "
            "El sistema NO registra la edad del estudiante; si el pedido la requiere, "
            "aclarar esa limitación en la respuesta en vez de inventar un valor."
        ),
        "parametros": _REPORTE_POSTULANTES_PARAMS,
        "funcion": _generar_reporte_postulantes,
    },
}


def definiciones_tools():
    """Catálogo en formato Ollama/OpenAI (`tools=[...]`) para pasar a `llm_client.chat`."""
    return [
        {
            "type": "function",
            "function": {
                "name": nombre,
                "description": datos["descripcion"],
                "parameters": datos["parametros"],
            },
        }
        for nombre, datos in CATALOGO.items()
    ]


def ejecutar_tool(nombre, argumentos):
    """Dispatcher seguro: solo ejecuta funciones del catálogo (lista blanca)."""
    entrada = CATALOGO.get(nombre)
    if entrada is None:
        return {"error": f"Tool desconocida: {nombre}"}
    try:
        return entrada["funcion"](**(argumentos or {}))
    except Exception as exc:
        return {"error": str(exc)}
