from django.urls import path

from .controllers import cuestionarios as c
from .controllers import evaluaciones as e
from .controllers import menu, periodos as per

urlpatterns = [
    path("", menu.inicio, name="inicio"),

    # Cuestionarios
    path("cuestionarios/", c.CuestionarioLista.as_view(), name="cuestionario_lista"),
    path("cuestionarios/nuevo/", c.CuestionarioCrear.as_view(), name="cuestionario_crear"),
    path("cuestionarios/<int:pk>/", c.CuestionarioDetalle.as_view(), name="cuestionario_detalle"),
    path("cuestionarios/<int:pk>/editar/", c.CuestionarioEditar.as_view(), name="cuestionario_editar"),
    path("cuestionarios/<int:pk>/eliminar/", c.CuestionarioEliminar.as_view(), name="cuestionario_eliminar"),

    # Secciones
    path("cuestionarios/<int:padre_pk>/secciones/nueva/", c.SeccionCrear.as_view(), name="seccion_crear"),
    path("secciones/<int:pk>/editar/", c.SeccionEditar.as_view(), name="seccion_editar"),
    path("secciones/<int:pk>/eliminar/", c.SeccionEliminar.as_view(), name="seccion_eliminar"),

    # Preguntas
    path("secciones/<int:padre_pk>/preguntas/nueva/", c.PreguntaCrear.as_view(), name="pregunta_crear"),
    path("preguntas/<int:pk>/editar/", c.PreguntaEditar.as_view(), name="pregunta_editar"),
    path("preguntas/<int:pk>/eliminar/", c.PreguntaEliminar.as_view(), name="pregunta_eliminar"),

    # Opciones
    path("preguntas/<int:padre_pk>/opciones/nueva/", c.OpcionCrear.as_view(), name="opcion_crear"),
    path("opciones/<int:pk>/editar/", c.OpcionEditar.as_view(), name="opcion_editar"),
    path("opciones/<int:pk>/eliminar/", c.OpcionEliminar.as_view(), name="opcion_eliminar"),

    # Periodos
    path("periodos/", per.PeriodoLista.as_view(), name="periodo_lista"),
    path("periodos/nuevo/", per.PeriodoCrear.as_view(), name="periodo_crear"),
    path("periodos/<int:pk>/editar/", per.PeriodoEditar.as_view(), name="periodo_editar"),
    path("periodos/<int:pk>/eliminar/", per.PeriodoEliminar.as_view(), name="periodo_eliminar"),

    # Evaluaciones (Admin)
    path("evaluaciones/", e.EvaluacionLista.as_view(), name="evaluacion_lista"),
    path("evaluaciones/nueva/", e.EvaluacionCrear.as_view(), name="evaluacion_crear"),
    path("evaluaciones/<int:pk>/", e.EvaluacionDetalle.as_view(), name="evaluacion_detalle"),
    path("evaluaciones/<int:pk>/editar/", e.EvaluacionEditar.as_view(), name="evaluacion_editar"),
    path("evaluaciones/<int:pk>/eliminar/", e.EvaluacionEliminar.as_view(), name="evaluacion_eliminar"),

    # Evaluador
    path("mis-evaluaciones/<int:pk>/responder/", e.ResponderEvaluacion.as_view(), name="evaluacion_responder"),
]
