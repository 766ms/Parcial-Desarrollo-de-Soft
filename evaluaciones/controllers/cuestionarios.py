"""CONTROLADOR (MVC) del CRUD de cuestionarios, secciones, preguntas y opciones.
Pide/guarda datos en el MODELO y entrega los resultados a la VISTA (templates)."""
from django.contrib import messages
from django.db.models import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import AdminMixin

from ..forms import CuestionarioForm, OpcionForm, PreguntaForm, SeccionForm
from ..models import Cuestionario, Opcion, Pregunta, Seccion


# ------------------------- Cuestionario -------------------------
class CuestionarioLista(AdminMixin, ListView):
    template_name = "cuestionarios/lista.html"
    context_object_name = "cuestionarios"

    def get_queryset(self):
        return Cuestionario.objects.con_totales()


class CuestionarioDetalle(AdminMixin, DetailView):
    template_name = "cuestionarios/detalle.html"
    context_object_name = "cuestionario"

    def get_queryset(self):
        return Cuestionario.objects.con_estructura()


class CuestionarioCrear(AdminMixin, CreateView):
    model = Cuestionario
    form_class = CuestionarioForm
    template_name = "crud/form.html"
    titulo = "Nuevo cuestionario"

    def url_retorno(self):
        return reverse("cuestionario_lista")

    def get_success_url(self):
        return reverse("cuestionario_detalle", args=[self.object.pk])


class CuestionarioEditar(AdminMixin, UpdateView):
    model = Cuestionario
    form_class = CuestionarioForm
    template_name = "crud/form.html"
    titulo = "Editar cuestionario"

    def url_retorno(self):
        return reverse("cuestionario_detalle", args=[self.object.pk])

    def get_success_url(self):
        return self.url_retorno()


class CuestionarioEliminar(AdminMixin, DeleteView):
    model = Cuestionario
    template_name = "crud/confirmar_eliminar.html"
    titulo = "Eliminar cuestionario"
    aviso = "Se eliminará también todo su contenido (secciones, preguntas y opciones)."

    def url_retorno(self):
        return reverse("cuestionario_detalle", args=[self.object.pk])

    def get_success_url(self):
        return reverse("cuestionario_lista")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar: el cuestionario ya está asignado a evaluaciones.")
            return redirect(self.url_retorno())


# ---------- Base común para Sección, Pregunta y Opción (todas cuelgan de un cuestionario) ----------
class HijoMixin(AdminMixin):
    def url_retorno(self):
        origen = self.padre if hasattr(self, "padre") else self.object
        return reverse("cuestionario_detalle", args=[origen.cuestionario_raiz.pk])

    def get_success_url(self):
        return self.url_retorno()


class HijoCrear(HijoMixin, CreateView):
    template_name = "crud/form.html"
    padre_model = None   # modelo del padre (p. ej. Cuestionario)
    padre_campo = None   # campo FK del hijo hacia el padre

    @cached_property
    def padre(self):
        return get_object_or_404(self.padre_model, pk=self.kwargs["padre_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.model(**{self.padre_campo: self.padre})
        return kwargs


class HijoEditar(HijoMixin, UpdateView):
    template_name = "crud/form.html"


class HijoEliminar(HijoMixin, DeleteView):
    template_name = "crud/confirmar_eliminar.html"


# ------------------------- Sección -------------------------
class SeccionCrear(HijoCrear):
    model, form_class = Seccion, SeccionForm
    padre_model, padre_campo = Cuestionario, "cuestionario"
    titulo = "Nueva sección"


class SeccionEditar(HijoEditar):
    model, form_class = Seccion, SeccionForm
    titulo = "Editar sección"


class SeccionEliminar(HijoEliminar):
    model = Seccion
    titulo = "Eliminar sección"
    aviso = "Se eliminarán también sus preguntas y opciones."


# ------------------------- Pregunta -------------------------
class PreguntaCrear(HijoCrear):
    model, form_class = Pregunta, PreguntaForm
    padre_model, padre_campo = Seccion, "seccion"
    titulo = "Nueva pregunta"


class PreguntaEditar(HijoEditar):
    model, form_class = Pregunta, PreguntaForm
    titulo = "Editar pregunta"


class PreguntaEliminar(HijoEliminar):
    model = Pregunta
    titulo = "Eliminar pregunta"
    aviso = "Se eliminarán también sus opciones."


# ------------------------- Opción (solo preguntas simples) -------------------------
class OpcionCrear(HijoCrear):
    model, form_class = Opcion, OpcionForm
    padre_model, padre_campo = Pregunta, "pregunta"
    titulo = "Nueva opción de respuesta"

    @cached_property
    def padre(self):
        pregunta = get_object_or_404(Pregunta, pk=self.kwargs["padre_pk"])
        if pregunta.tipo != Pregunta.Tipo.SIMPLE:
            raise Http404("Las preguntas de tipo libre no tienen opciones.")
        return pregunta


class OpcionEditar(HijoEditar):
    model, form_class = Opcion, OpcionForm
    titulo = "Editar opción"


class OpcionEliminar(HijoEliminar):
    model = Opcion
    titulo = "Eliminar opción"
