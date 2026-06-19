"""Consultas de agregación reutilizables para el dashboard de KPIs (CU26).

Cada función devuelve datos planos (dicts/listas), sin construir gráficos ni HTML —
eso es responsabilidad de `charts.py`. Esto permite que los mismos datos se rendericen
con cualquier motor de gráficos (hoy Plotly, a futuro Matplotlib para el PDF).
"""

import pandas as pd
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Min, Q

from apps.configuracion.models import FormularioSocioeconomico
from apps.notificaciones.models import Notificacion
from apps.postulaciones.models import DocumentoPostulacion, Postulacion

ESTADOS_RESULTADO_FINAL = [
    Postulacion.Estado.ADJUDICADA,
    Postulacion.Estado.NO_ADJUDICADA,
    Postulacion.Estado.LISTA_ESPERA,
]

ESTADOS_RECHAZO = [
    Postulacion.Estado.RECHAZADA_NO_PRESENTACION,
    Postulacion.Estado.RECHAZADA_IDENTIDAD,
    Postulacion.Estado.RECHAZADA_DOCUMENTACION,
]

CAMPOS_DISTRIBUCION_SOCIOECONOMICA = {
    "situacion_laboral": FormularioSocioeconomico.SituacionLaboral,
    "situacion_habitacional": FormularioSocioeconomico.SituacionHabitacional,
    "dependencia_economica": FormularioSocioeconomico.DependenciaEconomica,
    "tipo_tenencia_vivienda": FormularioSocioeconomico.TipoTenenciaVivienda,
}


def _filtrar_postulaciones(*, convocatoria=None, fecha_desde=None, fecha_hasta=None):
    qs = Postulacion.objects.all()
    if convocatoria is not None:
        qs = qs.filter(convocatoria=convocatoria)
    if fecha_desde is not None:
        qs = qs.filter(fecha_creacion__date__gte=fecha_desde)
    if fecha_hasta is not None:
        qs = qs.filter(fecha_creacion__date__lte=fecha_hasta)
    return qs


def _formularios_de_postulantes(*, convocatoria=None):
    """Formularios socioeconómicos únicos de los postulantes filtrados (sin duplicar por
    convocatoria, ya que el formulario es reutilizable entre postulaciones)."""
    ids = (
        _filtrar_postulaciones(convocatoria=convocatoria)
        .values_list("formulario_id", flat=True)
        .distinct()
    )
    return FormularioSocioeconomico.objects.filter(pk__in=ids)


# ---------------------------------------------------------------------------
# Demanda y convocatorias
# ---------------------------------------------------------------------------


