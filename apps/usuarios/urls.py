from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.lista_usuarios_view, name="lista"),
    path("crear/", views.crear_usuario_view, name="crear"),
    path("roles/", views.gestionar_roles_view, name="roles"),
]
