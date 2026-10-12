from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Usuario
from evaluaciones.models import (
    Cuestionario,
    Evaluacion,
    MENSAJE_RESPUESTA_LIBRE_CORTA,
    Opcion,
    Periodo,
    Pregunta,
    RespuestaInvalida,
    Seccion,
)


class EvaluacionTestCase(TestCase):
    def setUp(self):
        self.evaluador = Usuario.objects.create_user(
            email="evaluador@test.com", password="password123", nombre_completo="Juan Evaluador"
        )
        self.evaluado = Usuario.objects.create_user(
            email="evaluado@test.com", password="password123", nombre_completo="Pedro Evaluado"
        )

        hoy = timezone.localdate()
        self.periodo = Periodo.objects.create(
            nombre="Periodo Q1 2026",
            fecha_apertura=hoy - timedelta(days=5),
            fecha_cierre=hoy + timedelta(days=5),
        )

        self.cuestionario = Cuestionario.objects.create(
            nombre="Evaluación de Desempeño", descripcion="Cuestionario anual", estado=True
        )
        self.seccion = Seccion.objects.create(
            cuestionario=self.cuestionario, nombre="Habilidades Técnicas", descripcion="Sección 1"
        )

        self.pregunta_simple = Pregunta.objects.create(
            seccion=self.seccion,
            descripcion="¿Cumple con los plazos?",
            tipo=Pregunta.Tipo.SIMPLE,
            orden=1,
            requerida=True,
        )
        self.opcion_excelente = Opcion.objects.create(
            pregunta=self.pregunta_simple, nombre="Excelente", orden=1, valor=5
        )
        self.opcion_regular = Opcion.objects.create(
            pregunta=self.pregunta_simple, nombre="Regular", orden=2, valor=3
        )

        self.pregunta_libre = Pregunta.objects.create(
            seccion=self.seccion,
            descripcion="Comentarios adicionales",
            tipo=Pregunta.Tipo.LIBRE,
            orden=2,
            requerida=False,
        )

    def crear_evaluacion(self):
        sufijo = Evaluacion.objects.count() + 1
        hoy = timezone.localdate()
        periodo = Periodo.objects.create(
            nombre=f"Periodo prueba {sufijo}",
            fecha_apertura=hoy - timedelta(days=5),
            fecha_cierre=hoy + timedelta(days=5),
        )
        return Evaluacion.objects.create(
            cuestionario=self.cuestionario,
            periodo=periodo,
            evaluador=self.evaluador,
            evaluado=self.evaluado,
            cargo_evaluado="Desarrollador",
        )

    def test_creacion_evaluacion_estado_inicial_pendiente(self):
        evaluacion = Evaluacion.objects.create(
            cuestionario=self.cuestionario,
            periodo=self.periodo,
            evaluador=self.evaluador,
            evaluado=self.evaluado,
            cargo_evaluado="Desarrollador Senior",
        )
        self.assertEqual(evaluacion.estado, Evaluacion.Estado.PENDIENTE)
        self.assertIsNone(evaluacion.fecha_hora_inicio)
        self.assertIsNone(evaluacion.fecha_hora_final)

    def test_marcar_inicio_cambia_a_proceso(self):
        evaluacion = Evaluacion.objects.create(
            cuestionario=self.cuestionario,
            periodo=self.periodo,
            evaluador=self.evaluador,
            evaluado=self.evaluado,
            cargo_evaluado="Desarrollador",
        )
        evaluacion.marcar_inicio()
        self.assertEqual(evaluacion.estado, Evaluacion.Estado.PROCESO)
        self.assertIsNotNone(evaluacion.fecha_hora_inicio)



    def test_registrar_respuestas_completa_evaluacion(self):
        evaluacion = self.crear_evaluacion()
        evaluacion.registrar_respuestas({
            self.pregunta_simple.pk: str(self.opcion_excelente.pk),
            self.pregunta_libre.pk: "Buen desempeño general",
        })
        evaluacion.refresh_from_db()
        self.assertEqual(evaluacion.estado, Evaluacion.Estado.TERMINADA)
        self.assertIsNotNone(evaluacion.fecha_hora_final)
        self.assertEqual(evaluacion.respuestas_simples.count(), 1)
        self.assertEqual(evaluacion.respuestas_libres.count(), 1)

    def test_respuesta_libre_rechaza_menos_de_tres_caracteres_validos(self):
        casos_invalidos = ["A", "No", "   ", " A "]

        for texto in casos_invalidos:
            with self.subTest(texto=texto):
                evaluacion = self.crear_evaluacion()
                with self.assertRaises(RespuestaInvalida) as ctx:
                    evaluacion.registrar_respuestas({
                        self.pregunta_simple.pk: str(self.opcion_excelente.pk),
                        self.pregunta_libre.pk: texto,
                    })

                self.assertEqual(ctx.exception.errores[self.pregunta_libre.pk], MENSAJE_RESPUESTA_LIBRE_CORTA)
                evaluacion.refresh_from_db()
                self.assertEqual(evaluacion.estado, Evaluacion.Estado.PENDIENTE)
                self.assertIsNone(evaluacion.fecha_hora_final)
                self.assertEqual(evaluacion.respuestas_libres.count(), 0)

    def test_respuesta_libre_acepta_tres_o_mas_caracteres_validos(self):
        casos_validos = [("Sol", "Sol"), ("Hola", "Hola"), ("  Sol  ", "Sol")]

        for texto, esperado in casos_validos:
            with self.subTest(texto=texto):
                evaluacion = self.crear_evaluacion()
                evaluacion.registrar_respuestas({
                    self.pregunta_simple.pk: str(self.opcion_excelente.pk),
                    self.pregunta_libre.pk: texto,
                })

                evaluacion.refresh_from_db()
                self.assertEqual(evaluacion.estado, Evaluacion.Estado.TERMINADA)
                self.assertEqual(evaluacion.respuestas_libres.get(pregunta=self.pregunta_libre).texto, esperado)

    def test_respuesta_libre_opcional_vacia_se_conserva_opcional(self):
        evaluacion = self.crear_evaluacion()
        evaluacion.registrar_respuestas({
            self.pregunta_simple.pk: str(self.opcion_excelente.pk),
            self.pregunta_libre.pk: "",
        })

        evaluacion.refresh_from_db()
        self.assertEqual(evaluacion.estado, Evaluacion.Estado.TERMINADA)
        self.assertEqual(evaluacion.respuestas_simples.count(), 1)
        self.assertEqual(evaluacion.respuestas_libres.count(), 0)

    def test_respuesta_libre_obligatoria_vacia_sigue_siendo_obligatoria(self):
        pregunta_requerida = Pregunta.objects.create(
            seccion=self.seccion,
            descripcion="Justificación obligatoria",
            tipo=Pregunta.Tipo.LIBRE,
            orden=3,
            requerida=True,
        )
        evaluacion = self.crear_evaluacion()

        with self.assertRaises(RespuestaInvalida) as ctx:
            evaluacion.registrar_respuestas({
                self.pregunta_simple.pk: str(self.opcion_excelente.pk),
                self.pregunta_libre.pk: "",
                pregunta_requerida.pk: "",
            })

        self.assertEqual(ctx.exception.errores[pregunta_requerida.pk], "Esta pregunta es obligatoria.")

    def test_registrar_respuestas_valida_obligatorias(self):
        evaluacion = self.crear_evaluacion()
        with self.assertRaises(RespuestaInvalida):
            # No se envía la pregunta simple obligatoria
            evaluacion.registrar_respuestas({self.pregunta_libre.pk: "Texto libre solamente"})

    def test_validacion_evaluador_distinto_evaluado(self):
        evaluacion = Evaluacion(
            cuestionario=self.cuestionario,
            periodo=self.periodo,
            evaluador=self.evaluador,
            evaluado=self.evaluador,  # Mismo usuario
            cargo_evaluado="Desarrollador",
        )
        with self.assertRaises(ValidationError):
            evaluacion.full_clean()

    def test_manager_por_responder_de(self):
        evaluacion = Evaluacion.objects.create(
            cuestionario=self.cuestionario,
            periodo=self.periodo,
            evaluador=self.evaluador,
            evaluado=self.evaluado,
            cargo_evaluado="Desarrollador",
        )
        pendientes = list(Evaluacion.objects.por_responder_de(self.evaluador))
        self.assertIn(evaluacion, pendientes)

        evaluacion.marcar_inicio()
        pendientes_en_proceso = list(Evaluacion.objects.por_responder_de(self.evaluador))
        self.assertIn(evaluacion, pendientes_en_proceso)

        evaluacion.registrar_respuestas({self.pregunta_simple.pk: str(self.opcion_excelente.pk)})
        pendientes_despues = list(Evaluacion.objects.por_responder_de(self.evaluador))
        self.assertNotIn(evaluacion, pendientes_despues)
