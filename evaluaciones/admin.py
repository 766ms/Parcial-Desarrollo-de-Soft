from django.contrib import admin

from . import models

for m in (models.Cuestionario, models.Seccion, models.Pregunta, models.Opcion,
          models.Periodo, models.Evaluacion, models.RespuestaSimple, models.RespuestaLibre):
    admin.site.register(m)
