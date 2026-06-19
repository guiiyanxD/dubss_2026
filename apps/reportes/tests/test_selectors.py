import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.configuracion.models import FormularioSocioeconomico
from apps.notificaciones.models import Notificacion
from apps.postulaciones.models import DocumentoPostulacion, Postulacion
from apps.reportes import selectors

# ---------------------------------------------------------------------------
# Demanda y convocatorias
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_postulaciones_por_beca(convocatoria, beca, crear_estudiante):
    u1, f1 = crear_estudiante()
    u2, f2 = crear_estudiante()
    Postulacion.objects.create(
        estudiante=u1,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f1,
        estado=Postulacion.Estado.ENVIADA,
    )
    Postulacion.objects.create(
        estudiante=u2,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f2,
        estado=Postulacion.Estado.ENVIADA,
    )

    resultado = selectors.postulaciones_por_beca(convocatoria=convocatoria)
    assert resultado == {"etiquetas": [beca.nombre], "valores": [2]}


@pytest.mark.django_db
def test_tasa_adjudicacion_por_convocatoria(convocatoria, beca, crear_estudiante):
    u1, f1 = crear_estudiante()
    u2, f2 = crear_estudiante()
    Postulacion.objects.create(
        estudiante=u1,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f1,
        estado=Postulacion.Estado.ADJUDICADA,
        puntaje_socioeconomico=Decimal("80"),
    )
    Postulacion.objects.create(
        estudiante=u2,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f2,
        estado=Postulacion.Estado.NO_ADJUDICADA,
        puntaje_socioeconomico=Decimal("40"),
    )

    resultado = selectors.tasa_adjudicacion_por_convocatoria()
    assert resultado == {"etiquetas": [convocatoria.nombre], "valores": [50.0]}


@pytest.mark.django_db
def test_tamano_lista_espera_por_convocatoria(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante()
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.LISTA_ESPERA,
    )

    resultado = selectors.tamano_lista_espera_por_convocatoria()
    assert resultado == {"etiquetas": [convocatoria.nombre], "valores": [1]}


# ---------------------------------------------------------------------------
# Embudo de postulaciones
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_embudo_estados(convocatoria, beca, crear_estudiante):
    u1, f1 = crear_estudiante()
    u2, f2 = crear_estudiante()
    Postulacion.objects.create(
        estudiante=u1,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f1,
        estado=Postulacion.Estado.BORRADOR,
    )
    Postulacion.objects.create(
        estudiante=u2,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f2,
        estado=Postulacion.Estado.ENVIADA,
    )

    resultado = selectors.embudo_estados(convocatoria=convocatoria)
    assert resultado == {"etiquetas": ["Borrador", "Enviada"], "valores": [1, 1]}


@pytest.mark.django_db
def test_desglose_rechazos(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante()
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.RECHAZADA_IDENTIDAD,
    )

    resultado = selectors.desglose_rechazos(convocatoria=convocatoria)
    assert resultado == {
        "etiquetas": [
            "Rechazada - No Presentación",
            "Rechazada - Identidad",
            "Rechazada - Documentación",
        ],
        "valores": [0, 1, 0],
    }


@pytest.mark.django_db
def test_tiempos_promedio_por_etapa(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante()
    p = Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.BORRADOR,
    )
    p.estado = Postulacion.Estado.ENVIADA
    p.save()

    base = timezone.now() - datetime.timedelta(days=10)
    for i, registro in enumerate(p.history.order_by("history_date")):
        p.history.filter(pk=registro.pk).update(history_date=base + datetime.timedelta(days=i * 2))

    resultado = selectors.tiempos_promedio_por_etapa(convocatoria=convocatoria)
    assert resultado == {"etiquetas": ["Borrador → Enviada"], "valores": [2.0]}


@pytest.mark.django_db
def test_tiempos_promedio_por_etapa_sin_historial():
    resultado = selectors.tiempos_promedio_por_etapa()
    assert resultado == {"etiquetas": [], "valores": []}


# ---------------------------------------------------------------------------
# Validación documental
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_validacion_por_tipo_documento(convocatoria, beca, crear_estudiante, tipo_documento):
    u1, f1 = crear_estudiante()
    u2, f2 = crear_estudiante()
    p1 = Postulacion.objects.create(
        estudiante=u1,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f1,
        estado=Postulacion.Estado.EN_REVISION,
    )
    p2 = Postulacion.objects.create(
        estudiante=u2,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f2,
        estado=Postulacion.Estado.EN_REVISION,
    )
    DocumentoPostulacion.objects.create(
        postulacion=p1, tipo_documento=tipo_documento, validado=True
    )
    DocumentoPostulacion.objects.create(
        postulacion=p2, tipo_documento=tipo_documento, validado=False
    )

    resultado = selectors.validacion_por_tipo_documento()
    assert resultado == {
        "etiquetas": [tipo_documento.nombre],
        "aprobado": [1],
        "rechazado": [1],
        "pendiente": [0],
    }


@pytest.mark.django_db
def test_documento_mayor_rechazo(convocatoria, beca, crear_estudiante, tipo_documento):
    u, f = crear_estudiante()
    p = Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.EN_REVISION,
    )
    DocumentoPostulacion.objects.create(
        postulacion=p, tipo_documento=tipo_documento, validado=False
    )

    resultado = selectors.documento_mayor_rechazo()
    assert resultado == {"tipo_documento": tipo_documento.nombre, "porcentaje_rechazo": 100.0}


# ---------------------------------------------------------------------------
# Perfil socioeconómico
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_distribucion_ingreso_familiar(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante(ingreso=30000)
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.ENVIADA,
    )

    resultado = selectors.distribucion_ingreso_familiar(convocatoria=convocatoria)
    assert resultado == {"valores": [30000.0]}


