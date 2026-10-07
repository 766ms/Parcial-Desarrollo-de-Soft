"""CONTROLADOR (MVC): configuración de evaluaciones (Admin) y respuesta del cuestionario (evaluador)."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView

from accounts.mixins import AdminMixin, CrudCrear, CrudEditar, CrudEliminar, CrudLista

from ..forms import EvaluacionForm
from ..models import Evaluacion, RespuestaInvalida


# ---------------- Admin: CRUD de evaluaciones ----------------
class EvaluacionLista(CrudLista):
    template_name = "evaluaciones/lista.html"
    context_object_name = "evaluaciones"

    def get_queryset(self):
        return Evaluacion.objects.con_relaciones()


class EvaluacionDetalle(AdminMixin, DetailView):
    template_name = "evaluaciones/detalle.html"
    context_object_name = "evaluacion"

    def get_queryset(self):
        return Evaluacion.objects.con_respuestas()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["resumen"] = self.object.resumen_respuestas()
        return ctx


class EvaluacionCrear(CrudCrear):
    model, form_class = Evaluacion, EvaluacionForm
    url_lista, titulo = "evaluacion_lista", "Nueva evaluación"


class EvaluacionEditar(CrudEditar):
    model, form_class = Evaluacion, EvaluacionForm
    url_lista, titulo = "evaluacion_lista", "Editar evaluación"


class EvaluacionEliminar(CrudEliminar):
    model = Evaluacion
    url_lista, titulo = "evaluacion_lista", "Eliminar evaluación"
    aviso = "Se eliminarán también las respuestas registradas."


# ---------------- Evaluador: responder el cuestionario ----------------
class ResponderEvaluacion(LoginRequiredMixin, View):
    template_name = "evaluaciones/responder.html"

    def _evaluacion(self):
        # Solo evaluaciones PENDIENTES o PROCESO del usuario, con periodo activo por fechas
        return get_object_or_404(Evaluacion.objects.por_responder_de(self.request.user), pk=self.kwargs["pk"])

    def get(self, request, pk):
        evaluacion = self._evaluacion()
        evaluacion.marcar_inicio()
        valores_guardados = evaluacion.obtener_respuestas_dict()
        return self._mostrar(evaluacion, valores_guardados, {})

    def post(self, request, pk):
        evaluacion = self._evaluacion()
        valores = {int(k[2:]): v for k, v in request.POST.items() if k.startswith("p_") and k[2:].isdigit()}

        try:
            evaluacion.registrar_respuestas(valores)
        except RespuestaInvalida as e:
            messages.error(request, "Revisa las preguntas marcadas antes de enviar.")
            return self._mostrar(evaluacion, valores, e.errores)

        messages.success(request, "Evaluación enviada con éxito. ¡Gracias!")
        return redirect("inicio")

    def _mostrar(self, evaluacion, valores, errores):
        """Arma los datos que la VISTA necesita (sección → preguntas → opciones)."""
        secciones = []
        cuestionario_secciones = evaluacion.cuestionario.secciones.prefetch_related("preguntas__opciones")
        for s in cuestionario_secciones:
            preguntas = [
                {
                    "obj": p,
                    "campo": f"p_{p.pk}",
                    "valor": str(valores.get(p.pk, "")),
                    "error": errores.get(p.pk),
                    "opciones": [{"obj": o, "marcada": str(o.pk) == str(valores.get(p.pk, ""))} for o in p.opciones.all()],
                }
                for p in s.preguntas.all()
            ]
            secciones.append({"obj": s, "preguntas": preguntas})
        return render(self.request, self.template_name, {"evaluacion": evaluacion, "secciones": secciones})

