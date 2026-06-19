import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.acceso.models import Usuario
from apps.configuracion.models import FormularioSocioeconomico
from apps.convocatorias.models import Beca, Convocatoria
from apps.postulaciones.models import Postulacion
from apps.reportes import services
from apps.reportes.models import MensajeChat, ResumenIA


@pytest.fixture
def director(db):
    return Usuario.objects.create_superuser(email="dir@test.com", password="pass")


@pytest.fixture
def beca(db):
    return Beca.objects.create(nombre="Beca Test", activa=True)


@pytest.fixture
def convocatoria(db, director, beca):
    import datetime

    from django.utils import timezone

    c = Convocatoria.objects.create(
        nombre="Conv Test",
        fecha_apertura=timezone.now() - datetime.timedelta(days=5),
        fecha_cierre=timezone.now() + datetime.timedelta(days=30),
        estado=Convocatoria.Estado.PUBLICADA,
        creada_por=director,
    )
    c.becas.add(beca)
    return c


def _crear_estudiante(email, ingreso, familiares, laboral, habitacional, beca_previa=False):
    u = Usuario.objects.create_user(
        email=email, password="pass", first_name="Ana", last_name="Test"
    )
    formulario = FormularioSocioeconomico.objects.create(
        usuario=u,
        situacion_laboral=laboral,
        ingreso_mensual_familiar=Decimal(str(ingreso)),
        cantidad_familiares=familiares,
        situacion_habitacional=habitacional,
        tiene_beca_previa=beca_previa,
        completado=True,
    )
    return u, formulario


@pytest.fixture
def postulaciones_aprobadas(db, convocatoria, beca):
    u1, f1 = _crear_estudiante(
        "e1@t.com",
        20000,
        5,
        FormularioSocioeconomico.SituacionLaboral.DESEMPLEADO,
        FormularioSocioeconomico.SituacionHabitacional.ALQUILANDO,
    )
    u2, f2 = _crear_estudiante(
        "e2@t.com",
        100000,
        1,
        FormularioSocioeconomico.SituacionLaboral.EMPLEADO,
        FormularioSocioeconomico.SituacionHabitacional.PROPIETARIO,
        beca_previa=True,
    )

    p1 = Postulacion.objects.create(
        estudiante=u1,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f1,
        estado=Postulacion.Estado.APROBADA,
    )
    p2 = Postulacion.objects.create(
        estudiante=u2,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f2,
        estado=Postulacion.Estado.APROBADA,
    )
    return [p1, p2]


@pytest.mark.django_db
def test_procesar_formularios_calcula_puntajes(postulaciones_aprobadas, convocatoria):
    cantidad = services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)

    assert cantidad == 2
    p1 = Postulacion.objects.get(pk=postulaciones_aprobadas[0].pk)
    p2 = Postulacion.objects.get(pk=postulaciones_aprobadas[1].pk)

    assert p1.estado == Postulacion.Estado.PROCESADA
    assert p2.estado == Postulacion.Estado.PROCESADA
    assert p1.puntaje_socioeconomico is not None
    assert p2.puntaje_socioeconomico is not None
    # e1 debería tener mayor puntaje (menor ingreso, desempleado, más familiares, alquila)
    assert p1.puntaje_socioeconomico > p2.puntaje_socioeconomico


@pytest.mark.django_db
def test_procesar_formularios_sin_aprobadas(convocatoria):
    cantidad = services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
    assert cantidad == 0


@pytest.mark.django_db
def test_generar_ranking_adjudica_correctamente(postulaciones_aprobadas, convocatoria):
    services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
    resultado = services.generar_ranking(convocatoria=convocatoria, cupo=1, cupo_espera=1)

    estados = [p.estado for p in resultado]
    assert Postulacion.Estado.ADJUDICADA in estados
    assert Postulacion.Estado.LISTA_ESPERA in estados
    assert Postulacion.Estado.NO_ADJUDICADA not in estados


@pytest.mark.django_db
def test_generar_ranking_sin_espera(postulaciones_aprobadas, convocatoria):
    services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
    resultado = services.generar_ranking(convocatoria=convocatoria, cupo=1, cupo_espera=0)

    estados = [p.estado for p in resultado]
    assert Postulacion.Estado.ADJUDICADA in estados
    assert Postulacion.Estado.NO_ADJUDICADA in estados
    assert Postulacion.Estado.LISTA_ESPERA not in estados


@pytest.mark.django_db
def test_exportar_excel_retorna_bytes(postulaciones_aprobadas, convocatoria):
    services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
    services.generar_ranking(convocatoria=convocatoria, cupo=1, cupo_espera=1)

    xlsx = services.exportar_ranking_excel(convocatoria=convocatoria)
    assert isinstance(xlsx, bytes)
    assert len(xlsx) > 0
    # Magic bytes de ZIP (formato XLSX)
    assert xlsx[:2] == b"PK"


@pytest.mark.django_db
def test_solicitar_resumen_ia_encola_tarea(director, convocatoria):
    with patch("apps.reportes.tasks.tarea_generar_resumen_ia.delay") as mock_delay:
        resumen = services.solicitar_resumen_ia(usuario=director, convocatoria=convocatoria)

    assert resumen.estado == ResumenIA.Estado.PENDIENTE
    assert resumen.convocatoria == convocatoria
    mock_delay.assert_called_once_with(resumen.pk)


