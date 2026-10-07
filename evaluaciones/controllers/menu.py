from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import Usuario
from ..models import Cuestionario, Evaluacion, Periodo


@login_required
def inicio(request):
    evaluaciones = Evaluacion.objects.por_responder_de(request.user)
    context = {
        "evaluaciones": evaluaciones,
    }
    if request.user.es_admin:
        context.update({
            "total_cuestionarios": Cuestionario.objects.count(),
            "total_usuarios": Usuario.objects.count(),
            "total_periodos": Periodo.objects.count(),
        })
    return render(request, "evaluaciones/inicio.html", context)