@pytest.mark.django_db
def test_distribucion_puntaje_socioeconomico(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante()
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.PROCESADA,
        puntaje_socioeconomico=Decimal("65.5"),
    )

    resultado = selectors.distribucion_puntaje_socioeconomico(convocatoria=convocatoria)
    assert resultado == {"valores": [65.5]}


@pytest.mark.django_db
def test_distribucion_choices(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante(laboral=FormularioSocioeconomico.SituacionLaboral.DESEMPLEADO)
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.ENVIADA,
    )

    resultado = selectors.distribucion_choices("situacion_laboral", convocatoria=convocatoria)
    assert resultado == {"etiquetas": ["Desempleado/a"], "valores": [1]}


@pytest.mark.django_db
def test_indicadores_generales(convocatoria, beca, crear_estudiante):
    u1, f1 = crear_estudiante(familiares=4, tiene_discapacidad=True)
    u2, f2 = crear_estudiante(familiares=2)
    Postulacion.objects.create(
        estudiante=u1,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f1,
        estado=Postulacion.Estado.ENVIADA,
    )
    Postulacion.objects.create(
        estudiante=u2,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f2,
        estado=Postulacion.Estado.ENVIADA,
    )

    resultado = selectors.indicadores_generales(convocatoria=convocatoria)
    assert resultado["promedio_familiares"] == 3.0
    assert resultado["pct_discapacidad"] == 50.0
    assert resultado["pct_completos"] == 100.0


@pytest.mark.django_db
def test_indicadores_generales_sin_datos(convocatoria):
    resultado = selectors.indicadores_generales(convocatoria=convocatoria)
    assert resultado == {
        "promedio_familiares": 0.0,
        "promedio_hijos": 0.0,
        "pct_discapacidad": 0.0,
        "pct_completos": 0.0,
    }


# ---------------------------------------------------------------------------
# Ranking y adjudicación
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_comparacion_puntaje_por_resultado(convocatoria, beca, crear_estudiante):
    u1, f1 = crear_estudiante()
    u2, f2 = crear_estudiante()
    Postulacion.objects.create(
        estudiante=u1,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f1,
        estado=Postulacion.Estado.ADJUDICADA,
        puntaje_socioeconomico=Decimal("90"),
    )
    Postulacion.objects.create(
        estudiante=u2,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f2,
        estado=Postulacion.Estado.NO_ADJUDICADA,
        puntaje_socioeconomico=Decimal("30"),
    )

    resultado = selectors.comparacion_puntaje_por_resultado(convocatoria=convocatoria)
    assert resultado["Adjudicada"] == [90.0]
    assert resultado["No Adjudicada"] == [30.0]
    assert resultado["Lista de Espera"] == []


@pytest.mark.django_db
def test_punto_corte_por_convocatoria(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante()
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.ADJUDICADA,
        puntaje_socioeconomico=Decimal("72.3"),
    )

    resultado = selectors.punto_corte_por_convocatoria()
    assert resultado == {"etiquetas": [convocatoria.nombre], "valores": [72.3]}


# ---------------------------------------------------------------------------
# Académico
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_postulantes_por_carrera(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante(carrera="Ingeniería de Sistemas")
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.ENVIADA,
    )

    resultado = selectors.postulantes_por_carrera(convocatoria=convocatoria)
    assert resultado == {"etiquetas": ["Ingeniería de Sistemas"], "valores": [1]}


@pytest.mark.django_db
def test_tasa_adjudicacion_por_carrera(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante(carrera="Medicina")
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.ADJUDICADA,
        puntaje_socioeconomico=Decimal("80"),
    )

    resultado = selectors.tasa_adjudicacion_por_carrera()
    assert resultado == {"etiquetas": ["Medicina"], "valores": [100.0]}


@pytest.mark.django_db
def test_postulantes_por_anio_ingreso(convocatoria, beca, crear_estudiante):
    u, f = crear_estudiante(anio_ingreso=2021)
    Postulacion.objects.create(
        estudiante=u,
        convocatoria=convocatoria,
        beca=beca,
        formulario=f,
        estado=Postulacion.Estado.ENVIADA,
    )

    resultado = selectors.postulantes_por_anio_ingreso(convocatoria=convocatoria)
    assert resultado == {"etiquetas": ["2021"], "valores": [1]}


# ---------------------------------------------------------------------------
# Notificaciones
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_tasa_entrega_notificaciones(director):
    Notificacion.objects.create(
        usuario=director, asunto="Test", cuerpo="...", estado=Notificacion.Estado.ENVIADA
    )
    Notificacion.objects.create(
        usuario=director, asunto="Test", cuerpo="...", estado=Notificacion.Estado.ERROR
    )

    resultado = selectors.tasa_entrega_notificaciones()
    assert resultado == {"etiquetas": ["Pendiente", "Enviada", "Error"], "valores": [0, 1, 1]}


@pytest.mark.django_db
def test_latencia_envio_notificaciones(director):
    n = Notificacion.objects.create(
        usuario=director, asunto="Test", cuerpo="...", estado=Notificacion.Estado.ENVIADA
    )
    ahora = timezone.now()
    Notificacion.objects.filter(pk=n.pk).update(
        fecha_creacion=ahora - datetime.timedelta(minutes=10), fecha_envio=ahora
    )

    resultado = selectors.latencia_envio_notificaciones()
    assert resultado["minutos_promedio"] == pytest.approx(10.0, abs=0.5)


@pytest.mark.django_db
def test_latencia_envio_notificaciones_sin_datos():
    resultado = selectors.latencia_envio_notificaciones()
    assert resultado == {"minutos_promedio": 0.0}
