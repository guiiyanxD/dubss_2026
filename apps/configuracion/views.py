from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .services import ConfiguracionService
from .forms import (
    FormularioSocioeconomicoForm,
    IntegranteFamiliarFormSet,
    OpcionDependenciaForm,
    OpcionDiscapacidadForm,
    OpcionOtroBeneficioForm,
    RangoGrupoFamiliarForm,
    RangoIngresoForm,
    RangoInfraestructuraForm,
    TipoOcupacionSostenForm,
    TipoTenenciaViviendaForm,
)
from .models import (
    FormularioSocioeconomico,
    OpcionDependencia,
    OpcionDiscapacidad,
    OpcionOtroBeneficio,
    RangoGrupoFamiliar,
    RangoIngreso,
    RangoInfraestructura,
    TipoOcupacionSosten,
    TipoTenenciaVivienda,
)

_es_director = user_passes_test(lambda u: u.is_superuser or u.get_rol() == "Director")

# ---------------------------------------------------------------------------
# Registro de catálogos socioeconómicos
# ---------------------------------------------------------------------------

REGISTRO_CATALOGOS = {
    "dependencia": {
        "modelo": OpcionDependencia,
        "form_class": OpcionDependenciaForm,
        "titulo": "Dependencia económica",
        "seccion": "Sección 2a°",
        "columnas_extra": [],
    },
    "ocupacion": {
        "modelo": TipoOcupacionSosten,
        "form_class": TipoOcupacionSostenForm,
        "titulo": "Tipo de ocupación del sostén",
        "seccion": "Sección 2b°",
        "columnas_extra": [{"key": "documento_adjuntar", "label": "Documento a adjuntar"}],
    },
    "ingreso": {
        "modelo": RangoIngreso,
        "form_class": RangoIngresoForm,
        "titulo": "Rango de ingreso mensual familiar",
        "seccion": "Sección 2c°",
        "columnas_extra": [
            {"key": "monto_minimo", "label": "Mínimo (Bs.)"},
            {"key": "monto_maximo", "label": "Máximo (Bs.)"},
        ],
    },
    "grupo-familiar": {
        "modelo": RangoGrupoFamiliar,
        "form_class": RangoGrupoFamiliarForm,
        "titulo": "Grupo familiar",
        "seccion": "Sección 3°",
        "columnas_extra": [
            {"key": "cantidad_minima", "label": "Mín."},
            {"key": "cantidad_maxima", "label": "Máx."},
        ],
    },
    "tenencia": {
        "modelo": TipoTenenciaVivienda,
        "form_class": TipoTenenciaViviendaForm,
        "titulo": "Tenencia de vivienda",
        "seccion": "Sección 6°",
        "columnas_extra": [{"key": "documento_adjuntar", "label": "Documento a adjuntar"}],
    },
    "infraestructura": {
        "modelo": RangoInfraestructura,
        "form_class": RangoInfraestructuraForm,
        "titulo": "Infraestructura de la vivienda",
        "seccion": "Sección 7°",
        "columnas_extra": [
            {"key": "total_minimo", "label": "Ambientes mín."},
            {"key": "total_maximo", "label": "Ambientes máx."},
        ],
    },
    "otro-beneficio": {
        "modelo": OpcionOtroBeneficio,
        "form_class": OpcionOtroBeneficioForm,
        "titulo": "Otro beneficio universitario",
        "seccion": "Sección 8°",
        "columnas_extra": [],
    },
    "discapacidad": {
        "modelo": OpcionDiscapacidad,
        "form_class": OpcionDiscapacidadForm,
        "titulo": "Discapacidad",
        "seccion": "Sección 9°",
        "columnas_extra": [],
    },
}


def _get_catalogo_o_404(slug):
    entry = REGISTRO_CATALOGOS.get(slug)
    if entry is None:
        from django.http import Http404
        raise Http404(f"Catálogo '{slug}' no existe.")
    return entry


