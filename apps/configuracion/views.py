from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render

from . import services
from .forms import FormularioSocioeconomicoForm, IntegranteFamiliarFormSet
from .models import FormularioSocioeconomico

CAMPOS_FORMULARIO = [
    "situacion_laboral",
    "ingreso_mensual_familiar",
    "cantidad_familiares",
    "situacion_habitacional",
    "tiene_beca_previa",
    "numero_celular",
    "telefono_referencia",
    "dependencia_economica",
    "tipo_ocupacion_sosten",
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
