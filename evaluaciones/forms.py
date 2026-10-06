from django import forms

from accounts.forms import EstiloMixin
from accounts.models import Usuario

from .models import Cuestionario, Evaluacion, Opcion, Periodo, Pregunta, Seccion


class CuestionarioForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Cuestionario
        fields = ["nombre", "descripcion", "estado"]
        labels = {"estado": "Activo"}


class SeccionForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Seccion
        fields = ["nombre", "descripcion"]


class PreguntaForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ["descripcion", "comentarios", "tipo", "orden", "requerida"]
        labels = {"requerida": "Respuesta requerida"}


class OpcionForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Opcion
        fields = ["nombre", "orden", "valor"]


class PeriodoForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Periodo
        fields = ["nombre", "fecha_apertura", "fecha_cierre"]
        labels = {"fecha_apertura": "Fecha de apertura", "fecha_cierre": "Fecha de cierre"}
        widgets = {
            "fecha_apertura": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_cierre": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class EvaluacionForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Evaluacion
        fields = ["cuestionario", "periodo", "evaluador", "evaluado", "cargo_evaluado", "estado"]
        labels = {"evaluador": "Usuario que evalúa", "evaluado": "Usuario evaluado",
                  "cargo_evaluado": "Cargo del evaluado"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # al crear, solo opciones vigentes
            self.fields["evaluador"].queryset = Usuario.objects.filter(estado=True)
            self.fields["evaluado"].queryset = Usuario.objects.filter(estado=True)
            self.fields["cuestionario"].queryset = Cuestionario.objects.filter(estado=True)
