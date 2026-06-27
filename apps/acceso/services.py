from django.contrib.auth.models import Group
from django.db import transaction

from .exceptions import (
    ContrasenasNoCoincidenceError,
    EmailYaRegistradoError,
    NroRegistroYaRegistradoError,
)
from .models import PerfilEstudiante, Usuario


@transaction.atomic
def autorregistrar_estudiante(
    *, email, password1, password2, first_name, last_name, nro_registro, carrera, anio_ingreso, fecha_nacimiento
):
    """Registra un nuevo estudiante con su perfil académico básico.

    Args:
        email: Dirección de correo electrónico única.
        password1: Contraseña elegida.
        password2: Confirmación de contraseña.
        first_name: Nombre del estudiante.
        last_name: Apellido del estudiante.
        nro_registro: Número de registro universitario único.
        carrera: Nombre de la carrera.
        anio_ingreso: Año de ingreso a la universidad.
        fecha_nacimiento: Fecha de nacimiento (18–60 años).

    Returns:
        El Usuario recién creado con perfil de estudiante y grupo asignado.

    Raises:
        ContrasenasNoCoincidenceError: Si password1 != password2.
        EmailYaRegistradoError: Si el email ya existe en el sistema.
        NroRegistroYaRegistradoError: Si el número de registro ya está registrado.
    """
    if password1 != password2:
        raise ContrasenasNoCoincidenceError("Las contraseñas no coinciden.")

    if Usuario.objects.filter(email=email).exists():
        raise EmailYaRegistradoError(f"El email {email} ya está registrado.")

    if PerfilEstudiante.objects.filter(nro_registro=nro_registro).exists():
        raise NroRegistroYaRegistradoError(f"El Nro. de Registro {nro_registro} ya está registrado.")

    usuario = Usuario.objects.create_user(
        email=email,
        password=password1,
        first_name=first_name,
        last_name=last_name,
    )

    PerfilEstudiante.objects.create(
        usuario=usuario,
        nro_registro=nro_registro,
        carrera=carrera,
        anio_ingreso=anio_ingreso,
        fecha_nacimiento=fecha_nacimiento,
    )

    grupo_estudiante = Group.objects.get(name="Estudiante")
    usuario.groups.add(grupo_estudiante)

    return usuario