@pytest.mark.django_db
def test_generar_resumen_con_llm_completa_correctamente(director, convocatoria):
    resumen = ResumenIA.objects.create(usuario=director, convocatoria=convocatoria)

    with patch("apps.reportes.services.llm_client.chat") as mock_chat:
        mock_chat.return_value = {"message": {"content": "Resumen de prueba."}}
        services.generar_resumen_con_llm(resumen_pk=resumen.pk)

    resumen.refresh_from_db()
    assert resumen.estado == ResumenIA.Estado.COMPLETADO
    assert resumen.resultado == "Resumen de prueba."
    assert resumen.fecha_completado is not None


@pytest.mark.django_db
def test_generar_resumen_con_llm_marca_error_si_falla(director, convocatoria):
    resumen = ResumenIA.objects.create(usuario=director, convocatoria=convocatoria)

    with patch(
        "apps.reportes.services.llm_client.chat", side_effect=ConnectionError("sin conexión")
    ):
        with pytest.raises(ConnectionError):
            services.generar_resumen_con_llm(resumen_pk=resumen.pk)

    resumen.refresh_from_db()
    assert resumen.estado == ResumenIA.Estado.ERROR
    assert "sin conexión" in resumen.error_detalle


@pytest.mark.django_db
def test_marcar_resumenes_ia_vencidos(director, convocatoria):
    resumen = ResumenIA.objects.create(usuario=director, convocatoria=convocatoria)
    vencido = timezone.now() - datetime.timedelta(minutes=20)
    ResumenIA.objects.filter(pk=resumen.pk).update(fecha_creacion=vencido)

    count = services.marcar_resumenes_ia_vencidos(minutos=10)

    resumen.refresh_from_db()
    assert count == 1
    assert resumen.estado == ResumenIA.Estado.ERROR


@pytest.mark.django_db
def test_enviar_mensaje_chat_encola_tarea(director):
    conversacion = services.crear_conversacion(usuario=director)

    with patch("apps.reportes.tasks.tarea_procesar_mensaje_chat.delay") as mock_delay:
        mensaje = services.enviar_mensaje_chat(conversacion=conversacion, contenido="Hola")

    assert mensaje.rol == MensajeChat.Rol.USUARIO
    conversacion.refresh_from_db()
    assert conversacion.titulo == "Hola"
    mock_delay.assert_called_once_with(mensaje.pk)


@pytest.mark.django_db
def test_procesar_mensaje_con_llm_sin_tools(director):
    conversacion = services.crear_conversacion(usuario=director)
    mensaje = MensajeChat.objects.create(
        conversacion=conversacion, rol=MensajeChat.Rol.USUARIO, contenido="Hola"
    )

    with patch("apps.reportes.services.llm_client.chat") as mock_chat:
        mock_chat.return_value = {
            "message": {"content": "Hola, ¿en qué puedo ayudarte?", "tool_calls": []}
        }
        services.procesar_mensaje_con_llm(mensaje_pk=mensaje.pk)

    respuesta = conversacion.mensajes.filter(rol=MensajeChat.Rol.ASISTENTE).first()
    assert respuesta is not None
    assert respuesta.contenido == "Hola, ¿en qué puedo ayudarte?"
    assert respuesta.tools_usadas is None


@pytest.mark.django_db
def test_procesar_mensaje_con_llm_con_tool_call(director, convocatoria):
    conversacion = services.crear_conversacion(usuario=director)
    mensaje = MensajeChat.objects.create(
        conversacion=conversacion,
        rol=MensajeChat.Rol.USUARIO,
        contenido="¿Cuántas convocatorias hay?",
    )

    respuestas_simuladas = [
        {
            "message": {
                "content": "",
                "tool_calls": [{"function": {"name": "listar_convocatorias", "arguments": {}}}],
            }
        },
        {"message": {"content": "Hay 1 convocatoria registrada.", "tool_calls": []}},
    ]

    with patch("apps.reportes.services.llm_client.chat", side_effect=respuestas_simuladas):
        services.procesar_mensaje_con_llm(mensaje_pk=mensaje.pk)

    respuesta = conversacion.mensajes.filter(rol=MensajeChat.Rol.ASISTENTE).first()
    assert respuesta.contenido == "Hay 1 convocatoria registrada."
    assert respuesta.tools_usadas == [{"tool": "listar_convocatorias", "argumentos": {}}]


@pytest.mark.django_db
def test_procesar_mensaje_con_llm_marca_error_si_falla(director):
    conversacion = services.crear_conversacion(usuario=director)
    mensaje = MensajeChat.objects.create(
        conversacion=conversacion, rol=MensajeChat.Rol.USUARIO, contenido="Hola"
    )

    with patch(
        "apps.reportes.services.llm_client.chat", side_effect=ConnectionError("sin conexión")
    ):
        with pytest.raises(ConnectionError):
            services.procesar_mensaje_con_llm(mensaje_pk=mensaje.pk)

    respuesta = conversacion.mensajes.filter(rol=MensajeChat.Rol.ASISTENTE).first()
    assert respuesta is not None
    assert "no está disponible" in respuesta.contenido


@pytest.mark.django_db
def test_marcar_chats_vencidos(director):
    conversacion = services.crear_conversacion(usuario=director)
    mensaje = MensajeChat.objects.create(
        conversacion=conversacion, rol=MensajeChat.Rol.USUARIO, contenido="Hola"
    )
    vencido = timezone.now() - datetime.timedelta(minutes=20)
    MensajeChat.objects.filter(pk=mensaje.pk).update(fecha_creacion=vencido)

    count = services.marcar_chats_vencidos(minutos=10)

    assert count == 1
    assert conversacion.mensajes.filter(rol=MensajeChat.Rol.ASISTENTE).exists()
