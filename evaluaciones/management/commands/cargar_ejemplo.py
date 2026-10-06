from django.core.management.base import BaseCommand

from evaluaciones.models import Cuestionario, Opcion, Pregunta, Seccion

FACTORES = ["Calidad del trabajo", "Conocimiento del trabajador", "Responsabilidad", "Actitud",
            "Toma de decisiones", "Innovación", "Sentido de pertenencia", "Cumplimiento de normas"]
OPCIONES = [("Excelente", 4), ("Bueno", 3), ("Regular", 2), ("Deficiente", 1)]

SECCIONES = [
    ("Concepto personal sobre el empleado",
     "Escriba su opinión de acuerdo con el conocimiento que tenga sobre su empleado.",
     [("¿Cuál ha sido el aspecto sobresaliente del empleado durante el año evaluado?", "LIBRE"),
      ("¿Cuál es el principal aporte que ha realizado el empleado durante el año evaluado?", "LIBRE")]),
    ("Factores claves de desempeño",
     "Evalúe su desempeño según los criterios enunciados.",
     [(f, "SIMPLE") for f in FACTORES]),
    ("Capacitaciones requeridas",
     "Mencionar las capacitaciones requeridas para el empleado que permitan fortalecer su desempeño.",
     [("¿Qué capacitaciones fueron requeridas para la evaluación desempeño?", "LIBRE")]),
]


class Command(BaseCommand):
    help = "Crea el cuestionario de ejemplo 'Encuesta de Desempeño' del enunciado."

    def handle(self, *args, **options):
        cuestionario, creado = Cuestionario.objects.get_or_create(
            nombre="Encuesta de Desempeño", defaults={"descripcion": "Evaluación anual de desempeño."})
        if not creado:
            self.stdout.write("El cuestionario de ejemplo ya existe.")
            return
        for nombre, descripcion, preguntas in SECCIONES:
            seccion = Seccion.objects.create(cuestionario=cuestionario, nombre=nombre, descripcion=descripcion)
            for orden, (texto, tipo) in enumerate(preguntas, start=1):
                pregunta = Pregunta.objects.create(seccion=seccion, descripcion=texto, tipo=tipo, orden=orden)
                if tipo == "SIMPLE":
                    for o, (nom, valor) in enumerate(OPCIONES, start=1):
                        Opcion.objects.create(pregunta=pregunta, nombre=nom, orden=o, valor=valor)
        self.stdout.write(self.style.SUCCESS("Cuestionario de ejemplo creado."))
