from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from . import services
from .exceptions import (
    ContrasenasNoCoincidenceError,
    EmailYaRegistradoError,
    LegajoYaRegistradoError,
)
from .forms import RegistroEstudianteForm


def inicio_view(request):
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
                legajo=form.cleaned_data["legajo"],
                carrera=form.cleaned_data["carrera"],
                anio_ingreso=form.cleaned_data["anio_ingreso"],
            )
            login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "¡Registro exitoso! Bienvenido al Sistema de Becas.")
            return redirect("acceso:inicio")
        except ContrasenasNoCoincidenceError as e:
            form.add_error("password2", str(e))
        except EmailYaRegistradoError as e:
            form.add_error("email", str(e))
        except LegajoYaRegistradoError as e:
            form.add_error("legajo", str(e))
    return render(request, "acceso/registro.html", {"form": form})
