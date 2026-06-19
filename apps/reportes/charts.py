"""Construcción de figuras Plotly para el dashboard de KPIs (CU26).

Recibe los dicts planos que produce `selectors.py` y devuelve HTML/JS embebible
(`fig.to_html(full_html=False, include_plotlyjs=False)`). `plotly.js` se carga una sola
vez por CDN en `dashboard.html`, no en cada figura.
"""

import plotly.graph_objects as go

COLOR_PRIMARIO = "#880000"
PALETA = ["#880000", "#2a3964", "#c9a227", "#4c9a5a", "#9b6fd1", "#c0392b", "#16a085"]


def _to_html(fig, *, altura=380):
    fig.update_layout(
        margin={"l": 40, "r": 20, "t": 40, "b": 40}, height=altura, template="plotly_white"
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def vacio(mensaje="No hay datos disponibles para este filtro."):
    """Marcador de posición cuando un KPI no tiene datos para los filtros activos."""
    return f'<div class="text-center text-muted py-5">{mensaje}</div>'


def fig_barras(*, etiquetas, valores, titulo, horizontal=False, sufijo=""):
    if not etiquetas:
        return vacio()
    texto = [f"{v}{sufijo}" for v in valores]
    if horizontal:
        fig = go.Figure(
            go.Bar(y=etiquetas, x=valores, orientation="h", text=texto, marker_color=COLOR_PRIMARIO)
        )
    else:
        fig = go.Figure(go.Bar(x=etiquetas, y=valores, text=texto, marker_color=COLOR_PRIMARIO))
    fig.update_traces(textposition="outside")
    fig.update_layout(title=titulo)
    return _to_html(fig)


def fig_barras_apiladas(*, etiquetas, series, titulo):
    """series: dict {nombre_serie: [valores...]} alineados con `etiquetas`."""
    if not etiquetas:
        return vacio()
    fig = go.Figure()
    for (nombre, valores), color in zip(series.items(), PALETA, strict=False):
        fig.add_bar(name=nombre, x=etiquetas, y=valores, marker_color=color)
    fig.update_layout(barmode="stack", title=titulo)
    return _to_html(fig)


def fig_funnel(*, etiquetas, valores, titulo):
    if not etiquetas:
        return vacio()
    fig = go.Figure(go.Funnel(y=etiquetas, x=valores, marker={"color": PALETA}))
    fig.update_layout(title=titulo)
    return _to_html(fig, altura=420)


def fig_donut(*, etiquetas, valores, titulo):
    if not etiquetas or not any(valores):
        return vacio()
    fig = go.Figure(go.Pie(labels=etiquetas, values=valores, hole=0.55, marker={"colors": PALETA}))
    fig.update_layout(title=titulo)
    return _to_html(fig)


def fig_histograma(*, valores, titulo, eje_x):
    if not valores:
        return vacio()
    fig = go.Figure(go.Histogram(x=valores, marker_color=COLOR_PRIMARIO))
    fig.update_layout(title=titulo, xaxis_title=eje_x, yaxis_title="Cantidad de postulantes")
    return _to_html(fig)


def fig_boxplot(*, datos, titulo):
    """datos: dict {etiqueta_resultado: [puntajes...]}."""
    if not any(datos.values()):
        return vacio("Esta convocatoria todavía no tiene postulaciones con resultado final.")
    fig = go.Figure()
    for (nombre, valores), color in zip(datos.items(), PALETA, strict=False):
        fig.add_box(name=nombre, y=valores, marker_color=color)
    fig.update_layout(title=titulo, yaxis_title="Puntaje socioeconómico")
    return _to_html(fig)
