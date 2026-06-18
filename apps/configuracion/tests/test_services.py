from decimal import Decimal

import pytest

from apps.configuracion.models import FormularioSocioeconomico, IntegranteFamiliar
from apps.configuracion.services import guardar_formulario, guardar_integrantes_familiares


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

    assert FormularioSocioeconomico.objects.filter(usuario=estudiante).count() == 1
    assert formulario.situacion_laboral == FormularioSocioeconomico.SituacionLaboral.DESEMPLEADO
    assert formulario.ingreso_mensual_familiar == Decimal("20000.00")


@pytest.mark.django_db
def test_guardar_formulario_con_campos_dubs002(estudiante):
    formulario = guardar_formulario(
        estudiante=estudiante,
        situacion_laboral=FormularioSocioeconomico.SituacionLaboral.EMPLEADO,
        ingreso_mensual_familiar=Decimal("3000"),
        cantidad_familiares=3,
        situacion_habitacional=FormularioSocioeconomico.SituacionHabitacional.ALQUILANDO,
        tiene_beca_previa=False,
        numero_celular="70000000",
        dependencia_economica=FormularioSocioeconomico.DependenciaEconomica.AMBOS_PADRES,
        tipo_ocupacion_sosten=FormularioSocioeconomico.TipoOcupacionSosten.COMERCIANTE_MINORISTA,
        tiene_hijos=False,
        residencia_lugar="Santa Cruz",
        tipo_tenencia_vivienda=FormularioSocioeconomico.TipoTenenciaVivienda.DE_LOS_PADRES,
        dormitorios=5,
        banos=2,
        tiene_discapacidad=False,
    )

    assert formulario.numero_celular == "70000000"
    assert (
        formulario.dependencia_economica
        == FormularioSocioeconomico.DependenciaEconomica.AMBOS_PADRES
    )
    assert formulario.tipo_ocupacion_sosten == (
        FormularioSocioeconomico.TipoOcupacionSosten.COMERCIANTE_MINORISTA
    )
    assert formulario.dormitorios == 5


@pytest.mark.django_db
def test_guardar_integrantes_familiares_reemplaza_filas(estudiante):
    formulario = guardar_formulario(
        estudiante=estudiante,
        situacion_laboral=FormularioSocioeconomico.SituacionLaboral.EMPLEADO,
        ingreso_mensual_familiar=Decimal("3000"),
        cantidad_familiares=3,
        situacion_habitacional=FormularioSocioeconomico.SituacionHabitacional.PROPIETARIO,
        tiene_beca_previa=False,
    )

    guardar_integrantes_familiares(
        formulario=formulario,
        integrantes=[
            {
                "nombre_completo": "María Luz Vásquez",
                "parentesco": "Madre",
                "edad": 47,
                "ocupacion": "Comerciante",
                "observacion": "",
            },
            {
                "nombre_completo": "Gerardo Brun",
                "parentesco": "Padre",
                "edad": 52,
                "ocupacion": "Comerciante",
                "observacion": "",
            },
        ],
    )
    assert IntegranteFamiliar.objects.filter(formulario=formulario).count() == 2

    guardar_integrantes_familiares(
        formulario=formulario,
        integrantes=[
            {
                "nombre_completo": "Raquel Brun",
                "parentesco": "Hermana",
                "edad": 21,
                "ocupacion": "Estudiante",
                "observacion": "",
            },
        ],
    )
    integrantes = IntegranteFamiliar.objects.filter(formulario=formulario)
    assert integrantes.count() == 1
    assert integrantes.first().nombre_completo == "Raquel Brun"
