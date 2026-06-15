from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from . import services
from .exceptions import (
    ConvocatoriaNoModificableError,
    ConvocatoriaYaCerradaError,
    FechaInvalidaError,
    NombreDuplicadoError,
)
from .forms import (
    BecaForm,
    ConvocatoriaForm,
    TipoDocumentoForm,
    convocatoria_a_form_inicial,
)
from .models import Beca, Convocatoria, TipoDocumento


def _es_director_o_operador(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=["Director", "Operador"]).exists()
    )


def _es_director(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Director").exists()
    )


staff_required = user_passes_test(_es_director_o_operador, login_url="/accounts/login/")
director_required = user_passes_test(_es_director, login_url="/accounts/login/")


# ---------------------------------------------------------------------------
# Convocatorias
# ---------------------------------------------------------------------------


@login_required
def lista_convocatorias_view(request):
    es_estudiante = not _es_director_o_operador(request.user)
    convocatorias = services.listar_convocatorias(para_estudiante=es_estudiante)
    return render(
        request,
        "convocatorias/lista.html",
        {"convocatorias": convocatorias, "es_estudiante": es_estudiante},
    )


@director_required
def crear_convocatoria_view(request):
    form = ConvocatoriaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            convocatoria = services.crear_convocatoria(
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data.get("descripcion", ""),
                fecha_apertura=form.cleaned_data["fecha_apertura"],
                fecha_cierre=form.cleaned_data["fecha_cierre"],
                becas_ids=form.cleaned_data["becas"],
                documentos_ids=form.cleaned_data["documentos_requeridos"],
                creada_por=request.user,
            )
            messages.success(request, f"Convocatoria '{convocatoria.nombre}' creada.")
            return redirect("convocatorias:detalle", pk=convocatoria.pk)
        except FechaInvalidaError as e:
            form.add_error("fecha_cierre", str(e))
    return render(
        request, "convocatorias/form.html", {"form": form, "titulo": "Nueva Convocatoria"}
    )


@director_required
def editar_convocatoria_view(request, pk):
    convocatoria = get_object_or_404(Convocatoria, pk=pk)
    initial = convocatoria_a_form_inicial(convocatoria) if request.method == "GET" else None
    form = ConvocatoriaForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            services.editar_convocatoria(
                convocatoria=convocatoria,
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data.get("descripcion", ""),
                fecha_apertura=form.cleaned_data["fecha_apertura"],
                fecha_cierre=form.cleaned_data["fecha_cierre"],
                becas_ids=form.cleaned_data["becas"],
                documentos_ids=form.cleaned_data["documentos_requeridos"],
            )
            messages.success(request, f"Convocatoria '{convocatoria.nombre}' actualizada.")
            return redirect("convocatorias:detalle", pk=convocatoria.pk)
        except (FechaInvalidaError, ConvocatoriaNoModificableError) as e:
            messages.error(request, str(e))
    return render(
        request,
        "convocatorias/form.html",
        {"form": form, "titulo": "Editar Convocatoria", "convocatoria": convocatoria},
    )


@login_required
def detalle_convocatoria_view(request, pk):
    convocatoria = get_object_or_404(
        Convocatoria.objects.prefetch_related("becas", "documentos_requeridos"), pk=pk
    )
    return render(request, "convocatorias/detalle.html", {"convocatoria": convocatoria})


@director_required
def publicar_convocatoria_view(request, pk):
    if request.method == "POST":
        convocatoria = get_object_or_404(Convocatoria, pk=pk)
        try:
            services.publicar_convocatoria(convocatoria=convocatoria)
            messages.success(request, f"Convocatoria '{convocatoria.nombre}' publicada.")
        except ConvocatoriaNoModificableError as e:
            messages.error(request, str(e))
    return redirect("convocatorias:detalle", pk=pk)


@director_required
def cerrar_convocatoria_view(request, pk):
    if request.method == "POST":
        convocatoria = get_object_or_404(Convocatoria, pk=pk)
        try:
            services.cerrar_convocatoria(convocatoria=convocatoria)
            messages.success(request, f"Convocatoria '{convocatoria.nombre}' cerrada.")
        except ConvocatoriaYaCerradaError as e:
            messages.error(request, str(e))
    return redirect("convocatorias:detalle", pk=pk)


# ---------------------------------------------------------------------------
# Becas (catálogo)
# ---------------------------------------------------------------------------


@staff_required
def lista_becas_view(request):
    becas = Beca.objects.all()
    return render(request, "convocatorias/becas/lista.html", {"becas": becas})


@director_required
def crear_beca_view(request):
    form = BecaForm(request.POST or None, initial={"activa": True})
    if request.method == "POST" and form.is_valid():
        try:
            services.crear_beca(
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data.get("descripcion", ""),
            )
            messages.success(request, "Beca creada.")
            return redirect("convocatorias:becas-lista")
        except NombreDuplicadoError as e:
            form.add_error("nombre", str(e))
    return render(request, "convocatorias/becas/form.html", {"form": form, "titulo": "Nueva Beca"})


@director_required
def editar_beca_view(request, pk):
    beca = get_object_or_404(Beca, pk=pk)
    initial = {"nombre": beca.nombre, "descripcion": beca.descripcion, "activa": beca.activa}
    form = BecaForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            services.editar_beca(
                beca=beca,
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data.get("descripcion", ""),
                activa=form.cleaned_data["activa"],
            )
            messages.success(request, "Beca actualizada.")
            return redirect("convocatorias:becas-lista")
        except NombreDuplicadoError as e:
            form.add_error("nombre", str(e))
    return render(
        request,
        "convocatorias/becas/form.html",
        {"form": form, "titulo": "Editar Beca", "beca": beca},
    )


# ---------------------------------------------------------------------------
# Tipos de documento (catálogo)
# ---------------------------------------------------------------------------


@staff_required
def lista_tipos_documento_view(request):
    tipos = TipoDocumento.objects.all()
    return render(request, "convocatorias/documentos/lista.html", {"tipos": tipos})


@director_required
def crear_tipo_documento_view(request):
    form = TipoDocumentoForm(request.POST or None, initial={"activo": True})
    if request.method == "POST" and form.is_valid():
        try:
            services.crear_tipo_documento(
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data.get("descripcion", ""),
            )
            messages.success(request, "Tipo de documento creado.")
            return redirect("convocatorias:documentos-lista")
        except NombreDuplicadoError as e:
            form.add_error("nombre", str(e))
    return render(
        request,
        "convocatorias/documentos/form.html",
        {"form": form, "titulo": "Nuevo Tipo de Documento"},
    )


@director_required
def editar_tipo_documento_view(request, pk):
    tipo = get_object_or_404(TipoDocumento, pk=pk)
    initial = {"nombre": tipo.nombre, "descripcion": tipo.descripcion, "activo": tipo.activo}
    form = TipoDocumentoForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            services.editar_tipo_documento(
                tipo_documento=tipo,
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data.get("descripcion", ""),
                activo=form.cleaned_data["activo"],
            )
            messages.success(request, "Tipo de documento actualizado.")
            return redirect("convocatorias:documentos-lista")
        except NombreDuplicadoError as e:
            form.add_error("nombre", str(e))
    return render(
        request,
        "convocatorias/documentos/form.html",
        {"form": form, "titulo": "Editar Tipo de Documento", "tipo": tipo},
    )
