from django.urls import path

from . import views

app_name = "convocatorias"

urlpatterns = [
    path("", views.lista_convocatorias_view, name="lista"),
    path("crear/", views.crear_convocatoria_view, name="crear"),
    path("<int:pk>/", views.detalle_convocatoria_view, name="detalle"),
    path("<int:pk>/editar/", views.editar_convocatoria_view, name="editar"),
    path("<int:pk>/publicar/", views.publicar_convocatoria_view, name="publicar"),
    path("<int:pk>/cerrar/", views.cerrar_convocatoria_view, name="cerrar"),
    # Catálogos
    path("becas/", views.lista_becas_view, name="becas-lista"),
    path("becas/crear/", views.crear_beca_view, name="becas-crear"),
    path("becas/<int:pk>/editar/", views.editar_beca_view, name="becas-editar"),
    path("documentos/", views.lista_tipos_documento_view, name="documentos-lista"),
    path("documentos/crear/", views.crear_tipo_documento_view, name="documentos-crear"),
    path("documentos/<int:pk>/editar/", views.editar_tipo_documento_view, name="documentos-editar"),
]
