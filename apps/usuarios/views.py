from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.acceso.models import Usuario

from .services import UsuarioService
from .exceptions import (
    EmailYaRegistradoError,
    NombreRolDuplicadoError,
    RolConMiembrosError,
    RolInvalidoError,
)
from .forms import CrearUsuarioForm, EditarUsuarioForm, RolForm


def _es_director(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Director").exists()
    )


director_required = user_passes_test(_es_director, login_url="/accounts/login/")


@director_required
def lista_usuarios_view(request):
    rol = request.GET.get("rol", "")
    estado = request.GET.get("estado", "")
    busqueda = request.GET.get("q", "")

    qs = UsuarioService.listar_usuarios(
        excluir_pk=request.user.pk,
        rol=rol or None,
        estado=estado or None,
        busqueda=busqueda or None,
    )

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)

    params = request.GET.copy()
    params.pop("page", None)
    query_string = f"?{params.urlencode()}&" if params else "?"

    return render(request, "usuarios/lista.html", {
        "page_obj": page_obj,
        "page_range": page_range,
        "query_string": query_string,
        "rol": rol,
        "estado": estado,
        "busqueda": busqueda,
    })


@director_required
def crear_usuario_view(request):
    form = CrearUsuarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            usuario = UsuarioService.registrar_usuario(
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                rol=form.cleaned_data["rol"],
            )
            reset_form = PasswordResetForm({"email": usuario.email})
            if reset_form.is_valid():
                reset_form.save(request=request)
            messages.success(
                request,
                f"Usuario {usuario.email} creado. Se envió un email para establecer la contraseña.",
            )
            return redirect("usuarios:lista")
        except EmailYaRegistradoError as e:
            form.add_error("email", str(e))
        except RolInvalidoError as e:
            messages.error(request, str(e))
    return render(request, "usuarios/crear.html", {"form": form})


@director_required
def editar_usuario_view(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    initial = {
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "rol": usuario.get_rol(),
    }
    form = EditarUsuarioForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            UsuarioService.editar_usuario(
                usuario=usuario,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                rol=form.cleaned_data["rol"],
            )
            messages.success(request, f"Usuario {usuario.email} actualizado.")
            return redirect("usuarios:lista")
        except RolInvalidoError as e:
            messages.error(request, str(e))
    return render(request, "usuarios/editar.html", {"form": form, "usuario": usuario})


@director_required
def activar_usuario_view(request, pk):
    if request.method == "POST":
        usuario = get_object_or_404(Usuario, pk=pk)
        UsuarioService.activar_usuario(usuario=usuario)
        messages.success(request, f"Usuario {usuario.email} activado.")
    return redirect("usuarios:lista")


@director_required
def desactivar_usuario_view(request, pk):
    if request.method == "POST":
        usuario = get_object_or_404(Usuario, pk=pk)
        UsuarioService.desactivar_usuario(usuario=usuario)
        messages.success(request, f"Usuario {usuario.email} desactivado.")
    return redirect("usuarios:lista")


@director_required
def lista_roles_view(request):
    roles = UsuarioService.listar_roles()
    return render(request, "usuarios/roles.html", {"roles": roles})


@director_required
def crear_rol_view(request):
    form = RolForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            UsuarioService.crear_rol(nombre=form.cleaned_data["nombre"])
            messages.success(request, "Rol creado correctamente.")
            return redirect("usuarios:roles")
        except NombreRolDuplicadoError as e:
            form.add_error("nombre", str(e))
    return render(request, "usuarios/roles_form.html", {"form": form, "titulo": "Nuevo Rol"})


@director_required
def editar_rol_view(request, pk):
    grupo = get_object_or_404(Group, pk=pk)
    form = RolForm(request.POST or None, initial={"nombre": grupo.name})
    if request.method == "POST" and form.is_valid():
        try:
            UsuarioService.editar_rol(grupo=grupo, nombre=form.cleaned_data["nombre"])
            messages.success(request, "Rol actualizado correctamente.")
            return redirect("usuarios:roles")
        except NombreRolDuplicadoError as e:
            form.add_error("nombre", str(e))
    return render(
        request,
        "usuarios/roles_form.html",
        {"form": form, "titulo": "Editar Rol", "grupo": grupo},
    )


@director_required
def eliminar_rol_view(request, pk):
    if request.method == "POST":
        grupo = get_object_or_404(Group, pk=pk)
        try:
            UsuarioService.eliminar_rol(grupo=grupo)
            messages.success(request, f"Rol '{grupo.name}' eliminado.")
        except RolConMiembrosError as e:
            messages.error(request, str(e))
    return redirect("usuarios:roles")
