import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.acceso.models import Usuario
from apps.configuracion.models import (
    FormularioSocioeconomico,
    OpcionDependencia,
    RangoIngreso,
)
from apps.convocatorias.models import Beca, Convocatoria
from apps.postulaciones.models import Postulacion
from apps.reportes.services import ReporteService as services
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


def _crear_estudiante(email, familiares=3, dep=None, ingreso=None, tenencia=None, beca_previa=False):
    u = Usuario.objects.create_user(
        email=email, password="pass", first_name="Ana", last_name="Test"
    )
    formulario = FormularioSocioeconomico.objects.create(
        usuario=u,
        cantidad_familiares=familiares,
        dependencia_economica=dep,
        rango_ingreso=ingreso,
        tipo_tenencia_vivienda=tenencia,
        tiene_beca_previa=beca_previa,
        completado=True,
    )
    return u, formulario


@pytest.fixture
def postulaciones_aprobadas(db, convocatoria, beca):
    # dep_alto: opciones con puntaje alto (situación más vulnerable)
    dep_alto = OpcionDependencia.objects.create(nombre="Solo madre/padre test", valor_puntaje=80)
    dep_bajo = OpcionDependencia.objects.create(nombre="Independiente test", valor_puntaje=20)
    ing_alto = RangoIngreso.objects.create(nombre="Bajo test", valor_puntaje=100)
    ing_bajo = RangoIngreso.objects.create(nombre="Alto test", valor_puntaje=10)

    u1, f1 = _crear_estudiante("e1@t.com", familiares=5, dep=dep_alto, ingreso=ing_alto)
    u2, f2 = _crear_estudiante("e2@t.com", familiares=1, dep=dep_bajo, ingreso=ing_bajo, beca_previa=True)

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
    # e1 tiene puntaje más alto (más vulnerable: dep alto + ingreso bajo + más familiares)
    assert p1.puntaje_socioeconomico > p2.puntaje_socioeconomico


@pytest.mark.django_db
def test_procesar_formularios_usa_pesos_de_cada_beca(convocatoria):
    """CU15 — cada postulación se puntúa con los pesos de SU beca, no un valor global."""
    dep_alto = OpcionDependencia.objects.create(nombre="Solo madre test2", valor_puntaje=90)
    dep_bajo = OpcionDependencia.objects.create(nombre="Independiente test2", valor_puntaje=10)

    # beca_dep pesa 100% en dependencia económica (via peso_dependencia_economica)
    beca_dep = Beca.objects.create(
        nombre="Beca Solo Dep",
        peso_dependencia_economica=100,
        peso_grupo_familiar=0,
        peso_procedencia=0,
        peso_tenencia_vivienda=0,
        peso_infraestructura=0,
        peso_otro_beneficio=0,
        peso_discapacidad=0,
    )
    # beca_ing pesa 100% en ingreso (via peso_dependencia_economica pero solo rango_ingreso sub-campo)
    # Como la sección 2° es promedio de 3 sub-componentes, usamos beca con todos los pesos en dep
    convocatoria.becas.add(beca_dep)

    u1, f1 = _crear_estudiante("dep_alto@t.com", dep=dep_alto)
    u2, f2 = _crear_estudiante("dep_bajo@t.com", dep=dep_bajo)

    p1 = Postulacion.objects.create(
        estudiante=u1, convocatoria=convocatoria, beca=beca_dep,
        formulario=f1, estado=Postulacion.Estado.APROBADA,
    )
    p2 = Postulacion.objects.create(
        estudiante=u2, convocatoria=convocatoria, beca=beca_dep,
        formulario=f2, estado=Postulacion.Estado.APROBADA,
    )

    services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)

    p1.refresh_from_db()
    p2.refresh_from_db()
    # p1 tiene dep_alto (90), p2 dep_bajo (10) → p1 > p2 con beca que pondera dep al 100%
    assert p1.puntaje_socioeconomico > p2.puntaje_socioeconomico


