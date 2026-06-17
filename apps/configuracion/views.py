from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    "observaciones",
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
            if f.cleaned_data and f.tiene_datos()
        ]
        services.guardar_integrantes_familiares(formulario=formulario, integrantes=integrantes)
        messages.success(request, "Formulario guardado correctamente.")
        return redirect("configuracion:formulario")

    return render(
        request,
        "configuracion/formulario.html",
        {"form": form, "formset": formset, "formulario": formulario},
    )
