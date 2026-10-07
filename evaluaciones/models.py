from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class RespuestaInvalida(Exception):
    """Se lanza cuando las respuestas enviadas no cumplen las reglas del cuestionario."""

    def __init__(self, errores):
        super().__init__("Respuestas inválidas")
        self.errores = errores  # {id_pregunta: mensaje}


class CuestionarioManager(models.Manager):
    def con_totales(self):
        return self.annotate(
            total_secciones=models.Count("secciones", distinct=True),
            total_preguntas=models.Count("secciones__preguntas", distinct=True),
        )

    def con_estructura(self):
        return self.prefetch_related("secciones__preguntas__opciones")


class Cuestionario(models.Model):
    objects = CuestionarioManager()

    @property
    def cuestionario_raiz(self):
        return self

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Seccion(models.Model):
    @property
    def cuestionario_raiz(self):
        return self.cuestionario

    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE, related_name="secciones")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Pregunta(models.Model):
    @property
    def cuestionario_raiz(self):
        return self.seccion.cuestionario

    class Tipo(models.TextChoices):
        SIMPLE = "SIMPLE", "Simple"
        LIBRE = "LIBRE", "Libre"

    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE, related_name="preguntas")
    descripcion = models.CharField(max_length=300)
    comentarios = models.TextField(blank=True)
    tipo = models.CharField(max_length=6, choices=Tipo.choices)
    orden = models.PositiveIntegerField(default=1)
    requerida = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden"]

    def __str__(self):
        return self.descripcion


class Opcion(models.Model):
    @property
    def cuestionario_raiz(self):
        return self.pregunta.seccion.cuestionario

    # Solo aplica a preguntas de tipo SIMPLE
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name="opciones")
    nombre = models.CharField(max_length=100)
    orden = models.PositiveIntegerField(default=1)
    valor = models.IntegerField()

    class Meta:
        ordering = ["orden"]

    def __str__(self):
        return self.nombre


class PeriodoManager(models.Manager):
    def activos(self):
        hoy = timezone.localdate()
        return self.filter(fecha_apertura__lte=hoy, fecha_cierre__gte=hoy)


