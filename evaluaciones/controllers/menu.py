"""CONTROLADOR (MVC): menú principal."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models import Evaluacion


@login_required
def inicio(request):
    # Cualquier usuario ve sus evaluaciones pendientes del periodo activo
    evaluaciones = Evaluacion.objects.pendientes_de(request.user)
    return render(request, "evaluaciones/inicio.html", {"evaluaciones": evaluaciones})
