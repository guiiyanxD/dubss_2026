from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.convocatorias.models import Beca, Convocatoria

from . import services
from .exceptions import (
    BecaNoDisponibleError,
    ConstanciaNoDisponibleError,
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


@login_required
def imprimir_constancia_view(request, pk):
    postulacion = get_object_or_404(
        Postulacion.objects.select_related("estudiante", "convocatoria", "beca", "formulario"),
        pk=pk,
    )
    # Mismo control de acceso que detalle_postulacion_view: evita que un estudiante
    # descargue la constancia de otro probando distintos pk en la URL.
    if not _es_staff(request.user) and postulacion.estudiante != request.user:
        messages.error(request, "No tenés permiso para ver esta postulación.")
        return redirect("postulaciones:lista")

    try:
        pdf_bytes = services.generar_constancia_pdf(postulacion=postulacion)
    except ConstanciaNoDisponibleError as e:
        messages.error(request, str(e))
        return redirect("postulaciones:detalle", pk=pk)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="constancia_{postulacion.numero_referencia}.pdf"'
    )
    return response


# ---------------------------------------------------------------------------
# Vistas del Operador / Director
# ---------------------------------------------------------------------------


@staff_required
def cola_revision_view(request):
    estado = request.GET.get("estado", "")
    convocatoria_id = request.GET.get("convocatoria", "")
    beca_id = request.GET.get("beca", "")
    busqueda = request.GET.get("q", "")

    qs = services.listar_cola_revision(
        estado=estado or None,
        convocatoria_id=convocatoria_id or None,
        beca_id=beca_id or None,
        busqueda=busqueda or None,
    )

    # Opciones de los selects: solo convocatorias/becas con al menos una
    # postulación en la cola completa (sin filtrar), para no ofrecer
    # combinaciones que siempre den resultado vacío.
    base_qs = services.listar_cola_revision()
    convocatorias_disponibles = (
        Convocatoria.objects.filter(postulaciones__in=base_qs).distinct().order_by("nombre")
    )
    becas_disponibles = Beca.objects.filter(postulaciones__in=base_qs).distinct().order_by("nombre")

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)

    params = request.GET.copy()
    params.pop("page", None)
    query_string = f"?{params.urlencode()}&" if params else "?"

    return render(
        request,
        "postulaciones/cola_revision.html",
        {
            "page_obj": page_obj,
            "page_range": page_range,
            "query_string": query_string,
            "estado": estado,
            "convocatoria_id": convocatoria_id,
            "beca_id": beca_id,
            "busqueda": busqueda,
            "convocatorias_disponibles": convocatorias_disponibles,
            "becas_disponibles": becas_disponibles,
        },
    )


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
