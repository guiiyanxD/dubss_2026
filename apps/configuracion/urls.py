from django.urls import path

from . import views

app_name = "configuracion"

urlpatterns = [
    path("formulario/", views.formulario_view, name="formulario"),
    path(
        "formulario/integrantes/nueva-fila/",
        views.integrante_familiar_nueva_fila,
        name="integrante_nueva_fila",
    ),
]
