from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Count

from apps.acceso.models import Usuario

from .exceptions import (
    EmailYaRegistradoError,
    NombreRolDuplicadoError,
    RolConMiembrosError,
    RolInvalidoError,
)

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


def listar_usuarios(*, excluir_pk=None, rol=None, estado=None, busqueda=None):
    """Retorna usuarios filtrados y con grupos precargados.

    Args:
        excluir_pk: PK del usuario a excluir (ej: el usuario autenticado).
        rol: Nombre de grupo ('Director', 'Operador', 'Estudiante') o None para todos.
        estado: 'activo', 'inactivo', o None para todos.
        busqueda: Texto a buscar en email, nombre y apellido.

    Returns:
        QuerySet de Usuario ordenado por apellido y nombre.
    """
    qs = Usuario.objects.prefetch_related("groups").order_by("last_name", "first_name", "email")
    if excluir_pk:
        qs = qs.exclude(pk=excluir_pk)
    if rol:
        qs = qs.filter(groups__name=rol)
    if estado == "activo":
        qs = qs.filter(is_active=True)
    elif estado == "inactivo":
        qs = qs.filter(is_active=False)
    if busqueda:
        from django.db.models import Q

        qs = qs.filter(
            Q(email__icontains=busqueda)
            | Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
        )
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


# ---------------------------------------------------------------------------
# Gestión de Roles (Groups)
# ---------------------------------------------------------------------------


def listar_roles():
    """Retorna todos los grupos con la cantidad de miembros anotada.

    Returns:
        QuerySet de Group ordenado por nombre, con `num_miembros` anotado.
    """
    return Group.objects.annotate(num_miembros=Count("user")).order_by("name")


@transaction.atomic
def crear_rol(*, nombre):
    """Crea un nuevo grupo/rol en el sistema.

    Args:
        nombre: Nombre del rol a crear.

    Returns:
        El Group recién creado.

    Raises:
        NombreRolDuplicadoError: Si ya existe un grupo con ese nombre.
    """
    if Group.objects.filter(name=nombre).exists():
        raise NombreRolDuplicadoError(f"Ya existe un rol con el nombre '{nombre}'.")
    return Group.objects.create(name=nombre)


@transaction.atomic
def editar_rol(*, grupo, nombre):
    """Renombra un grupo existente.

    Args:
        grupo: Instancia de Group a modificar.
        nombre: Nuevo nombre del rol.

    Returns:
        El Group modificado.

    Raises:
        NombreRolDuplicadoError: Si ya existe otro grupo con ese nombre.
    """
    if Group.objects.filter(name=nombre).exclude(pk=grupo.pk).exists():
        raise NombreRolDuplicadoError(f"Ya existe un rol con el nombre '{nombre}'.")
    grupo.name = nombre
    grupo.save(update_fields=["name"])
    return grupo


@transaction.atomic
def eliminar_rol(*, grupo):
    """Elimina un grupo del sistema.

    Args:
        grupo: Instancia de Group a eliminar.

    Raises:
        RolConMiembrosError: Si el grupo tiene usuarios activos asignados.
    """
    if grupo.user_set.filter(is_active=True).exists():
        raise RolConMiembrosError(
            f"El rol '{grupo.name}' tiene usuarios activos asignados y no puede eliminarse."
        )
    grupo.delete()
