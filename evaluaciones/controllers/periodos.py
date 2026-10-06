"""CONTROLADOR (MVC): gestión de periodos."""
from accounts.mixins import CrudCrear, CrudEditar, CrudEliminar, CrudLista

from ..forms import PeriodoForm
from ..models import Periodo


class PeriodoLista(CrudLista):
    template_name = "periodos/lista.html"
    context_object_name = "periodos"
    queryset = Periodo.objects.order_by("-fecha_apertura")


class PeriodoCrear(CrudCrear):
    model, form_class = Periodo, PeriodoForm
    url_lista, titulo = "periodo_lista", "Nuevo periodo"


class PeriodoEditar(CrudEditar):
    model, form_class = Periodo, PeriodoForm
    url_lista, titulo = "periodo_lista", "Editar periodo"


class PeriodoEliminar(CrudEliminar):
    model = Periodo
    url_lista, titulo = "periodo_lista", "Eliminar periodo"
    aviso = "Si el periodo ya tiene evaluaciones asociadas no se podrá eliminar."
