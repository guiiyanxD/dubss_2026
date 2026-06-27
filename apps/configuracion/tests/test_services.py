import pytest

from apps.configuracion.models import (
    FormularioSocioeconomico,
    IntegranteFamiliar,
    OpcionDependencia,
    RangoIngreso,
    TipoOcupacionSosten,
    TipoTenenciaVivienda,
)
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
        cantidad_familiares=3,
        tiene_beca_previa=False,
    )

    assert formulario.pk is not None
    assert formulario.completado is True
    assert formulario.usuario == estudiante


@pytest.mark.django_db
def test_guardar_formulario_actualiza_existente(estudiante):
    guardar_formulario(
        estudiante=estudiante,
        cantidad_familiares=3,
        tiene_beca_previa=False,
    )
    formulario = guardar_formulario(
        estudiante=estudiante,
        cantidad_familiares=2,
        tiene_beca_previa=True,
    )

    assert FormularioSocioeconomico.objects.filter(usuario=estudiante).count() == 1
    assert formulario.cantidad_familiares == 2
    assert formulario.tiene_beca_previa is True


@pytest.mark.django_db
def test_guardar_formulario_con_campos_fk(estudiante):
    dep = OpcionDependencia.objects.create(nombre="Ambos padres (test)", valor_puntaje=50)
    ocup = TipoOcupacionSosten.objects.create(nombre="Asalariado formal (test)", valor_puntaje=40)
    ten = TipoTenenciaVivienda.objects.create(nombre="Alquiler (test)", valor_puntaje=100)
    rng = RangoIngreso.objects.create(nombre="Hasta Bs. 2.500 (test)", valor_puntaje=100)

    formulario = guardar_formulario(
        estudiante=estudiante,
        cantidad_familiares=3,
        tiene_beca_previa=False,
        numero_celular="70000000",
        dependencia_economica=dep,
        tipo_ocupacion_sosten=ocup,
        tipo_tenencia_vivienda=ten,
        rango_ingreso=rng,
        tiene_hijos=False,
        residencia_lugar="Santa Cruz",
        dormitorios=5,
        banos=2,
        tiene_discapacidad=False,
    )

    assert formulario.numero_celular == "70000000"
    assert formulario.dependencia_economica == dep
    assert formulario.tipo_ocupacion_sosten == ocup
    assert formulario.tipo_tenencia_vivienda == ten
    assert formulario.rango_ingreso == rng
    assert formulario.dormitorios == 5


@pytest.mark.django_db
def test_guardar_integrantes_familiares_reemplaza_filas(estudiante):
    formulario = guardar_formulario(
        estudiante=estudiante,
        cantidad_familiares=3,
        tiene_beca_previa=False,
    )

    guardar_integrantes_familiares(
        formulario=formulario,
        integrantes=[
            {
                "nombre_completo": "María Luz Vásquez",
                "parentesco": "MADRE",
                "edad": 47,
                "ocupacion": "Comerciante",
                "observacion": "",
            },
            {
                "nombre_completo": "Gerardo Brun",
                "parentesco": "PADRE",
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
                "parentesco": "HERMANA",
                "edad": 21,
                "ocupacion": "Estudiante",
                "observacion": "",
            },
        ],
    )
    integrantes = IntegranteFamiliar.objects.filter(formulario=formulario)
    assert integrantes.count() == 1
    assert integrantes.first().nombre_completo == "Raquel Brun"
