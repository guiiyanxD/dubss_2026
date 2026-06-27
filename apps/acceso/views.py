from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from . import services
from .exceptions import (
    ContrasenasNoCoincidenceError,
    EmailYaRegistradoError,
    NroRegistroYaRegistradoError,
)
from .forms import RegistroEstudianteForm


def inicio_view(request):
    if request.user.is_authenticated:
        rol = request.user.get_rol()
        if rol == "Estudiante":
            return redirect("convocatorias:lista")
        elif rol in ("Director", "Operador") or request.user.is_superuser:
            return redirect("postulaciones:cola-revision")
    return render(request, "acceso/inicio.html")


def registro_estudiante_view(request):
    form = RegistroEstudianteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            usuario = services.autorregistrar_estudiante(
                email=form.cleaned_data["email"],
                password1=form.cleaned_data["password1"],
                password2=form.cleaned_data["password2"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                nro_registro=form.cleaned_data["nro_registro"],
                carrera=form.cleaned_data["carrera"],
                anio_ingreso=form.cleaned_data["anio_ingreso"],
                fecha_nacimiento=form.cleaned_data["fecha_nacimiento"],
            )
            login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "¡Registro exitoso! Bienvenido al Sistema de Becas.")
            return redirect("acceso:inicio")
        except ContrasenasNoCoincidenceError as e:
            form.add_error("password2", str(e))
        except EmailYaRegistradoError as e:
            form.add_error("email", str(e))
        except NroRegistroYaRegistradoError as e:
            form.add_error("nro_registro", str(e))
    return render(request, "acceso/registro.html", {"form": form})
