import pytest
from django.contrib.auth.models import Group

from apps.acceso.exceptions import (
    ContrasenasNoCoincidenceError,
    EmailYaRegistradoError,
    LegajoYaRegistradoError,
)
from apps.acceso.models import PerfilEstudiante, Usuario
from apps.acceso.services import autorregistrar_estudiante


@pytest.fixture(autouse=True)
def grupos(db):
    Group.objects.get_or_create(name="Estudiante")
    Group.objects.get_or_create(name="Director")
    Group.objects.get_or_create(name="Operador")


def _datos_validos(**overrides):
    base = {
        "email": "estudiante@test.com",
        "password1": "Segura123!",
        "password2": "Segura123!",
        "first_name": "Ana",
        "last_name": "García",
        "nro_registro": "216002400",
        "carrera": "Ingeniería Informática",
        "anio_ingreso": 2022,
    }
    base.update(overrides)
    return base


def test_autorregistrar_estudiante_exitoso(db):
    usuario = autorregistrar_estudiante(**_datos_validos())

    assert isinstance(usuario, Usuario)
    assert usuario.email == "estudiante@test.com"
    assert usuario.groups.filter(name="Estudiante").exists()
    assert PerfilEstudiante.objects.filter(usuario=usuario, nro_registro="216002400").exists()


def test_autorregistrar_estudiante_contrasenas_distintas(db):
    with pytest.raises(ContrasenasNoCoincidenceError):
        autorregistrar_estudiante(**_datos_validos(password2="Diferente999!"))


def test_autorregistrar_estudiante_email_duplicado(db):
    autorregistrar_estudiante(**_datos_validos())
    with pytest.raises(EmailYaRegistradoError):
        autorregistrar_estudiante(**_datos_validos(nro_registro="216002401"))


def test_autorregistrar_estudiante_nro_registro_duplicado(db):
    autorregistrar_estudiante(**_datos_validos())
    with pytest.raises(LegajoYaRegistradoError):
        autorregistrar_estudiante(**_datos_validos(email="otro@test.com"))
