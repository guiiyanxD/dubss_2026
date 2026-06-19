"""Gráficos estáticos (Matplotlib) para incrustar en PDFs generados con WeasyPrint.

WeasyPrint no ejecuta JavaScript, así que los gráficos interactivos de Plotly
(`charts.py`) no se ven ahí — estos builders generan PNG en base64 a partir de los
mismos dicts de `selectors.py` que ya consume el dashboard.
"""

import base64
import io

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

COLOR_PRIMARIO = "#880000"
COLOR_SECUNDARIO = "#2a3964"


def _figura_a_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def grafico_embudo_estatico(*, etiquetas, valores, titulo):
    if not etiquetas:
        return None
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.barh(etiquetas, valores, color=COLOR_PRIMARIO)
    ax.set_title(titulo)
    ax.invert_yaxis()
    return _figura_a_base64(fig)


def grafico_histograma_estatico(*, valores, titulo, eje_x):
    if not valores:
        return None
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.hist(valores, bins=10, color=COLOR_SECUNDARIO)
    ax.set_title(titulo)
    ax.set_xlabel(eje_x)
    ax.set_ylabel("Cantidad")
    return _figura_a_base64(fig)