def _serializar_entrada(obj, columnas_extra):
    extras = [getattr(obj, col["key"], None) for col in columnas_extra]
    return {"pk": obj.pk, "nombre": obj.nombre, "valor_puntaje": obj.valor_puntaje, "activo": obj.activo, "extras": extras}

CAMPOS_FORMULARIO = [
    "cantidad_familiares",
    "tiene_beca_previa",
    "numero_celular",
    "telefono_referencia",
    "dependencia_economica",
    "tipo_ocupacion_sosten",
    "rango_ingreso",
    "tiene_hijos",
    "cantidad_hijos",
    "lugar_procedencia",
    "residencia_lugar",
    "residencia_provincia",
    "residencia_zona_anillo",
    "residencia_barrio",
    "residencia_calle",
    "tipo_tenencia_vivienda",
    "dormitorios",
    "banos",
    "comedores",
    "salas",
    "patios",
    "detalle_otro_beneficio",
    "tiene_discapacidad",
    "detalle_discapacidad",
    "observaciones",
]


@login_required
def formulario_view(request):
    try:
        formulario = FormularioSocioeconomico.objects.get(usuario=request.user)
        initial = {campo: getattr(formulario, campo) for campo in CAMPOS_FORMULARIO}
        integrantes_initial = list(
            formulario.integrantes_familiares.values(
                "nombre_completo", "parentesco", "edad", "ocupacion", "observacion"
            )
        )
    except FormularioSocioeconomico.DoesNotExist:
        formulario = None
        initial = {}
        integrantes_initial = []

    form = FormularioSocioeconomicoForm(request.POST or None, initial=initial)
    formset = IntegranteFamiliarFormSet(
        request.POST or None, initial=integrantes_initial, prefix="integrantes"
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        formulario = ConfiguracionService.guardar_formulario(
            estudiante=request.user,
            **{campo: form.cleaned_data.get(campo) for campo in CAMPOS_FORMULARIO},
        )
        integrantes = [
            {
                "nombre_completo": f.cleaned_data["nombre_completo"],
                "parentesco": f.cleaned_data["parentesco"],
                "edad": f.cleaned_data["edad"],
                "ocupacion": f.cleaned_data.get("ocupacion", ""),
                "observacion": f.cleaned_data.get("observacion", ""),
            }
            for f in formset.forms
            if f.cleaned_data and not f.cleaned_data.get("DELETE") and f.tiene_datos()
        ]
        ConfiguracionService.guardar_integrantes_familiares(formulario=formulario, integrantes=integrantes)
        messages.success(request, "Formulario guardado correctamente.")
        return redirect("configuracion:formulario")

    return render(
        request,
        "configuracion/formulario.html",
        {"form": form, "formset": formset, "formulario": formulario},
    )


@login_required
@_es_director
def catalogos_socioeconomicos_view(request):
    catalogos = []
    for slug, entry in REGISTRO_CATALOGOS.items():
        modelo = entry["modelo"]
        cols = entry["columnas_extra"]
        filas = [_serializar_entrada(obj, cols) for obj in modelo.objects.all()]
        catalogos.append({
            "slug": slug,
            "titulo": entry["titulo"],
            "seccion": entry["seccion"],
            "columnas_extra": cols,
            "filas": filas,
        })
    return render(request, "configuracion/catalogos.html", {"catalogos": catalogos})


@login_required
@_es_director
def catalogo_nueva_entrada_view(request, slug):
    entry = _get_catalogo_o_404(slug)
    form_class = entry["form_class"]
    cols = entry["columnas_extra"]

    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            try:
                obj = ConfiguracionService.crear_entrada_catalogo(entry["modelo"], form.cleaned_data)
                entrada = _serializar_entrada(obj, cols)
                return render(request, "configuracion/_catalogo_fila.html", {
                    "entrada": entrada, "slug": slug, "columnas_extra": cols,
                })
            except ValueError as e:
                form.add_error("nombre", str(e))
        return render(request, "configuracion/_catalogo_form_nuevo.html", {
            "form": form, "slug": slug, "columnas_extra": cols,
        }, status=422)

    form = form_class()
    return render(request, "configuracion/_catalogo_form_nuevo.html", {
        "form": form, "slug": slug, "columnas_extra": cols,
    })


@login_required
@_es_director
def catalogo_editar_entrada_view(request, slug, pk):
    entry = _get_catalogo_o_404(slug)
    modelo = entry["modelo"]
    form_class = entry["form_class"]
    cols = entry["columnas_extra"]
    obj = get_object_or_404(modelo, pk=pk)

    if request.method == "POST":
        form = form_class(request.POST, instance=obj)
        if form.is_valid():
            try:
                obj = ConfiguracionService.editar_entrada_catalogo(obj, form.cleaned_data)
                entrada = _serializar_entrada(obj, cols)
                return render(request, "configuracion/_catalogo_fila.html", {
                    "entrada": entrada, "slug": slug, "columnas_extra": cols,
                })
            except ValueError as e:
                form.add_error("nombre", str(e))
        return render(request, "configuracion/_catalogo_fila_editar.html", {
            "form": form, "slug": slug, "pk": pk, "columnas_extra": cols,
        }, status=422)

    form = form_class(instance=obj)
    return render(request, "configuracion/_catalogo_fila_editar.html", {
        "form": form, "slug": slug, "pk": pk, "columnas_extra": cols,
    })


@login_required
@_es_director
@require_POST
def catalogo_toggle_activo_view(request, slug, pk):
    entry = _get_catalogo_o_404(slug)
    obj = get_object_or_404(entry["modelo"], pk=pk)
    cols = entry["columnas_extra"]
    obj = ConfiguracionService.toggle_activo_catalogo(obj)
    entrada = _serializar_entrada(obj, cols)
    return render(request, "configuracion/_catalogo_fila.html", {
        "entrada": entrada, "slug": slug, "columnas_extra": cols,
    })


@login_required
@_es_director
def catalogo_cancelar_edicion_view(request, slug, pk):
    entry = _get_catalogo_o_404(slug)
    obj = get_object_or_404(entry["modelo"], pk=pk)
    cols = entry["columnas_extra"]
    entrada = _serializar_entrada(obj, cols)
    return render(request, "configuracion/_catalogo_fila.html", {
        "entrada": entrada, "slug": slug, "columnas_extra": cols,
    })


@login_required
@_es_director
def catalogo_eliminar_entrada_view(request, slug, pk):
    entry = _get_catalogo_o_404(slug)
    obj = get_object_or_404(entry["modelo"], pk=pk)
    if request.method in ("POST", "DELETE"):
        ConfiguracionService.eliminar_entrada_catalogo(obj)
        return HttpResponse("")
    return HttpResponseBadRequest()


@login_required
def integrante_familiar_nueva_fila(request):
    """Devuelve el HTML de una fila vacía adicional del formset de integrantes."""
    try:
        total_forms = int(request.GET.get("integrantes-TOTAL_FORMS", 0))
    except ValueError:
        return HttpResponseBadRequest()

    if total_forms >= IntegranteFamiliarFormSet.max_num:
        return HttpResponseBadRequest("Se alcanzó el máximo de integrantes.")

    formset = IntegranteFamiliarFormSet(prefix="integrantes")
    fila_form = formset.empty_form
    fila_form.prefix = f"integrantes-{total_forms}"

    nuevo_total = total_forms + 1
    return render(
        request,
        "configuracion/_integrante_fila.html",
        {
            "integrante_form": fila_form,
            "es_existente": False,
            "nuevo_total_forms": nuevo_total,
            "deshabilitar_boton_agregar": nuevo_total >= IntegranteFamiliarFormSet.max_num,
        },
    )
