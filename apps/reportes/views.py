from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from apps.convocatorias.models import Convocatoria
from apps.postulaciones.models import Postulacion

from . import services
from .forms import FiltroDashboardForm, GenerarRankingForm
from .models import Conversacion, ResumenIA


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


@director_required
def dashboard_view(request):
    form = FiltroDashboardForm(request.GET or None)
    convocatoria = fecha_desde = fecha_hasta = None
    if form.is_valid():
        convocatoria = form.cleaned_data["convocatoria"]
        fecha_desde = form.cleaned_data["fecha_desde"]
        fecha_hasta = form.cleaned_data["fecha_hasta"]

    contexto = services.construir_contexto_dashboard(
        convocatoria=convocatoria, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )
    contexto["form"] = form

    template = "reportes/_dashboard_kpis.html" if request.htmx else "reportes/dashboard.html"
    return render(request, template, contexto)


@director_required
def resumen_ia_solicitar_view(request):
    convocatoria_pk = request.POST.get("convocatoria")
    convocatoria = get_object_or_404(Convocatoria, pk=convocatoria_pk) if convocatoria_pk else None
    resumen = services.solicitar_resumen_ia(
        usuario=request.user,
        convocatoria=convocatoria,
        prompt_adicional=request.POST.get("prompt_adicional", ""),
    )
    return render(request, "reportes/_resumen_ia_estado.html", {"resumen": resumen})


@director_required
def resumen_ia_estado_view(request, resumen_pk):
    resumen = get_object_or_404(ResumenIA, pk=resumen_pk)
    return render(request, "reportes/_resumen_ia_estado.html", {"resumen": resumen})


@director_required
def resumen_ia_exportar_pdf_view(request, resumen_pk):
    resumen = get_object_or_404(ResumenIA, pk=resumen_pk)
    pdf_bytes = services.exportar_resumen_ia_pdf(resumen_pk=resumen.pk)
    nombre = f"resumen_ia_{resumen.pk}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return response


@director_required
def chat_lista_view(request):
    if request.method == "POST":
        conversacion = services.crear_conversacion(usuario=request.user)
        return redirect("reportes:chat_detalle", conversacion_pk=conversacion.pk)

    conversaciones = Conversacion.objects.filter(usuario=request.user)
    return render(request, "reportes/chat_lista.html", {"conversaciones": conversaciones})


@director_required
def chat_detalle_view(request, conversacion_pk):
    conversacion = get_object_or_404(Conversacion, pk=conversacion_pk, usuario=request.user)

    if request.method == "POST":
        contenido = request.POST.get("contenido", "").strip()
        if contenido:
            services.enviar_mensaje_chat(conversacion=conversacion, contenido=contenido)
        return render(request, "reportes/_chat_mensajes.html", {"conversacion": conversacion})

    return render(request, "reportes/chat_detalle.html", {"conversacion": conversacion})


@director_required
def chat_estado_view(request, conversacion_pk):
    conversacion = get_object_or_404(Conversacion, pk=conversacion_pk, usuario=request.user)
    return render(request, "reportes/_chat_mensajes.html", {"conversacion": conversacion})
