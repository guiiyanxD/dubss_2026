import pytest
from django.contrib.auth.models import Group

from apps.acceso.models import Usuario
from apps.usuarios.exceptions import EmailYaRegistradoError, RolInvalidoError
from apps.usuarios.services import asignar_rol, registrar_usuario


@pytest.fixture(autouse=True)
def grupos(db):
    Group.objects.get_or_create(name="Director")
    Group.objects.get_or_create(name="Operador")
    Group.objects.get_or_create(name="Estudiante")


def test_registrar_usuario_director(db):
    usuario = registrar_usuario(
        email="dir@test.com", first_name="Juan", last_name="Pérez", rol="Director"
    )
    assert isinstance(usuario, Usuario)
    assert not usuario.has_usable_password()
    assert usuario.groups.filter(name="Director").exists()


def test_registrar_usuario_rol_invalido(db):
    with pytest.raises(RolInvalidoError):
        registrar_usuario(email="x@test.com", first_name="X", last_name="Y", rol="Superadmin")


def test_registrar_usuario_email_duplicado(db):
    registrar_usuario(email="dup@test.com", first_name="A", last_name="B", rol="Operador")
    with pytest.raises(EmailYaRegistradoError):
        registrar_usuario(email="dup@test.com", first_name="C", last_name="D", rol="Director")


def test_asignar_rol_reemplaza_grupo(db):
    usuario = registrar_usuario(
        email="op@test.com", first_name="Op", last_name="Test", rol="Operador"
    )
    asignar_rol(usuario=usuario, rol="Director")
    assert usuario.groups.filter(name="Director").exists()
    assert not usuario.groups.filter(name="Operador").exists()
