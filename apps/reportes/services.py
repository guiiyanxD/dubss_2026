import io
from decimal import Decimal

from django.template.loader import render_to_string
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from apps.postulaciones.models import Postulacion
from apps.postulaciones.signals import resultado_adjudicacion

from . import charts, selectors


def procesar_formularios_socioeconomicos(*, convocatoria):
    """CU23 — Calcula el puntaje socioeconómico para postulaciones APROBADAS.

    Usa Pandas para normalizar y ponderar los factores socioeconómicos.
    Actualiza cada Postulacion con su puntaje y la marca como PROCESADA.

    Args:
        convocatoria: Instancia de Convocatoria.

    Returns:
        Cantidad de postulaciones procesadas.
    """
    import pandas as pd

    postulaciones = list(
        Postulacion.objects.filter(
            convocatoria=convocatoria,
            estado=Postulacion.Estado.APROBADA,
        ).select_related("formulario")
    )

    if not postulaciones:
        return 0

    data = [
        {
            "id": p.pk,
            "ingreso": float(p.formulario.ingreso_mensual_familiar),
            "familiares": p.formulario.cantidad_familiares,
            "desempleado": p.formulario.situacion_laboral == "DESEMPLEADO",
            "no_propietario": p.formulario.situacion_habitacional != "PROPIETARIO",
            "sin_beca_previa": not p.formulario.tiene_beca_previa,
        }
        for p in postulaciones
    ]

    df = pd.DataFrame(data)

    ingreso_max = df["ingreso"].max()
    familiares_max = df["familiares"].max()

    df["ingreso_norm"] = df["ingreso"] / ingreso_max if ingreso_max > 0 else 0.0
    df["familiares_norm"] = df["familiares"] / familiares_max if familiares_max > 0 else 0.0

    df["puntaje"] = (
        (1 - df["ingreso_norm"]) * 40
        + df["desempleado"].astype(int) * 20
        + df["familiares_norm"] * 20
        + df["no_propietario"].astype(int) * 10
        + df["sin_beca_previa"].astype(int) * 10
    ).round(2)

    for _, row in df.iterrows():
        Postulacion.objects.filter(pk=int(row["id"])).update(
            puntaje_socioeconomico=Decimal(str(row["puntaje"])),
            estado=Postulacion.Estado.PROCESADA,
        )

    return len(postulaciones)


def generar_ranking(*, convocatoria, cupo, cupo_espera=None):
    """CU24 — Ordena postulaciones PROCESADAS y asigna resultados finales.

    Args:
        convocatoria: Instancia de Convocatoria.
        cupo: Número de postulaciones a adjudicar.
        cupo_espera: Número de postulaciones en lista de espera (default = cupo).

    Returns:
        Lista de Postulacion con estado actualizado, ordenadas por puntaje.
    """
    if cupo_espera is None:
        cupo_espera = cupo

    postulaciones = list(
        Postulacion.objects.filter(
            convocatoria=convocatoria,
            estado=Postulacion.Estado.PROCESADA,
        )
        .select_related("estudiante", "beca")
        .order_by("-puntaje_socioeconomico", "fecha_envio")
    )

    for i, p in enumerate(postulaciones):
        if i < cupo:
            p.estado = Postulacion.Estado.ADJUDICADA
        elif i < cupo + cupo_espera:
            p.estado = Postulacion.Estado.LISTA_ESPERA
        else:
            p.estado = Postulacion.Estado.NO_ADJUDICADA

        p.save(update_fields=["estado"])
        resultado_adjudicacion.send(sender=Postulacion, postulacion=p)

    return postulaciones


