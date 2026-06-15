from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.lista_usuarios_view, name="lista"),
    path("crear/", views.crear_usuario_view, name="crear"),
    path("<int:pk>/editar/", views.editar_usuario_view, name="editar"),
    path("<int:pk>/activar/", views.activar_usuario_view, name="activar"),
    path("<int:pk>/desactivar/", views.desactivar_usuario_view, name="desactivar"),
    path("roles/", views.gestionar_roles_view, name="roles"),
]
