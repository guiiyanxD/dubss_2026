from decimal import Decimal

import pytest

from apps.configuracion.models import FormularioSocioeconomico
from apps.configuracion.services import guardar_formulario


@pytest.fixture
def estudiante(db):
    from apps.acceso.models import Usuario

    return Usuario.objects.create_user(
        email="est@test.com",
        password="pass",
        first_name="Ana",
        last_name="Gómez",
    )


@pytest.mark.django_db
def test_guardar_formulario_crea_nuevo(estudiante):
    formulario = guardar_formulario(
        estudiante=estudiante,
        situacion_laboral=FormularioSocioeconomico.SituacionLaboral.EMPLEADO,
        ingreso_mensual_familiar=Decimal("50000.00"),
        cantidad_familiares=3,
        situacion_habitacional=FormularioSocioeconomico.SituacionHabitacional.PROPIETARIO,
        tiene_beca_previa=False,
    )

    assert formulario.pk is not None
    assert formulario.completado is True
    assert formulario.usuario == estudiante
    assert formulario.ingreso_mensual_familiar == Decimal("50000.00")


@pytest.mark.django_db
def test_guardar_formulario_actualiza_existente(estudiante):
    guardar_formulario(
        estudiante=estudiante,
        situacion_laboral=FormularioSocioeconomico.SituacionLaboral.EMPLEADO,
        ingreso_mensual_familiar=Decimal("50000.00"),
        cantidad_familiares=3,
        situacion_habitacional=FormularioSocioeconomico.SituacionHabitacional.PROPIETARIO,
        tiene_beca_previa=False,
    )
    formulario = guardar_formulario(
        estudiante=estudiante,
        situacion_laboral=FormularioSocioeconomico.SituacionLaboral.DESEMPLEADO,
        ingreso_mensual_familiar=Decimal("20000.00"),
        cantidad_familiares=2,
        situacion_habitacional=FormularioSocioeconomico.SituacionHabitacional.ALQUILANDO,
        tiene_beca_previa=True,
    )

    assert FormularioSocioeconomico.objects.count() == 1
    assert formulario.situacion_laboral == FormularioSocioeconomico.SituacionLaboral.DESEMPLEADO
    assert formulario.ingreso_mensual_familiar == Decimal("20000.00")
