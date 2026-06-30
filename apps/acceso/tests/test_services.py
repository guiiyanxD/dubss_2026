import datetime
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group

from apps.acceso.exceptions import (
    ContrasenasNoCoincidenceError,
    EmailYaRegistradoError,
    NroRegistroYaRegistradoError,
)
from apps.acceso.forms import RegistroEstudianteForm
from apps.acceso.models import PerfilEstudiante, Usuario
from apps.acceso.services import AccesoService


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
        "fecha_nacimiento": datetime.date(2000, 1, 15),
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Servicio
# ---------------------------------------------------------------------------


def test_autorregistrar_estudiante_exitoso(db):
    usuario = AccesoService.autorregistrar_estudiante(**_datos_validos())

    assert isinstance(usuario, Usuario)
    assert usuario.email == "estudiante@test.com"
    assert usuario.groups.filter(name="Estudiante").exists()
    assert PerfilEstudiante.objects.filter(usuario=usuario, nro_registro="216002400").exists()


def test_autorregistrar_estudiante_persiste_fecha_nacimiento(db):
    usuario = AccesoService.autorregistrar_estudiante(**_datos_validos())
    perfil = PerfilEstudiante.objects.get(usuario=usuario)
    assert perfil.fecha_nacimiento == datetime.date(2000, 1, 15)


def test_autorregistrar_estudiante_contrasenas_distintas(db):
    with pytest.raises(ContrasenasNoCoincidenceError):
        AccesoService.autorregistrar_estudiante(**_datos_validos(password2="Diferente999!"))


def test_autorregistrar_estudiante_email_duplicado(db):
    AccesoService.autorregistrar_estudiante(**_datos_validos())
    with pytest.raises(EmailYaRegistradoError):
        AccesoService.autorregistrar_estudiante(**_datos_validos(nro_registro="216002401"))


def test_autorregistrar_estudiante_nro_registro_duplicado(db):
    AccesoService.autorregistrar_estudiante(**_datos_validos())
    with pytest.raises(NroRegistroYaRegistradoError):
        AccesoService.autorregistrar_estudiante(**_datos_validos(email="otro@test.com"))


# ---------------------------------------------------------------------------
# Formulario — validación de edad (18–60)
# ---------------------------------------------------------------------------


def _datos_form(**overrides):
    hoy = datetime.date.today()
    base = {
        "email": "test@test.com",
        "first_name": "Ana",
        "last_name": "García",
        "password1": "Segura123!",
        "password2": "Segura123!",
        "nro_registro": "216002400",
        "carrera": "Ingeniería Informática",
        "anio_ingreso": 2022,
        "fecha_nacimiento": datetime.date(hoy.year - 25, hoy.month, hoy.day).isoformat(),
        "acepta_terminos": True,
    }
    base.update(overrides)
    return base


def _hace_n_anios(n):
    """Devuelve una fecha de nacimiento que produce exactamente n años hoy."""
    hoy = datetime.date.today()
    return datetime.date(hoy.year - n, hoy.month, hoy.day).isoformat()


def test_form_fecha_nacimiento_valida():
    form = RegistroEstudianteForm(_datos_form())
    assert form.is_valid(), form.errors


def test_form_edad_exactamente_18_acepta():
    form = RegistroEstudianteForm(_datos_form(fecha_nacimiento=_hace_n_anios(18)))
    assert form.is_valid(), form.errors


def test_form_edad_exactamente_60_acepta():
    form = RegistroEstudianteForm(_datos_form(fecha_nacimiento=_hace_n_anios(60)))
    assert form.is_valid(), form.errors


def test_form_edad_menor_18_rechaza():
    form = RegistroEstudianteForm(_datos_form(fecha_nacimiento=_hace_n_anios(17)))
    assert not form.is_valid()
    assert "fecha_nacimiento" in form.errors


def test_form_edad_mayor_60_rechaza():
    form = RegistroEstudianteForm(_datos_form(fecha_nacimiento=_hace_n_anios(61)))
    assert not form.is_valid()
    assert "fecha_nacimiento" in form.errors


# ---------------------------------------------------------------------------
# Modelo — PerfilEstudiante.get_edad()
# Se usa una fecha fija como "hoy" (2026-06-27) para aislar el test del reloj real.
# ---------------------------------------------------------------------------


class _FechaFija(datetime.date):
    """Subclase de date que devuelve 2026-06-27 en today()."""

    @classmethod
    def today(cls):
        return datetime.date(2026, 6, 27)


def _perfil_con_fn(fecha_nacimiento):
    """Crea un PerfilEstudiante en memoria (sin persistir) para probar get_edad()."""
    perfil = PerfilEstudiante.__new__(PerfilEstudiante)
    perfil.fecha_nacimiento = fecha_nacimiento
    return perfil


def test_get_edad_cumpleanos_hoy():
    # Cumpleaños el 27/06 → ya cumplió exactamente 30 años
    perfil = _perfil_con_fn(datetime.date(1996, 6, 27))
    with patch("apps.acceso.models.date", _FechaFija):
        assert perfil.get_edad() == 30


def test_get_edad_cumpleanos_no_alcanzado():
    # Cumpleaños el 28/06 → aún no cumplió al 27/06 → 29 años
    perfil = _perfil_con_fn(datetime.date(1996, 6, 28))
    with patch("apps.acceso.models.date", _FechaFija):
        assert perfil.get_edad() == 29


def test_get_edad_cumpleanos_ya_paso():
    # Cumpleaños el 26/06 → ya cumplió al 27/06 → 30 años
    perfil = _perfil_con_fn(datetime.date(1996, 6, 26))
    with patch("apps.acceso.models.date", _FechaFija):
        assert perfil.get_edad() == 30