def exportar_ranking_excel(*, convocatoria):
    """CU25 — Genera un archivo Excel con el ranking de la convocatoria.

    Args:
        convocatoria: Instancia de Convocatoria.

    Returns:
        Bytes del archivo .xlsx.
    """
    postulaciones = (
        Postulacion.objects.filter(
            convocatoria=convocatoria,
            estado__in=[
                Postulacion.Estado.ADJUDICADA,
                Postulacion.Estado.LISTA_ESPERA,
                Postulacion.Estado.NO_ADJUDICADA,
            ],
        )
        .select_related("estudiante", "beca")
        .order_by("-puntaje_socioeconomico", "fecha_envio")
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Ranking"

    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    headers = ["Pos.", "Apellido", "Nombre", "Email", "Beca", "Puntaje", "Resultado"]
    col_widths = [6, 20, 20, 30, 25, 12, 20]

    for col, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[cell.column_letter].width = width

    estado_colores = {
        Postulacion.Estado.ADJUDICADA: "C6EFCE",
        Postulacion.Estado.LISTA_ESPERA: "FFEB9C",
        Postulacion.Estado.NO_ADJUDICADA: "FFC7CE",
    }

    for pos, p in enumerate(postulaciones, start=1):
        fila = [
            pos,
            p.estudiante.last_name,
            p.estudiante.first_name,
            p.estudiante.email,
            p.beca.nombre,
            float(p.puntaje_socioeconomico or 0),
            p.get_estado_display(),
        ]
        color = estado_colores.get(p.estado, "FFFFFF")
        fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        for col, valor in enumerate(fila, start=1):
            cell = ws.cell(row=pos + 1, column=col, value=valor)
            cell.fill = fill

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def exportar_reporte_pdf(*, convocatoria, request=None):
    """CU26 — Genera un PDF con el reporte de la convocatoria.

    Args:
        convocatoria: Instancia de Convocatoria.
        request: HttpRequest opcional (para URLs absolutas en el PDF).

    Returns:
        Bytes del archivo .pdf.
    """
    from weasyprint import HTML

    postulaciones = list(
        Postulacion.objects.filter(
            convocatoria=convocatoria,
            estado__in=[
                Postulacion.Estado.ADJUDICADA,
                Postulacion.Estado.LISTA_ESPERA,
                Postulacion.Estado.NO_ADJUDICADA,
            ],
        )
        .select_related("estudiante", "beca")
        .order_by("-puntaje_socioeconomico", "fecha_envio")
    )

    total = len(postulaciones)
    adjudicadas = sum(1 for p in postulaciones if p.estado == Postulacion.Estado.ADJUDICADA)
    espera = sum(1 for p in postulaciones if p.estado == Postulacion.Estado.LISTA_ESPERA)
    no_adjudicadas = total - adjudicadas - espera

    contexto = {
        "convocatoria": convocatoria,
        "postulaciones": postulaciones,
        "total": total,
        "adjudicadas": adjudicadas,
        "espera": espera,
        "no_adjudicadas": no_adjudicadas,
    }

    html_str = render_to_string("reportes/reporte_pdf.html", contexto)
    pdf_bytes = HTML(string=html_str).write_pdf()
    return pdf_bytes


def construir_contexto_dashboard(*, convocatoria=None, fecha_desde=None, fecha_hasta=None):
    """CU26 — Orquesta selectors.py + charts.py para el dashboard de KPIs.

    Args:
        convocatoria: Instancia de Convocatoria para filtrar, o None para todas.
        fecha_desde: date mínima de fecha_creacion a incluir, o None.
        fecha_hasta: date máxima de fecha_creacion a incluir, o None.

    Returns:
        Dict listo para renderizar en dashboard.html / _dashboard_kpis.html.
    """
    filtro = {"convocatoria": convocatoria, "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta}

    demanda_beca = selectors.postulaciones_por_beca(**filtro)
    tasa_adj_conv = selectors.tasa_adjudicacion_por_convocatoria()
    espera_conv = selectors.tamano_lista_espera_por_convocatoria()

    embudo = selectors.embudo_estados(**filtro)
    rechazos = selectors.desglose_rechazos(**filtro)
    tiempos_etapa = selectors.tiempos_promedio_por_etapa(convocatoria=convocatoria)

    validacion_doc = selectors.validacion_por_tipo_documento()
    mayor_rechazo = selectors.documento_mayor_rechazo()

    ingreso = selectors.distribucion_ingreso_familiar(convocatoria=convocatoria)
    puntaje = selectors.distribucion_puntaje_socioeconomico(convocatoria=convocatoria)
    indicadores = selectors.indicadores_generales(convocatoria=convocatoria)

    punto_corte = selectors.punto_corte_por_convocatoria()

    carreras = selectors.postulantes_por_carrera(convocatoria=convocatoria)
    tasa_carrera = selectors.tasa_adjudicacion_por_carrera()
    anio_ingreso = selectors.postulantes_por_anio_ingreso(convocatoria=convocatoria)

    entrega = selectors.tasa_entrega_notificaciones(
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )
    latencia = selectors.latencia_envio_notificaciones()

    if convocatoria is not None:
        comparacion = selectors.comparacion_puntaje_por_resultado(convocatoria=convocatoria)
        grafico_comparacion = charts.fig_boxplot(
            datos=comparacion, titulo="Puntaje socioeconómico por resultado"
        )
    else:
        grafico_comparacion = charts.vacio(
            "Seleccioná una convocatoria específica para comparar puntajes por resultado."
        )

    return {
        "grafico_demanda_beca": charts.fig_barras(**demanda_beca, titulo="Postulaciones por beca"),
        "grafico_tasa_adjudicacion_convocatoria": charts.fig_barras(
            **tasa_adj_conv,
            titulo="Tasa de adjudicación por convocatoria",
            horizontal=True,
            sufijo="%",
        ),
        "grafico_lista_espera": charts.fig_barras(
            **espera_conv, titulo="Tamaño de lista de espera por convocatoria"
        ),
        "grafico_embudo": charts.fig_funnel(**embudo, titulo="Embudo de postulaciones"),
        "grafico_rechazos": charts.fig_donut(**rechazos, titulo="Motivos de rechazo"),
        "grafico_tiempos_etapa": charts.fig_barras(
            **tiempos_etapa, titulo="Tiempo promedio entre etapas", horizontal=True, sufijo=" días"
        ),
        "grafico_validacion_documental": charts.fig_barras_apiladas(
            etiquetas=validacion_doc["etiquetas"],
            series={
                "Aprobado": validacion_doc["aprobado"],
                "Rechazado": validacion_doc["rechazado"],
                "Pendiente": validacion_doc["pendiente"],
            },
            titulo="Validación documental por tipo",
        ),
        "documento_mayor_rechazo": mayor_rechazo,
        "grafico_ingreso_familiar": charts.fig_histograma(
            valores=ingreso["valores"],
            titulo="Distribución de ingreso familiar",
            eje_x="Ingreso mensual familiar (ARS)",
        ),
        "grafico_puntaje": charts.fig_histograma(
            valores=puntaje["valores"],
            titulo="Distribución de puntaje socioeconómico",
            eje_x="Puntaje",
        ),
        "grafico_comparacion_puntaje": grafico_comparacion,
        "graficos_distribucion_choices": {
            campo: charts.fig_donut(
                **selectors.distribucion_choices(campo, convocatoria=convocatoria), titulo=titulo
            )
            for campo, titulo in [
                ("situacion_laboral", "Situación laboral"),
                ("situacion_habitacional", "Situación habitacional"),
                ("dependencia_economica", "Dependencia económica"),
                ("tipo_tenencia_vivienda", "Tenencia de vivienda"),
            ]
        },
        "indicadores_generales": indicadores,
        "punto_corte_por_convocatoria": list(
            zip(punto_corte["etiquetas"], punto_corte["valores"], strict=True)
        ),
        "grafico_carreras": charts.fig_barras(
            **carreras, titulo="Postulantes por carrera (top 10)", horizontal=True
        ),
        "grafico_tasa_carrera": charts.fig_barras(
            **tasa_carrera, titulo="Tasa de adjudicación por carrera", horizontal=True, sufijo="%"
        ),
        "grafico_anio_ingreso": charts.fig_barras(
            **anio_ingreso, titulo="Postulantes por año de ingreso"
        ),
        "grafico_entrega_notificaciones": charts.fig_donut(
            **entrega, titulo="Estado de envío de notificaciones"
        ),
        "latencia_notificaciones": latencia,
    }
