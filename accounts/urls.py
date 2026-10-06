from django.contrib.auth.views import LogoutView
from django.urls import path

from . import controllers as c

urlpatterns = [
    path("login/", c.LoginController.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("usuarios/", c.UsuarioLista.as_view(), name="usuario_lista"),
    path("usuarios/nuevo/", c.UsuarioCrear.as_view(), name="usuario_crear"),
    path("usuarios/<int:pk>/editar/", c.UsuarioEditar.as_view(), name="usuario_editar"),
    path("usuarios/<int:pk>/eliminar/", c.UsuarioEliminar.as_view(), name="usuario_eliminar"),
]