def postulaciones_por_beca(*, convocatoria=None, fecha_desde=None, fecha_hasta=None):
    """Total de postulaciones agrupadas por beca."""
    filas = (
        _filtrar_postulaciones(
            convocatoria=convocatoria, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
        )
        .values("beca__nombre")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return {"etiquetas": [f["beca__nombre"] for f in filas], "valores": [f["total"] for f in filas]}


def tasa_adjudicacion_por_convocatoria():
    """% de postulaciones ADJUDICADA sobre el total con resultado final, por convocatoria."""
    filas = (
        Postulacion.objects.filter(estado__in=ESTADOS_RESULTADO_FINAL)
        .values("convocatoria__nombre")
        .annotate(
            total=Count("id"),
            adjudicadas=Count("id", filter=Q(estado=Postulacion.Estado.ADJUDICADA)),
        )
        .order_by("convocatoria__nombre")
    )
    etiquetas = [f["convocatoria__nombre"] for f in filas]
    valores = [round(f["adjudicadas"] / f["total"] * 100, 1) if f["total"] else 0.0 for f in filas]
    return {"etiquetas": etiquetas, "valores": valores}


def tamano_lista_espera_por_convocatoria():
    """Cantidad de postulaciones en LISTA_ESPERA por convocatoria."""
    filas = (
        Postulacion.objects.filter(estado=Postulacion.Estado.LISTA_ESPERA)
        .values("convocatoria__nombre")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return {
        "etiquetas": [f["convocatoria__nombre"] for f in filas],
        "valores": [f["total"] for f in filas],
    }


# ---------------------------------------------------------------------------
# Embudo de postulaciones
# ---------------------------------------------------------------------------


def embudo_estados(*, convocatoria=None, fecha_desde=None, fecha_hasta=None):
    """Cantidad de postulaciones por estado actual, en el orden lógico del pipeline."""
    qs = _filtrar_postulaciones(
        convocatoria=convocatoria, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )
    conteos = dict(qs.values_list("estado").annotate(total=Count("id")))
    etiquetas, valores = [], []
    for estado in Postulacion.Estado:
        total = conteos.get(estado.value, 0)
        if total:
            etiquetas.append(estado.label)
            valores.append(total)
    return {"etiquetas": etiquetas, "valores": valores}


def desglose_rechazos(*, convocatoria=None, fecha_desde=None, fecha_hasta=None):
    """Cantidad de postulaciones rechazadas, desglosadas por motivo de rechazo."""
    qs = _filtrar_postulaciones(
        convocatoria=convocatoria, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )
    conteos = dict(
        qs.filter(estado__in=ESTADOS_RECHAZO).values_list("estado").annotate(total=Count("id"))
    )
    return {
        "etiquetas": [e.label for e in ESTADOS_RECHAZO],
        "valores": [conteos.get(e.value, 0) for e in ESTADOS_RECHAZO],
    }


def tiempos_promedio_por_etapa(*, convocatoria=None):
    """Tiempo promedio (en días) entre transiciones de estado consecutivas, calculado a
    partir del historial de auditoría (django-simple-history) de cada Postulacion."""
    qs = Postulacion.objects.all()
    if convocatoria is not None:
        qs = qs.filter(convocatoria=convocatoria)

    filas = []
    for postulacion in qs.only("id"):
        anterior = None
        for registro in postulacion.history.order_by("history_date"):
            if anterior is not None and registro.estado != anterior.estado:
                filas.append(
                    {
                        "transicion": f"{anterior.get_estado_display()} → {registro.get_estado_display()}",
                        "dias": (registro.history_date - anterior.history_date).total_seconds()
                        / 86400,
                    }
                )
            anterior = registro

    if not filas:
        return {"etiquetas": [], "valores": []}

    df = pd.DataFrame(filas)
    promedio = df.groupby("transicion")["dias"].mean().round(2).sort_values(ascending=False)
    return {"etiquetas": list(promedio.index), "valores": list(promedio.to_numpy())}


# ---------------------------------------------------------------------------
# Validación documental
# ---------------------------------------------------------------------------


def validacion_por_tipo_documento():
    """Cantidad de documentos aprobados/rechazados/pendientes, por tipo de documento."""
    filas = (
        DocumentoPostulacion.objects.values("tipo_documento__nombre", "validado")
        .annotate(total=Count("id"))
        .order_by("tipo_documento__nombre")
    )
    por_tipo = {}
    for f in filas:
        tipo = f["tipo_documento__nombre"]
        bucket = por_tipo.setdefault(tipo, {"aprobado": 0, "rechazado": 0, "pendiente": 0})
        if f["validado"] is True:
            bucket["aprobado"] += f["total"]
        elif f["validado"] is False:
            bucket["rechazado"] += f["total"]
        else:
            bucket["pendiente"] += f["total"]

    etiquetas = list(por_tipo.keys())
    return {
        "etiquetas": etiquetas,
        "aprobado": [por_tipo[t]["aprobado"] for t in etiquetas],
        "rechazado": [por_tipo[t]["rechazado"] for t in etiquetas],
        "pendiente": [por_tipo[t]["pendiente"] for t in etiquetas],
    }


def documento_mayor_rechazo():
    """Tipo de documento con mayor porcentaje de rechazo (cuello de botella documental)."""
    datos = validacion_por_tipo_documento()
    mejor_tipo, mejor_pct = None, 0.0
    for tipo, aprobado, rechazado, pendiente in zip(
        datos["etiquetas"], datos["aprobado"], datos["rechazado"], datos["pendiente"], strict=True
    ):
        total = aprobado + rechazado + pendiente
        pct = (rechazado / total * 100) if total else 0.0
        if pct > mejor_pct:
            mejor_tipo, mejor_pct = tipo, pct
    return {"tipo_documento": mejor_tipo, "porcentaje_rechazo": round(mejor_pct, 1)}


# ---------------------------------------------------------------------------
# Perfil socioeconómico
# ---------------------------------------------------------------------------


def distribucion_ingreso_familiar(*, convocatoria=None):
    """Lista de ingresos mensuales familiares de los postulantes (para histograma)."""
    valores = _formularios_de_postulantes(convocatoria=convocatoria).values_list(
        "ingreso_mensual_familiar", flat=True
    )
    return {"valores": [float(v) for v in valores]}


def distribucion_puntaje_socioeconomico(*, convocatoria=None):
    """Lista de puntajes socioeconómicos ya calculados (para histograma)."""
    valores = (
        _filtrar_postulaciones(convocatoria=convocatoria)
        .exclude(puntaje_socioeconomico__isnull=True)
        .values_list("puntaje_socioeconomico", flat=True)
    )
    return {"valores": [float(v) for v in valores]}


def distribucion_choices(campo, *, convocatoria=None):
    """Distribución de postulantes según un campo TextChoices del formulario socioeconómico.

    Args:
        campo: Una clave de `CAMPOS_DISTRIBUCION_SOCIOECONOMICA`.
        convocatoria: Filtra a los postulantes de esta convocatoria (None = todas).
    """
    enum = CAMPOS_DISTRIBUCION_SOCIOECONOMICA[campo]
    formularios = _formularios_de_postulantes(convocatoria=convocatoria)
    conteos = dict(
        formularios.exclude(**{campo: ""}).values_list(campo).annotate(total=Count("id"))
    )
    etiquetas, valores = [], []
    for choice in enum:
        total = conteos.get(choice.value, 0)
        if total:
            etiquetas.append(choice.label)
            valores.append(total)
    return {"etiquetas": etiquetas, "valores": valores}


def indicadores_generales(*, convocatoria=None):
    """Indicadores socioeconómicos agregados: promedios e indicadores binarios en %."""
    formularios = _formularios_de_postulantes(convocatoria=convocatoria)
    total = formularios.count()
    if not total:
        return {
            "promedio_familiares": 0.0,
            "promedio_hijos": 0.0,
            "pct_discapacidad": 0.0,
            "pct_completos": 0.0,
        }

    agregados = formularios.aggregate(
        promedio_familiares=Avg("cantidad_familiares"),
        promedio_hijos=Avg("cantidad_hijos"),
        con_discapacidad=Count("id", filter=Q(tiene_discapacidad=True)),
        completos=Count("id", filter=Q(completado=True)),
    )
    return {
        "promedio_familiares": round(agregados["promedio_familiares"] or 0, 1),
        "promedio_hijos": round(agregados["promedio_hijos"] or 0, 1),
        "pct_discapacidad": round(agregados["con_discapacidad"] / total * 100, 1),
        "pct_completos": round(agregados["completos"] / total * 100, 1),
    }


# ---------------------------------------------------------------------------
# Ranking y adjudicación
# ---------------------------------------------------------------------------


def comparacion_puntaje_por_resultado(*, convocatoria):
    """Distribución de puntaje_socioeconomico por resultado final, para UNA convocatoria.

    Requiere una convocatoria específica: los cupos (y por lo tanto los puntajes de
    corte) no son comparables entre convocatorias distintas.
    """
    datos = {}
    for estado in ESTADOS_RESULTADO_FINAL:
        valores = (
            Postulacion.objects.filter(convocatoria=convocatoria, estado=estado)
            .exclude(puntaje_socioeconomico__isnull=True)
            .values_list("puntaje_socioeconomico", flat=True)
        )
        datos[estado.label] = [float(v) for v in valores]
    return datos


def punto_corte_por_convocatoria():
    """Puntaje mínimo entre las postulaciones ADJUDICADA, por convocatoria."""
    filas = (
        Postulacion.objects.filter(estado=Postulacion.Estado.ADJUDICADA)
        .values("convocatoria__nombre")
        .annotate(corte=Min("puntaje_socioeconomico"))
        .order_by("convocatoria__nombre")
    )
    return {
        "etiquetas": [f["convocatoria__nombre"] for f in filas],
        "valores": [float(f["corte"]) if f["corte"] is not None else 0.0 for f in filas],
    }


# ---------------------------------------------------------------------------
# Académico
# ---------------------------------------------------------------------------


def postulantes_por_carrera(*, convocatoria=None, top=10):
    """Cantidad de postulaciones por carrera del postulante (top N carreras)."""
    filas = (
        _filtrar_postulaciones(convocatoria=convocatoria)
        .exclude(estudiante__perfil_estudiante__isnull=True)
        .values("estudiante__perfil_estudiante__carrera")
        .annotate(total=Count("id"))
        .order_by("-total")[:top]
    )
    return {
        "etiquetas": [f["estudiante__perfil_estudiante__carrera"] for f in filas],
        "valores": [f["total"] for f in filas],
    }


def tasa_adjudicacion_por_carrera():
    """% de postulaciones ADJUDICADA sobre el total con resultado final, por carrera."""
    filas = (
        Postulacion.objects.filter(estado__in=ESTADOS_RESULTADO_FINAL)
        .exclude(estudiante__perfil_estudiante__isnull=True)
        .values("estudiante__perfil_estudiante__carrera")
        .annotate(
            total=Count("id"),
            adjudicadas=Count("id", filter=Q(estado=Postulacion.Estado.ADJUDICADA)),
        )
        .order_by("-total")
    )
    etiquetas = [f["estudiante__perfil_estudiante__carrera"] for f in filas]
    valores = [round(f["adjudicadas"] / f["total"] * 100, 1) if f["total"] else 0.0 for f in filas]
    return {"etiquetas": etiquetas, "valores": valores}


def postulantes_por_anio_ingreso(*, convocatoria=None):
    """Cantidad de postulaciones agrupadas por año de ingreso a la carrera."""
    filas = (
        _filtrar_postulaciones(convocatoria=convocatoria)
        .exclude(estudiante__perfil_estudiante__isnull=True)
        .values("estudiante__perfil_estudiante__anio_ingreso")
        .annotate(total=Count("id"))
        .order_by("estudiante__perfil_estudiante__anio_ingreso")
    )
    return {
        "etiquetas": [str(f["estudiante__perfil_estudiante__anio_ingreso"]) for f in filas],
        "valores": [f["total"] for f in filas],
    }


# ---------------------------------------------------------------------------
# Notificaciones
# ---------------------------------------------------------------------------


def tasa_entrega_notificaciones(*, fecha_desde=None, fecha_hasta=None):
    """Cantidad de notificaciones por estado de entrega."""
    qs = Notificacion.objects.all()
    if fecha_desde is not None:
        qs = qs.filter(fecha_creacion__date__gte=fecha_desde)
    if fecha_hasta is not None:
        qs = qs.filter(fecha_creacion__date__lte=fecha_hasta)
    conteos = dict(qs.values_list("estado").annotate(total=Count("id")))
    return {
        "etiquetas": [e.label for e in Notificacion.Estado],
        "valores": [conteos.get(e.value, 0) for e in Notificacion.Estado],
    }


def latencia_envio_notificaciones():
    """Minutos promedio entre la creación y el envío exitoso de una notificación."""
    duracion = ExpressionWrapper(
        F("fecha_envio") - F("fecha_creacion"), output_field=DurationField()
    )
    resultado = (
        Notificacion.objects.filter(estado=Notificacion.Estado.ENVIADA)
        .annotate(latencia=duracion)
        .aggregate(promedio=Avg("latencia"))
    )
    promedio = resultado["promedio"]
    return {"minutos_promedio": round(promedio.total_seconds() / 60, 1) if promedio else 0.0}


# ---------------------------------------------------------------------------
# Búsqueda de postulantes (reportes ad-hoc, registros individuales)
# ---------------------------------------------------------------------------


def buscar_postulantes(
    *,
    convocatoria=None,
    carrera=None,
    anio_ingreso_min=None,
    anio_ingreso_max=None,
    cantidad_familiares_min=None,
    cantidad_familiares_max=None,
    situacion_laboral=None,
    situacion_habitacional=None,
    tiene_discapacidad=None,
    tiene_hijos=None,
    estado_postulacion=None,
    limite=200,
):
    """Búsqueda de postulantes con filtros acotados, para reportes ad-hoc (CU26 / chat IA).

    A diferencia del resto de `selectors.py`, esta función devuelve registros
    individuales (nombre, email, legajo) en vez de agregados — usar con cuidado. Todos
    los filtros son opcionales y se mapean a lookups explícitos del ORM (nunca a
    nombres de campo dinámicos).

    Returns:
        Lista de dicts, como máximo `limite` filas.
    """
    qs = Postulacion.objects.select_related(
        "estudiante", "estudiante__perfil_estudiante", "formulario", "convocatoria", "beca"
    )

    if convocatoria is not None:
        qs = qs.filter(convocatoria=convocatoria)
    if carrera:
        qs = qs.filter(estudiante__perfil_estudiante__carrera__icontains=carrera)
    if anio_ingreso_min is not None:
        qs = qs.filter(estudiante__perfil_estudiante__anio_ingreso__gte=anio_ingreso_min)
    if anio_ingreso_max is not None:
        qs = qs.filter(estudiante__perfil_estudiante__anio_ingreso__lte=anio_ingreso_max)
    if cantidad_familiares_min is not None:
        qs = qs.filter(formulario__cantidad_familiares__gte=cantidad_familiares_min)
    if cantidad_familiares_max is not None:
        qs = qs.filter(formulario__cantidad_familiares__lte=cantidad_familiares_max)
    if situacion_laboral:
        qs = qs.filter(formulario__situacion_laboral=situacion_laboral)
    if situacion_habitacional:
        qs = qs.filter(formulario__situacion_habitacional=situacion_habitacional)
    if tiene_discapacidad is not None:
        qs = qs.filter(formulario__tiene_discapacidad=tiene_discapacidad)
    if tiene_hijos is not None:
        qs = qs.filter(formulario__tiene_hijos=tiene_hijos)
    if estado_postulacion:
        qs = qs.filter(estado=estado_postulacion)

    qs = qs.distinct().order_by("estudiante__last_name", "estudiante__first_name")[:limite]

    resultados = []
    for p in qs:
        # getattr(p.estudiante, "perfil_estudiante", None) protege correctamente la
        # relación inversa O2O cuando no existe; encadenar el acceso en una sola
        # expresión (p.estudiante.perfil_estudiante.legajo) evaluaría el atributo
        # ANTES de que getattr pueda capturar RelatedObjectDoesNotExist.
        perfil = getattr(p.estudiante, "perfil_estudiante", None)
        resultados.append(
            {
                "nombre": p.estudiante.get_full_name() or p.estudiante.email,
                "email": p.estudiante.email,
                "legajo": getattr(perfil, "legajo", ""),
                "carrera": getattr(perfil, "carrera", ""),
                "anio_ingreso": getattr(perfil, "anio_ingreso", None),
                "cantidad_familiares": p.formulario.cantidad_familiares,
                "convocatoria": p.convocatoria.nombre,
                "beca": p.beca.nombre,
                "estado_postulacion": p.get_estado_display(),
            }
        )
    return resultados
