from unittest.mock import patch

import pytest

from apps.acceso.models import Usuario
from apps.notificaciones.models import Notificacion
from apps.notificaciones.services import enviar_notificacion


@pytest.fixture
def usuario(db):
    return Usuario.objects.create_user(
        email="test@test.com", password="pass", first_name="Test", last_name="User"
    )


@pytest.mark.django_db
def test_enviar_notificacion_crea_registro(usuario):
    with patch("apps.notificaciones.tasks.tarea_enviar_email.delay") as mock_delay:
        notif = enviar_notificacion(
            usuario=usuario,
            asunto="Prueba",
            cuerpo="Cuerpo de prueba",
        )

    assert notif.pk is not None
    assert notif.estado == Notificacion.Estado.PENDIENTE
    assert notif.asunto == "Prueba"
    assert notif.usuario == usuario
    mock_delay.assert_called_once_with(notif.pk)


@pytest.mark.django_db
def test_notificacion_estado_inicial_pendiente(usuario):
    notif = Notificacion.objects.create(
        usuario=usuario,
        asunto="Test",
        cuerpo="Cuerpo",
    )
    assert notif.estado == Notificacion.Estado.PENDIENTE
    assert notif.fecha_envio is None
