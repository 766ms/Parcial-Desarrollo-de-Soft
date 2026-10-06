"""CONTROLADOR (MVC): login y gestión de usuarios."""
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

from .forms import LoginForm, UsuarioForm
from .mixins import CrudCrear, CrudEditar, CrudEliminar, CrudLista
from .models import Usuario


class LoginController(LoginView):
    template_name = "accounts/login.html"   # VISTA que se muestra
    authentication_form = LoginForm         # valida contra el MODELO Usuario
    redirect_authenticated_user = True


class UsuarioLista(CrudLista):
    template_name = "usuarios/lista.html"
    context_object_name = "usuarios"
    queryset = Usuario.objects.order_by("nombre_completo")


class UsuarioCrear(CrudCrear):
    model, form_class = Usuario, UsuarioForm
    url_lista, titulo = "usuario_lista", "Nuevo usuario"


class UsuarioEditar(CrudEditar):
    model, form_class = Usuario, UsuarioForm
    url_lista, titulo = "usuario_lista", "Editar usuario"

    def form_valid(self, form):
        if form.instance.pk == self.request.user.pk and (
                form.cleaned_data["rol"] != Usuario.Rol.ADMIN or not form.cleaned_data["estado"]):
            form.add_error(None, "No puedes quitarte el rol de Admin ni desactivarte a ti mismo.")
            return self.form_invalid(form)
        respuesta = super().form_valid(form)
        if form.cleaned_data.get("password") and self.object.pk == self.request.user.pk:
            update_session_auth_hash(self.request, self.object)  # no cerrar la sesión propia
        return respuesta


class UsuarioEliminar(CrudEliminar):
    model = Usuario
    url_lista, titulo = "usuario_lista", "Eliminar usuario"
    aviso = "Si el usuario ya participó en evaluaciones no se podrá eliminar; en ese caso márcalo como inactivo."

    def form_valid(self, form):
        if self.object.pk == self.request.user.pk:
            messages.error(self.request, "No puedes eliminar tu propio usuario.")
            return redirect(self.url_retorno())
        return super().form_valid(form)
