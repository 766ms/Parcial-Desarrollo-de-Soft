"""Piezas reutilizables del CONTROLADOR (MVC): control de acceso Admin y base para CRUD."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Solo usuarios con rol Admin. Además entrega título, aviso y enlace 'Cancelar' a la VISTA."""
    titulo = ""
    aviso = ""

    def test_func(self):
        return self.request.user.es_admin

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = self.titulo
        ctx["aviso"] = self.aviso
        if hasattr(self, "url_retorno"):
            ctx["cancelar_url"] = self.url_retorno()
        return ctx


class CrudLista(AdminMixin, ListView):
    pass


class CrudCrear(AdminMixin, CreateView):
    template_name = "crud/form.html"
    url_lista = None  # nombre de la URL de la lista

    def url_retorno(self):
        return reverse(self.url_lista)

    def get_success_url(self):
        return self.url_retorno()


class CrudEditar(AdminMixin, UpdateView):
    template_name = "crud/form.html"
    url_lista = None

    def url_retorno(self):
        return reverse(self.url_lista)

    def get_success_url(self):
        return self.url_retorno()


class CrudEliminar(AdminMixin, DeleteView):
    template_name = "crud/confirmar_eliminar.html"
    url_lista = None

    def url_retorno(self):
        return reverse(self.url_lista)

    def get_success_url(self):
        return self.url_retorno()

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, f"No se puede eliminar «{self.object}»: ya está en uso.")
            return redirect(self.url_retorno())
