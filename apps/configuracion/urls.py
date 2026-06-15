from django.urls import path

from . import views

app_name = "configuracion"

urlpatterns = [
    path("formulario/", views.formulario_view, name="formulario"),
]
