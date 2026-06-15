from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from apps.convocatorias.models import Convocatoria
from apps.postulaciones.models import Postulacion

from . import services
from .forms import GenerarRankingForm


def _es_director(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Director").exists()
    )


director_required = user_passes_test(_es_director, login_url="/accounts/login/")


@director_required
def panel_view(request):
    convocatorias = Convocatoria.objects.prefetch_related("postulaciones").order_by(
        "-fecha_apertura"
    )

    resumen = []
    for c in convocatorias:
        posts = c.postulaciones.all()
        resumen.append(
            {
                "convocatoria": c,
                "aprobadas": posts.filter(estado=Postulacion.Estado.APROBADA).count(),
                "procesadas": posts.filter(estado=Postulacion.Estado.PROCESADA).count(),
                "adjudicadas": posts.filter(estado=Postulacion.Estado.ADJUDICADA).count(),
                "tiene_ranking": posts.filter(
                    estado__in=[
                        Postulacion.Estado.ADJUDICADA,
                        Postulacion.Estado.LISTA_ESPERA,
                        Postulacion.Estado.NO_ADJUDICADA,
                    ]
                ).exists(),
            }
        )

    return render(request, "reportes/panel.html", {"resumen": resumen})


@director_required
def procesar_view(request, convocatoria_pk):
    if request.method == "POST":
        convocatoria = get_object_or_404(Convocatoria, pk=convocatoria_pk)
        cantidad = services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
        if cantidad:
            messages.success(request, f"{cantidad} postulaciones procesadas con puntaje.")
        else:
            messages.warning(request, "No hay postulaciones en estado Aprobada para procesar.")
    return redirect("reportes:panel")


@director_required
def ranking_view(request, convocatoria_pk):
    convocatoria = get_object_or_404(Convocatoria, pk=convocatoria_pk)

    postulaciones_procesadas = (
        Postulacion.objects.filter(
            convocatoria=convocatoria,
            estado__in=[
                Postulacion.Estado.PROCESADA,
                Postulacion.Estado.ADJUDICADA,
                Postulacion.Estado.LISTA_ESPERA,
                Postulacion.Estado.NO_ADJUDICADA,
            ],
        )
        .select_related("estudiante", "beca")
        .order_by("-puntaje_socioeconomico", "fecha_envio")
    )

    form = GenerarRankingForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        postulaciones_resultado = services.generar_ranking(
            convocatoria=convocatoria,
            cupo=form.cleaned_data["cupo"],
            cupo_espera=form.cleaned_data["cupo_espera"],
        )
        messages.success(
            request,
            f"Ranking generado: {len(postulaciones_resultado)} postulaciones clasificadas.",
        )
        return redirect("reportes:ranking", convocatoria_pk=convocatoria_pk)

    tiene_ranking = postulaciones_procesadas.filter(
        estado__in=[
            Postulacion.Estado.ADJUDICADA,
            Postulacion.Estado.LISTA_ESPERA,
            Postulacion.Estado.NO_ADJUDICADA,
        ]
    ).exists()

    return render(
        request,
        "reportes/ranking.html",
        {
            "convocatoria": convocatoria,
            "postulaciones": postulaciones_procesadas,
            "form": form,
            "tiene_ranking": tiene_ranking,
        },
    )


@director_required
def exportar_excel_view(request, convocatoria_pk):
    convocatoria = get_object_or_404(Convocatoria, pk=convocatoria_pk)
    xlsx_bytes = services.exportar_ranking_excel(convocatoria=convocatoria)
    nombre = f"ranking_{slugify(convocatoria.nombre)}.xlsx"
    response = HttpResponse(
        xlsx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return response


@director_required
def exportar_pdf_view(request, convocatoria_pk):
    convocatoria = get_object_or_404(Convocatoria, pk=convocatoria_pk)
    pdf_bytes = services.exportar_reporte_pdf(convocatoria=convocatoria, request=request)
    nombre = f"reporte_{slugify(convocatoria.nombre)}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return response
