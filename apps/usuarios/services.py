from django.contrib.auth.models import Group
from django.db import transaction

from apps.acceso.models import Usuario

from .exceptions import EmailYaRegistradoError, RolInvalidoError

ROLES_INTERNOS = {"Director", "Operador"}
ROLES_VALIDOS = {"Director", "Operador", "Estudiante"}


@transaction.atomic
def registrar_usuario(*, email, first_name, last_name, rol):
    """Registra un usuario interno (Director u Operador) sin contraseña utilizable.

    El usuario recibe un email para establecer su contraseña (enviado desde la vista).

    Args:
        email: Dirección de correo electrónico única.
        first_name: Nombre del usuario.
        last_name: Apellido del usuario.
        rol: Nombre del grupo a asignar ('Director' o 'Operador').

    Returns:
        El Usuario recién creado.

    Raises:
        RolInvalidoError: Si el rol no es 'Director' ni 'Operador'.
        EmailYaRegistradoError: Si el email ya existe en el sistema.
    """
    if rol not in ROLES_INTERNOS:
        raise RolInvalidoError(f"El rol '{rol}' no es válido para usuarios internos.")

    if Usuario.objects.filter(email=email).exists():
        raise EmailYaRegistradoError(f"El email {email} ya está registrado.")

    usuario = Usuario.objects.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=None,
    )

    grupo = Group.objects.get(name=rol)
    usuario.groups.add(grupo)

    return usuario


@transaction.atomic
def asignar_rol(*, usuario, rol):
    """Reemplaza todos los grupos del usuario por el rol indicado.

    Args:
        usuario: Instancia de Usuario al que asignar el rol.
        rol: Nombre del grupo destino.

    Raises:
        RolInvalidoError: Si el rol no existe en la tabla de grupos.
    """
    if rol not in ROLES_VALIDOS:
        raise RolInvalidoError(f"El rol '{rol}' no es un rol válido del sistema.")

    grupo = Group.objects.filter(name=rol).first()
    if not grupo:
        raise RolInvalidoError(f"El grupo '{rol}' no existe en la base de datos.")

    usuario.groups.clear()
    usuario.groups.add(grupo)


def listar_usuarios(*, excluir_pk=None):
    """Retorna todos los usuarios con sus grupos precargados.

    Args:
        excluir_pk: PK del usuario a excluir (ej: el usuario autenticado).

    Returns:
        QuerySet de Usuario ordenado por apellido y nombre.
    """
    qs = Usuario.objects.prefetch_related("groups").order_by("last_name", "first_name", "email")
    if excluir_pk:
        qs = qs.exclude(pk=excluir_pk)
    return qs


@transaction.atomic
def editar_usuario(*, usuario, first_name, last_name, rol):
    """Actualiza nombre, apellido y rol de un usuario existente.

    Args:
        usuario: Instancia de Usuario a editar.
        first_name: Nuevo nombre.
        last_name: Nuevo apellido.
        rol: Nuevo rol (cualquiera de los roles válidos).

    Returns:
        El Usuario modificado.

    Raises:
        RolInvalidoError: Si el rol no es válido.
    """
    if rol not in ROLES_VALIDOS:
        raise RolInvalidoError(f"El rol '{rol}' no es válido.")
    usuario.first_name = first_name
    usuario.last_name = last_name
    usuario.save(update_fields=["first_name", "last_name"])
    asignar_rol(usuario=usuario, rol=rol)
    return usuario


@transaction.atomic
def activar_usuario(*, usuario):
    """Activa un usuario previamente desactivado."""
    usuario.is_active = True
    usuario.save(update_fields=["is_active"])


@transaction.atomic
def desactivar_usuario(*, usuario):
    """Desactiva un usuario sin eliminarlo de la base de datos."""
    usuario.is_active = False
    usuario.save(update_fields=["is_active"])