@pytest.mark.django_db
def test_procesar_formularios_sin_aprobadas(convocatoria):
    cantidad = services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
    assert cantidad == 0


@pytest.mark.django_db
def test_generar_ranking_adjudica_correctamente(postulaciones_aprobadas, convocatoria, beca):
    services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
    resultado = services.generar_ranking(
        convocatoria=convocatoria, beca=beca, cupo=1, cupo_espera=1
    )

    estados = [p.estado for p in resultado]
    assert Postulacion.Estado.ADJUDICADA in estados
    assert Postulacion.Estado.LISTA_ESPERA in estados
    assert Postulacion.Estado.NO_ADJUDICADA not in estados


@pytest.mark.django_db
def test_generar_ranking_sin_espera(postulaciones_aprobadas, convocatoria, beca):
    services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
    resultado = services.generar_ranking(
        convocatoria=convocatoria, beca=beca, cupo=1, cupo_espera=0
    )

    estados = [p.estado for p in resultado]
    assert Postulacion.Estado.ADJUDICADA in estados
    assert Postulacion.Estado.NO_ADJUDICADA in estados
    assert Postulacion.Estado.LISTA_ESPERA not in estados


@pytest.mark.django_db
def test_exportar_excel_retorna_bytes(postulaciones_aprobadas, convocatoria, beca):
    services.procesar_formularios_socioeconomicos(convocatoria=convocatoria)
    services.generar_ranking(convocatoria=convocatoria, beca=beca, cupo=1, cupo_espera=1)

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


_FILA_POSTULANTE_EJEMPLO = {
    "nombre": "Ana Test",
    "email": "ana@test.com",
    "legajo": "L1",
    "carrera": "Ingeniería de Sistemas",
    "anio_ingreso": 2021,
    "cantidad_familiares": 3,
    "convocatoria": "Conv Test",
    "beca": "Beca Test",
    "estado_postulacion": "Enviada",
}


def test_generar_archivo_postulantes_excel():
    nombre, contenido = services.generar_archivo_postulantes(
        filas=[_FILA_POSTULANTE_EJEMPLO], formato="excel"
    )
    assert nombre.endswith(".xlsx")
    assert isinstance(contenido, bytes)
    assert contenido[:2] == b"PK"  # magic bytes de ZIP (formato XLSX)


def test_generar_archivo_postulantes_pdf():
    nombre, contenido = services.generar_archivo_postulantes(
        filas=[_FILA_POSTULANTE_EJEMPLO], formato="pdf"
    )
    assert nombre.endswith(".pdf")
    assert contenido[:4] == b"%PDF"


@pytest.mark.django_db
def test_procesar_mensaje_con_llm_adjunta_archivo_generado(director):
    conversacion = services.crear_conversacion(usuario=director)
    mensaje = MensajeChat.objects.create(
        conversacion=conversacion,
        rol=MensajeChat.Rol.USUARIO,
        contenido="Dame un excel de postulantes de familias con 3 integrantes",
    )

    respuestas_simuladas = [
        {
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "generar_reporte_postulantes",
                            "arguments": {"cantidad_familiares_min": 3, "formato": "excel"},
                        }
                    }
                ],
            }
        },
        {"message": {"content": "Listo, generé el archivo solicitado.", "tool_calls": []}},
    ]

    with patch("apps.reportes.services.llm_client.chat", side_effect=respuestas_simuladas):
        services.procesar_mensaje_con_llm(mensaje_pk=mensaje.pk)

    respuesta = conversacion.mensajes.filter(rol=MensajeChat.Rol.ASISTENTE).first()
    assert respuesta.contenido == "Listo, generé el archivo solicitado."
    assert respuesta.archivo
    assert respuesta.archivo.name.endswith(".xlsx")
    # el archivo nunca debe viajar en tools_usadas (solo metadatos)
    assert "_archivo_bytes" not in respuesta.tools_usadas[0]
