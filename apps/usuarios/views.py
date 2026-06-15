from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from apps.acceso.models import Usuario

from . import services
from .exceptions import EmailYaRegistradoError, RolInvalidoError
from .forms import CrearUsuarioForm


def _es_director(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Director").exists()
    )


director_required = user_passes_test(_es_director, login_url="/accounts/login/")


@director_required
def lista_usuarios_view(request):
    usuarios = services.listar_usuarios(excluir_pk=request.user.pk)
    return render(request, "usuarios/lista.html", {"usuarios": usuarios})


@director_required
def crear_usuario_view(request):
    form = CrearUsuarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            usuario = services.registrar_usuario(
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
def gestionar_roles_view(request):
    grupos = Group.objects.all()
    grupos_con_miembros = [
        (grupo, Usuario.objects.filter(groups=grupo).order_by("last_name", "first_name"))
        for grupo in grupos
    ]
    return render(request, "usuarios/roles.html", {"grupos_con_miembros": grupos_con_miembros})
