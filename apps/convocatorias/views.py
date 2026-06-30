from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .services import ConvocatoriaService
from .exceptions import (
    ConvocatoriaNoModificableError,
    ConvocatoriaYaCerradaError,
    FechaInvalidaError,
    NombreDuplicadoError,
    PonderacionInvalidaError,
)
from .forms import (
    BecaForm,
    ConvocatoriaForm,
    TipoDocumentoForm,
    convocatoria_a_form_inicial,
)
from .models import Beca, Convocatoria, TipoDocumento

_CAMPOS_PESO = [
    "peso_dependencia_economica",
    "peso_grupo_familiar",
    "peso_procedencia",
    "peso_tenencia_vivienda",
    "peso_infraestructura",
    "peso_otro_beneficio",
    "peso_discapacidad",
]


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
    estado = request.GET.get("estado", "") if not es_estudiante else ""
    busqueda = request.GET.get("q", "")

    qs = ConvocatoriaService.listar_convocatorias(
        para_estudiante=es_estudiante,
        estado=estado or None,
        busqueda=busqueda or None,
    )

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)

    params = request.GET.copy()
    params.pop("page", None)
    query_string = f"?{params.urlencode()}&" if params else "?"

    return render(
        request,
        "convocatorias/lista.html",
        {
            "page_obj": page_obj,
            "page_range": page_range,
            "query_string": query_string,
            "es_estudiante": es_estudiante,
            "estado": estado,
            "busqueda": busqueda,
        },
    )


@director_required
def crear_convocatoria_view(request):
    form = ConvocatoriaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            convocatoria = ConvocatoriaService.crear_convocatoria(
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
            ConvocatoriaService.editar_convocatoria(
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
    return render(
        request,
        "convocatorias/detalle.html",
        {
            "convocatoria": convocatoria,
            "es_director": _es_director(request.user),
            "es_estudiante": not _es_director_o_operador(request.user),
        },
    )


@director_required
def publicar_convocatoria_view(request, pk):
    if request.method == "POST":
        convocatoria = get_object_or_404(Convocatoria, pk=pk)
        try:
            ConvocatoriaService.publicar_convocatoria(convocatoria=convocatoria)
            messages.success(request, f"Convocatoria '{convocatoria.nombre}' publicada.")
        except ConvocatoriaNoModificableError as e:
            messages.error(request, str(e))
    return redirect("convocatorias:detalle", pk=pk)


@director_required
def cerrar_convocatoria_view(request, pk):
    if request.method == "POST":
        convocatoria = get_object_or_404(Convocatoria, pk=pk)
        try:
            ConvocatoriaService.cerrar_convocatoria(convocatoria=convocatoria)
            messages.success(request, f"Convocatoria '{convocatoria.nombre}' cerrada.")
        except ConvocatoriaYaCerradaError as e:
            messages.error(request, str(e))
    return redirect("convocatorias:detalle", pk=pk)


# ---------------------------------------------------------------------------
# Becas (catálogo)
# ---------------------------------------------------------------------------


@staff_required
def lista_becas_view(request):
    activa = request.GET.get("activa", "")
    busqueda = request.GET.get("q", "")

    qs = Beca.objects.order_by("nombre")
    if activa == "1":
        qs = qs.filter(activa=True)
    elif activa == "0":
        qs = qs.filter(activa=False)
    if busqueda:
        qs = qs.filter(nombre__icontains=busqueda)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)

    params = request.GET.copy()
    params.pop("page", None)
    query_string = f"?{params.urlencode()}&" if params else "?"

    return render(
        request,
        "convocatorias/becas/lista.html",
        {
            "page_obj": page_obj,
            "page_range": page_range,
            "query_string": query_string,
            "activa": activa,
            "busqueda": busqueda,
        },
    )


@director_required
def crear_beca_view(request):
    form = BecaForm(request.POST or None, initial={"activa": True})
    if request.method == "POST" and form.is_valid():
        try:
            ConvocatoriaService.crear_beca(
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data.get("descripcion", ""),
                **{campo: form.cleaned_data[campo] for campo in _CAMPOS_PESO},
            )
            messages.success(request, "Beca creada.")
            return redirect("convocatorias:becas-lista")
        except NombreDuplicadoError as e:
            form.add_error("nombre", str(e))
        except PonderacionInvalidaError as e:
            form.add_error(None, str(e))
    return render(request, "convocatorias/becas/form.html", {"form": form, "titulo": "Nueva Beca"})


@director_required
def editar_beca_view(request, pk):
    beca = get_object_or_404(Beca, pk=pk)
    initial = {
        "nombre": beca.nombre,
        "descripcion": beca.descripcion,
        "activa": beca.activa,
        **{campo: getattr(beca, campo) for campo in _CAMPOS_PESO},
    }
    form = BecaForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            ConvocatoriaService.editar_beca(
                beca=beca,
                nombre=form.cleaned_data["nombre"],
                descripcion=form.cleaned_data.get("descripcion", ""),
                activa=form.cleaned_data["activa"],
                **{campo: form.cleaned_data[campo] for campo in _CAMPOS_PESO},
            )
            messages.success(request, "Beca actualizada.")
            return redirect("convocatorias:becas-lista")
        except NombreDuplicadoError as e:
            form.add_error("nombre", str(e))
        except PonderacionInvalidaError as e:
            form.add_error(None, str(e))
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
    activo = request.GET.get("activo", "")
    busqueda = request.GET.get("q", "")

    qs = TipoDocumento.objects.order_by("nombre")
    if activo == "1":
        qs = qs.filter(activo=True)
    elif activo == "0":
        qs = qs.filter(activo=False)
    if busqueda:
        qs = qs.filter(nombre__icontains=busqueda)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)

    params = request.GET.copy()
    params.pop("page", None)
    query_string = f"?{params.urlencode()}&" if params else "?"

    return render(
        request,
        "convocatorias/documentos/lista.html",
        {
            "page_obj": page_obj,
            "page_range": page_range,
            "query_string": query_string,
            "activo": activo,
            "busqueda": busqueda,
        },
    )


@director_required
def crear_tipo_documento_view(request):
    form = TipoDocumentoForm(request.POST or None, initial={"activo": True})
    if request.method == "POST" and form.is_valid():
        try:
            ConvocatoriaService.crear_tipo_documento(
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
            ConvocatoriaService.editar_tipo_documento(
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
