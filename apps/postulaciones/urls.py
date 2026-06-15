from django.urls import path

from . import views

app_name = "postulaciones"

urlpatterns = [
    # Estudiante
    path("", views.mis_postulaciones_view, name="lista"),
    path("<int:pk>/", views.detalle_postulacion_view, name="detalle"),
    path("<int:pk>/enviar/", views.enviar_postulacion_view, name="enviar"),
    path("iniciar/<int:convocatoria_pk>/", views.iniciar_postulacion_view, name="iniciar"),
    # Operador / Director
    path("revision/", views.cola_revision_view, name="cola-revision"),
    path("revision/<int:pk>/", views.revision_postulacion_view, name="revision"),
    path(
        "revision/<int:pk>/identidad/", views.verificar_identidad_view, name="verificar-identidad"
    ),
    path(
        "documentos/<int:doc_pk>/validar/", views.validar_documento_view, name="validar-documento"
    ),
    path(
        "documentos/<int:doc_pk>/digitalizar/", views.digitalizar_documento_view, name="digitalizar"
    ),
]
