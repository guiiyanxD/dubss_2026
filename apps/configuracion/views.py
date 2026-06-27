from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render

from . import services
from .forms import FormularioSocioeconomicoForm, IntegranteFamiliarFormSet
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
        formulario = services.guardar_formulario(
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
        services.guardar_integrantes_familiares(formulario=formulario, integrantes=integrantes)
        messages.success(request, "Formulario guardado correctamente.")
        return redirect("configuracion:formulario")

    return render(
        request,
        "configuracion/formulario.html",
        {"form": form, "formset": formset, "formulario": formulario},
    )


def _serializar_catalogo(qs, campos_extra=None):
    campos_extra = campos_extra or []
    filas = []
    for obj in qs:
        extras = [getattr(obj, campo, None) for campo in campos_extra]
        filas.append({
            "nombre": obj.nombre,
            "valor_puntaje": obj.valor_puntaje,
            "activo": obj.activo,
            "extras": extras,
        })
    return filas


@login_required
@_es_director
def catalogos_socioeconomicos_view(request):
    catalogos = [
        {
            "titulo": "Dependencia económica",
            "seccion": "Sección 2a°",
            "admin_url": "configuracion/opciondependencia",
            "columnas_extra": [],
            "filas": _serializar_catalogo(OpcionDependencia.objects.all()),
        },
        {
            "titulo": "Tipo de ocupación del sostén",
            "seccion": "Sección 2b°",
            "admin_url": "configuracion/tipocupacionsosten",
            "columnas_extra": [],
            "filas": _serializar_catalogo(TipoOcupacionSosten.objects.all()),
        },
        {
            "titulo": "Rango de ingreso mensual familiar",
            "seccion": "Sección 2c°",
            "admin_url": "configuracion/rangoingreso",
            "columnas_extra": [
                {"key": "monto_minimo", "label": "Mínimo (Bs.)"},
                {"key": "monto_maximo", "label": "Máximo (Bs.)"},
            ],
            "filas": _serializar_catalogo(
                RangoIngreso.objects.all(), ["monto_minimo", "monto_maximo"]
            ),
        },
        {
            "titulo": "Grupo familiar",
            "seccion": "Sección 3°",
            "admin_url": "configuracion/rangogrupofamiliar",
            "columnas_extra": [
                {"key": "cantidad_minima", "label": "Mín. miembros"},
                {"key": "cantidad_maxima", "label": "Máx. miembros"},
            ],
            "filas": _serializar_catalogo(
                RangoGrupoFamiliar.objects.all(), ["cantidad_minima", "cantidad_maxima"]
            ),
        },
        {
            "titulo": "Tenencia de vivienda",
            "seccion": "Sección 6°",
            "admin_url": "configuracion/tipotenancivienda",
            "columnas_extra": [],
            "filas": _serializar_catalogo(TipoTenenciaVivienda.objects.all()),
        },
        {
            "titulo": "Infraestructura de la vivienda",
            "seccion": "Sección 7°",
            "admin_url": "configuracion/rangoinfraestructura",
            "columnas_extra": [
                {"key": "total_minimo", "label": "Ambientes mín."},
                {"key": "total_maximo", "label": "Ambientes máx."},
            ],
            "filas": _serializar_catalogo(
                RangoInfraestructura.objects.all(), ["total_minimo", "total_maximo"]
            ),
        },
        {
            "titulo": "Otro beneficio universitario",
            "seccion": "Sección 8°",
            "admin_url": "configuracion/opcionotrobeneficio",
            "columnas_extra": [],
            "filas": _serializar_catalogo(OpcionOtroBeneficio.objects.all()),
        },
        {
            "titulo": "Discapacidad",
            "seccion": "Sección 9°",
            "admin_url": "configuracion/opciondiscapacidad",
            "columnas_extra": [],
            "filas": _serializar_catalogo(OpcionDiscapacidad.objects.all()),
        },
    ]
    return render(request, "configuracion/catalogos.html", {"catalogos": catalogos})


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
