from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from . import services
from .forms import FormularioSocioeconomicoForm
from .models import FormularioSocioeconomico


@login_required
def formulario_view(request):
    try:
        formulario = FormularioSocioeconomico.objects.get(usuario=request.user)
        initial = {
            "situacion_laboral": formulario.situacion_laboral,
            "ingreso_mensual_familiar": formulario.ingreso_mensual_familiar,
            "cantidad_familiares": formulario.cantidad_familiares,
            "situacion_habitacional": formulario.situacion_habitacional,
            "tiene_beca_previa": formulario.tiene_beca_previa,
            "observaciones": formulario.observaciones,
        }
    except FormularioSocioeconomico.DoesNotExist:
        formulario = None
        initial = {}

    form = FormularioSocioeconomicoForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        services.guardar_formulario(
            estudiante=request.user,
            situacion_laboral=form.cleaned_data["situacion_laboral"],
            ingreso_mensual_familiar=form.cleaned_data["ingreso_mensual_familiar"],
            cantidad_familiares=form.cleaned_data["cantidad_familiares"],
            situacion_habitacional=form.cleaned_data["situacion_habitacional"],
            tiene_beca_previa=form.cleaned_data["tiene_beca_previa"],
            observaciones=form.cleaned_data.get("observaciones", ""),
        )
        messages.success(request, "Formulario guardado correctamente.")
        return redirect("configuracion:formulario")

    return render(
        request, "configuracion/formulario.html", {"form": form, "formulario": formulario}
    )
