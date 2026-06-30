from django.urls import path

from . import views

app_name = "configuracion"

urlpatterns = [
    path("catalogos/", views.catalogos_socioeconomicos_view, name="catalogos"),
    path("catalogos/<slug:slug>/nueva/", views.catalogo_nueva_entrada_view, name="catalogo-nueva"),
    path("catalogos/<slug:slug>/<int:pk>/editar/", views.catalogo_editar_entrada_view, name="catalogo-editar"),
    path("catalogos/<slug:slug>/<int:pk>/toggle/", views.catalogo_toggle_activo_view, name="catalogo-toggle"),
    path("catalogos/<slug:slug>/<int:pk>/cancelar/", views.catalogo_cancelar_edicion_view, name="catalogo-cancelar"),
    path("catalogos/<slug:slug>/<int:pk>/eliminar/", views.catalogo_eliminar_entrada_view, name="catalogo-eliminar"),
    path("formulario/", views.formulario_view, name="formulario"),
    path(
        "formulario/integrantes/nueva-fila/",
        views.integrante_familiar_nueva_fila,
        name="integrante_nueva_fila",
    ),
]
