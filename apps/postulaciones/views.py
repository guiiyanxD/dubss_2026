from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from apps.convocatorias.models import Convocatoria

from . import services
from .exceptions import (
    BecaNoDisponibleError,
    ConvocatoriaNoVigenteError,
    DocumentoNoAprobadoError,
    FormularioIncompletoError,
    PostulacionActivaExistenteError,
    TransicionEstadoInvalidaError,
)
from .forms import (
    DigitalizarDocumentoForm,
    IniciarPostulacionForm,
    VerificarIdentidadForm,
)
from .models import DocumentoPostulacion, Postulacion


def _es_staff(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=["Director", "Operador"]).exists()
    )


staff_required = user_passes_test(_es_staff, login_url="/accounts/login/")


# ---------------------------------------------------------------------------
# Vistas del Estudiante
# ---------------------------------------------------------------------------


@login_required
def mis_postulaciones_view(request):
    postulaciones = services.listar_postulaciones_estudiante(estudiante=request.user)
    return render(request, "postulaciones/mis_postulaciones.html", {"postulaciones": postulaciones})


@login_required
def iniciar_postulacion_view(request, convocatoria_pk):
    convocatoria = get_object_or_404(
        Convocatoria, pk=convocatoria_pk, estado=Convocatoria.Estado.PUBLICADA
    )
    form = IniciarPostulacionForm(request.POST or None, convocatoria=convocatoria)

    if request.method == "POST" and form.is_valid():
        try:
            postulacion = services.iniciar_postulacion(
                estudiante=request.user,
                convocatoria=convocatoria,
                beca=form.cleaned_data["beca"],
            )
            messages.success(
                request, "Postulación iniciada. Revisala y enviala cuando estés listo."
            )
            return redirect("postulaciones:detalle", pk=postulacion.pk)
        except FormularioIncompletoError as e:
            messages.error(request, str(e))
            return redirect("configuracion:formulario")
        except PostulacionActivaExistenteError as e:
            messages.error(request, str(e))
            return redirect("postulaciones:lista")
        except (ConvocatoriaNoVigenteError, BecaNoDisponibleError) as e:
            messages.error(request, str(e))

    return render(
        request,
        "postulaciones/iniciar.html",
        {"form": form, "convocatoria": convocatoria},
    )


@login_required
def detalle_postulacion_view(request, pk):
    postulacion = get_object_or_404(
        Postulacion.objects.select_related("convocatoria", "beca", "formulario").prefetch_related(
            "documentos__tipo_documento"
        ),
        pk=pk,
    )
    # Estudiante solo ve sus propias postulaciones; staff ve todas
    if not _es_staff(request.user) and postulacion.estudiante != request.user:
        messages.error(request, "No tenés permiso para ver esta postulación.")
        return redirect("postulaciones:lista")

    return render(request, "postulaciones/detalle.html", {"postulacion": postulacion})


@login_required
def enviar_postulacion_view(request, pk):
    if request.method == "POST":
        postulacion = get_object_or_404(Postulacion, pk=pk, estudiante=request.user)
        try:
            services.enviar_postulacion(postulacion=postulacion)
            messages.success(request, "Postulación enviada correctamente.")
        except TransicionEstadoInvalidaError as e:
            messages.error(request, str(e))
    return redirect("postulaciones:detalle", pk=pk)


# ---------------------------------------------------------------------------
# Vistas del Operador / Director
# ---------------------------------------------------------------------------


@staff_required
def cola_revision_view(request):
    postulaciones = services.listar_cola_revision()
    return render(request, "postulaciones/cola_revision.html", {"postulaciones": postulaciones})


@staff_required
def revision_postulacion_view(request, pk):
    postulacion = get_object_or_404(
        Postulacion.objects.select_related(
            "estudiante", "convocatoria", "beca", "formulario"
        ).prefetch_related("documentos__tipo_documento"),
        pk=pk,
    )
    form_identidad = VerificarIdentidadForm()
    return render(
        request,
        "postulaciones/revision.html",
        {"postulacion": postulacion, "form_identidad": form_identidad},
    )


@staff_required
def verificar_identidad_view(request, pk):
    if request.method == "POST":
        postulacion = get_object_or_404(Postulacion, pk=pk)
        form = VerificarIdentidadForm(request.POST)
        if form.is_valid():
            try:
                services.verificar_identidad(
                    postulacion=postulacion,
                    aprobar=form.cleaned_data["aprobar"] == "1",
                    observaciones=form.cleaned_data.get("observaciones", ""),
                )
                messages.success(request, "Identidad verificada.")
            except TransicionEstadoInvalidaError as e:
                messages.error(request, str(e))
    return redirect("postulaciones:revision", pk=pk)


@staff_required
def validar_documento_view(request, doc_pk):
    if request.method == "POST":
        documento = get_object_or_404(DocumentoPostulacion, pk=doc_pk)
        aprobar_raw = request.POST.get("aprobar")
        if aprobar_raw not in ("0", "1"):
            messages.error(request, "Acción inválida.")
            return redirect("postulaciones:revision", pk=documento.postulacion.pk)
        try:
            services.validar_documento(
                documento=documento,
                aprobar=aprobar_raw == "1",
            )
            messages.success(request, f"Documento '{documento.tipo_documento}' validado.")
        except (TransicionEstadoInvalidaError, Exception) as e:
            messages.error(request, str(e))
        return redirect("postulaciones:revision", pk=documento.postulacion.pk)
    return redirect("postulaciones:cola-revision")


@staff_required
def digitalizar_documento_view(request, doc_pk):
    documento = get_object_or_404(DocumentoPostulacion, pk=doc_pk)
    form = DigitalizarDocumentoForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        try:
            services.digitalizar_documento(
                documento=documento,
                archivo=request.FILES["archivo"],
            )
            messages.success(request, f"Documento '{documento.tipo_documento}' digitalizado.")
        except DocumentoNoAprobadoError as e:
            messages.error(request, str(e))
        return redirect("postulaciones:revision", pk=documento.postulacion.pk)

    return render(
        request,
        "postulaciones/digitalizar.html",
        {"form": form, "documento": documento},
    )