class Periodo(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_apertura = models.DateField(db_index=True)
    fecha_cierre = models.DateField(db_index=True)

    objects = PeriodoManager()

    class Meta:
        ordering = ["-fecha_apertura"]
        indexes = [
            models.Index(fields=["fecha_apertura", "fecha_cierre"], name="idx_periodo_fechas"),
        ]

    @property
    def esta_activo(self):
        hoy = timezone.localdate()
        return self.fecha_apertura <= hoy <= self.fecha_cierre

    def clean(self):
        if self.fecha_apertura and self.fecha_cierre and self.fecha_cierre < self.fecha_apertura:
            raise ValidationError({"fecha_cierre": "La fecha de cierre no puede ser anterior a la de apertura."})

    def __str__(self):
        return self.nombre


class EvaluacionManager(models.Manager):
    def con_relaciones(self):
        return self.select_related("cuestionario", "periodo", "evaluador", "evaluado").order_by("-pk")

    def con_respuestas(self):
        return (
            self.select_related("cuestionario", "periodo", "evaluador", "evaluado")
            .prefetch_related(
                "respuestas_simples__opcion",
                "respuestas_libres",
                "cuestionario__secciones__preguntas__opciones",
            )
            .order_by("-pk")
        )

    def por_responder_de(self, usuario):
        """Evaluaciones PENDIENTES o EN PROCESO del usuario (evaluador) cuyo periodo está activo por fechas."""
        hoy = timezone.localdate()
        return (
            self.select_related("evaluado", "periodo", "cuestionario")
            .filter(
                evaluador=usuario,
                estado__in=[Evaluacion.Estado.PENDIENTE, Evaluacion.Estado.PROCESO],
                periodo__fecha_apertura__lte=hoy,
                periodo__fecha_cierre__gte=hoy,
            )
        )

    def pendientes_de(self, usuario):
        """Alias para retrocompatibilidad."""
        return self.por_responder_de(usuario)


class Evaluacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PROCESO = "PROCESO", "Proceso"
        TERMINADA = "TERMINADA", "Terminada"

    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.PROTECT)
    periodo = models.ForeignKey(Periodo, on_delete=models.PROTECT)
    evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="evaluaciones_realizadas")
    evaluado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="evaluaciones_recibidas")
    cargo_evaluado = models.CharField(max_length=100)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True)
    fecha_hora_inicio = models.DateTimeField(null=True, blank=True)
    fecha_hora_final = models.DateTimeField(null=True, blank=True)

    @property
    def cargo_real(self):
        """Retorna el cargo real del evaluado, corrigiendo cualquier valor de rol de sistema."""
        val = (self.cargo_evaluado or "").strip()
        if not val or val.lower() in ["user", "admin"]:
            return "Trabajador"
        return val

    objects = EvaluacionManager()

    class Meta:
        ordering = ["-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["evaluador", "evaluado", "periodo", "cuestionario"],
                name="unique_evaluacion_evaluador_evaluado_periodo_cuestionario",
            ),
            models.CheckConstraint(
                condition=~models.Q(evaluador=models.F("evaluado")),
                name="check_evaluador_diferente_evaluado",
            ),
        ]
        indexes = [
            models.Index(fields=["evaluador", "estado"], name="idx_eval_evaluador_estado"),
            models.Index(fields=["evaluado", "estado"], name="idx_eval_evaluado_estado"),
            models.Index(fields=["estado"], name="idx_eval_estado"),
        ]

    def clean(self):
        if self.evaluador_id and self.evaluador_id == self.evaluado_id:
            raise ValidationError({"evaluado": "El evaluado debe ser distinto de quien evalúa."})

    def marcar_inicio(self):
        """Marca el inicio de la evaluación (transiciona a PROCESO si estaba PENDIENTE)."""
        actualizar = []
        if not self.fecha_hora_inicio:
            self.fecha_hora_inicio = timezone.now()
            actualizar.append("fecha_hora_inicio")
        if self.estado == self.Estado.PENDIENTE:
            self.estado = self.Estado.PROCESO
            actualizar.append("estado")
        if actualizar:
            self.save(update_fields=actualizar)

    def obtener_respuestas_dict(self):
        """Retorna dict {id_pregunta: string_valor} con las respuestas guardadas (borrador o final)."""
        res = {}
        for r in self.respuestas_simples.all():
            res[r.pregunta_id] = str(r.opcion_id)
        for r in self.respuestas_libres.all():
            res[r.pregunta_id] = r.texto
        return res

    def guardar_borrador(self, respuestas):
        """Guarda parcialidades/borrador sin exigir que todas las preguntas obligatorias se respondan."""
        preguntas = {
            p.pk: p for p in Pregunta.objects.filter(seccion__cuestionario=self.cuestionario).prefetch_related("opciones")
        }
        simples, libres = [], []
        for p_id, val in respuestas.items():
            if p_id not in preguntas:
                continue
            p = preguntas[p_id]
            texto = (str(val) if val is not None else "").strip()
            if not texto:
                continue
            if p.tipo == Pregunta.Tipo.SIMPLE:
                opcion = next((o for o in p.opciones.all() if str(o.pk) == texto), None)
                if opcion:
                    simples.append(RespuestaSimple(evaluacion=self, pregunta=p, opcion=opcion))
            else:
                libres.append(RespuestaLibre(evaluacion=self, pregunta=p, texto=texto))

        with transaction.atomic():
            self.respuestas_simples.all().delete()
            self.respuestas_libres.all().delete()
            if simples:
                RespuestaSimple.objects.bulk_create(simples)
            if libres:
                RespuestaLibre.objects.bulk_create(libres)

            actualizar = []
            if self.estado == self.Estado.PENDIENTE:
                self.estado = self.Estado.PROCESO
                actualizar.append("estado")
            if not self.fecha_hora_inicio:
                self.fecha_hora_inicio = timezone.now()
                actualizar.append("fecha_hora_inicio")
            if actualizar:
                self.save(update_fields=actualizar)

    def registrar_respuestas(self, respuestas):
        """Valida y guarda las respuestas definitivas.
        Si todo es válido, la evaluación queda TERMINADA. Si no, lanza RespuestaInvalida."""
        preguntas = (
            Pregunta.objects.filter(seccion__cuestionario=self.cuestionario)
            .prefetch_related("opciones")
            .order_by("seccion_id", "orden")
        )
        errores, simples, libres = {}, [], []
        for p in preguntas:
            valor = (str(respuestas.get(p.pk)) if respuestas.get(p.pk) is not None else "").strip()
            if not valor:
                if p.requerida:
                    errores[p.pk] = "Esta pregunta es obligatoria."
                continue
            if p.tipo == Pregunta.Tipo.SIMPLE:
                opcion = next((o for o in p.opciones.all() if str(o.pk) == valor), None)
                if opcion is None:
                    errores[p.pk] = "Selecciona una opción válida."
                    continue
                simples.append(RespuestaSimple(evaluacion=self, pregunta=p, opcion=opcion))
            else:
                libres.append(RespuestaLibre(evaluacion=self, pregunta=p, texto=valor))

        if errores:
            raise RespuestaInvalida(errores)

        with transaction.atomic():
            self.respuestas_simples.all().delete()
            self.respuestas_libres.all().delete()
            if simples:
                RespuestaSimple.objects.bulk_create(simples)
            if libres:
                RespuestaLibre.objects.bulk_create(libres)

            self.fecha_hora_final = timezone.now()
            self.fecha_hora_inicio = self.fecha_hora_inicio or self.fecha_hora_final
            self.estado = self.Estado.TERMINADA
            self.save(update_fields=["fecha_hora_inicio", "fecha_hora_final", "estado"])

    def resumen_respuestas(self):
        """[(sección, [(pregunta, respuesta_en_texto), ...]), ...] para mostrar resultados."""
        simples = {r.pregunta_id: r.opcion for r in self.respuestas_simples.select_related("opcion")}
        libres = {r.pregunta_id: r.texto for r in self.respuestas_libres.all()}
        resumen = []
        secciones = self.cuestionario.secciones.prefetch_related("preguntas")
        for s in secciones:
            filas = []
            for p in s.preguntas.all():
                if p.tipo == Pregunta.Tipo.SIMPLE:
                    o = simples.get(p.pk)
                    texto = f"{o.nombre} (valor {o.valor})" if o else ""
                else:
                    texto = libres.get(p.pk, "")
                filas.append((p, texto))
            resumen.append((s, filas))
        return resumen

    def __str__(self):
        return f"{self.evaluador} → {self.evaluado} ({self.periodo})"


class RespuestaSimple(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name="respuestas_simples")
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    opcion = models.ForeignKey(Opcion, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("evaluacion", "pregunta")


class RespuestaLibre(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name="respuestas_libres")
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    texto = models.TextField()

    class Meta:
        unique_together = ("evaluacion", "pregunta")

