import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from apps.acceso.models import Usuario
from apps.configuracion.models import FormularioSocioeconomico
from apps.convocatorias.models import Beca, Convocatoria
from apps.postulaciones import services
from apps.postulaciones.models import Postulacion


@pytest.fixture
def estudiante(db):
    return Usuario.objects.create_user(
        email="est@test.com", password="pass", first_name="Ana", last_name="Gómez"
    )


@pytest.fixture
def otro_estudiante(db):
    return Usuario.objects.create_user(email="otro@test.com", password="pass")


@pytest.fixture
def operador(db):
    grupo, _ = Group.objects.get_or_create(name="Operador")
    user = Usuario.objects.create_user(email="op@test.com", password="pass")
    user.groups.add(grupo)
    return user


@pytest.fixture
def formulario(db, estudiante):
    return FormularioSocioeconomico.objects.create(
        usuario=estudiante,
        situacion_laboral=FormularioSocioeconomico.SituacionLaboral.EMPLEADO,
        ingreso_mensual_familiar=Decimal("40000"),
        cantidad_familiares=3,
        situacion_habitacional=FormularioSocioeconomico.SituacionHabitacional.PROPIETARIO,
        tiene_beca_previa=False,
        completado=True,
    )


@pytest.fixture
def beca(db):
    return Beca.objects.create(nombre="Beca Excelencia", activa=True)


@pytest.fixture
def convocatoria(db, beca):
    c = Convocatoria.objects.create(
        nombre="Conv 2026",
        fecha_apertura=timezone.now() - datetime.timedelta(days=1),
        fecha_cierre=timezone.now() + datetime.timedelta(days=30),
        estado=Convocatoria.Estado.PUBLICADA,
    )
    c.becas.add(beca)
    return c


@pytest.fixture
def postulacion_borrador(db, estudiante, convocatoria, beca, formulario):
    return Postulacion.objects.create(
        estudiante=estudiante,
        convocatoria=convocatoria,
        beca=beca,
        formulario=formulario,
        estado=Postulacion.Estado.BORRADOR,
    )


@pytest.fixture
def postulacion_enviada(postulacion_borrador):
    return services.enviar_postulacion(postulacion=postulacion_borrador)


@pytest.mark.django_db
def test_constancia_dueno_puede_descargar(client, estudiante, postulacion_enviada):
    client.login(username=estudiante.email, password="pass")
    response = client.get(
        reverse("postulaciones:constancia", kwargs={"pk": postulacion_enviada.pk})
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_constancia_otro_estudiante_no_puede(client, otro_estudiante, postulacion_enviada):
    client.login(username=otro_estudiante.email, password="pass")
    response = client.get(
        reverse("postulaciones:constancia", kwargs={"pk": postulacion_enviada.pk})
    )
    assert response.status_code == 302
    assert response.url == reverse("postulaciones:lista")


@pytest.mark.django_db
def test_constancia_staff_puede_descargar(client, operador, postulacion_enviada):
    client.login(username=operador.email, password="pass")
    response = client.get(
        reverse("postulaciones:constancia", kwargs={"pk": postulacion_enviada.pk})
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_constancia_sin_enviar_redirige(client, estudiante, postulacion_borrador):
    client.login(username=estudiante.email, password="pass")
    response = client.get(
        reverse("postulaciones:constancia", kwargs={"pk": postulacion_borrador.pk})
    )
    assert response.status_code == 302
    assert response.url == reverse("postulaciones:detalle", kwargs={"pk": postulacion_borrador.pk})
