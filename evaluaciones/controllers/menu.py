from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import Usuario
from ..models import Cuestionario, Evaluacion, Periodo


@login_required
def inicio(request):
    # Pendientes y en proceso: solo las que se pueden responder (periodo activo)
    por_responder = Evaluacion.objects.por_responder_de(request.user)
    # Terminadas: historial completo del evaluador, de cualquier periodo
    terminadas = Evaluacion.objects.con_relaciones().filter(
        evaluador=request.user, estado=Evaluacion.Estado.TERMINADA
    )
    context = {
        "evaluaciones": por_responder,
        "pendientes": por_responder.filter(estado=Evaluacion.Estado.PENDIENTE),
        "en_proceso": por_responder.filter(estado=Evaluacion.Estado.PROCESO),
        "terminadas": terminadas,
    }
    if request.user.es_admin:
        context.update({
            "total_cuestionarios": Cuestionario.objects.count(),
            "total_usuarios": Usuario.objects.count(),
            "total_periodos": Periodo.objects.count(),
        })
    return render(request, "evaluaciones/inicio.html", context)