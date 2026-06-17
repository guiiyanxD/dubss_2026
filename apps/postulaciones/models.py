from django.db import models
from simple_history.models import HistoricalRecords


class Postulacion(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        ENVIADA = "ENVIADA", "Enviada"
        EN_REVISION = "EN_REVISION", "En Revisión"
        APROBADA = "APROBADA", "Aprobada"
        PROCESADA = "PROCESADA", "Procesada"
        ADJUDICADA = "ADJUDICADA", "Adjudicada"
        NO_ADJUDICADA = "NO_ADJUDICADA", "No Adjudicada"
        LISTA_ESPERA = "LISTA_ESPERA", "Lista de Espera"
        RECHAZADA_NO_PRESENTACION = "RECHAZADA_NO_PRESENTACION", "Rechazada - No Presentación"
        RECHAZADA_IDENTIDAD = "RECHAZADA_IDENTIDAD", "Rechazada - Identidad"
        RECHAZADA_DOCUMENTACION = "RECHAZADA_DOCUMENTACION", "Rechazada - Documentación"

    ESTADOS_ACTIVOS = [
        Estado.BORRADOR,
        Estado.ENVIADA,
        Estado.EN_REVISION,
        Estado.APROBADA,
    ]

    estudiante = models.ForeignKey(
        "acceso.Usuario",
        on_delete=models.PROTECT,
        related_name="postulaciones",
        verbose_name="estudiante",
    )
    convocatoria = models.ForeignKey(
        "convocatorias.Convocatoria",
        on_delete=models.PROTECT,
        related_name="postulaciones",
        verbose_name="convocatoria",
    )
    beca = models.ForeignKey(
        "convocatorias.Beca",
        on_delete=models.PROTECT,
        related_name="postulaciones",
        verbose_name="beca",
    )
    formulario = models.ForeignKey(
        "configuracion.FormularioSocioeconomico",
        on_delete=models.PROTECT,
        related_name="postulaciones",
        verbose_name="formulario socioeconómico",
    )
    estado = models.CharField(
        "estado",
        max_length=30,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_envio = models.DateTimeField("fecha de envío", null=True, blank=True)
    observaciones_identidad = models.TextField("observaciones de identidad", blank=True)
    puntaje_socioeconomico = models.DecimalField(
        "puntaje socioeconómico",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    numero_referencia = models.PositiveIntegerField(
        "número de referencia",
        unique=True,
        null=True,
        blank=True,
        help_text="Asignado al enviar la postulación; identifica la constancia impresa.",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "postulación"
        verbose_name_plural = "postulaciones"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.estudiante.email} — {self.convocatoria} ({self.get_estado_display()})"


class DocumentoPostulacion(models.Model):
    postulacion = models.ForeignKey(
        Postulacion,
        on_delete=models.CASCADE,
        related_name="documentos",
        verbose_name="postulación",
    )
    tipo_documento = models.ForeignKey(
        "convocatorias.TipoDocumento",
        on_delete=models.PROTECT,
        related_name="documentos_postulacion",
        verbose_name="tipo de documento",
    )
    validado = models.BooleanField(
        "validado",
        null=True,
        blank=True,
        help_text="None=pendiente, True=aprobado, False=rechazado",
    )
    archivo = models.FileField(
        "archivo digitalizado",
        upload_to="documentos/",
        null=True,
        blank=True,
    )
    fecha_validacion = models.DateTimeField("fecha de validación", null=True, blank=True)

    class Meta:
        verbose_name = "documento de postulación"
        verbose_name_plural = "documentos de postulación"
        unique_together = [("postulacion", "tipo_documento")]

    def __str__(self):
        return f"{self.tipo_documento} — {self.postulacion}"


class ContadorReferencia(models.Model):
    """Fila única que genera números de referencia secuenciales para constancias.

    Se usa con select_for_update() para evitar números duplicados entre envíos
    concurrentes, sin derivar el número del PK de Postulacion.
    """

    ultimo_numero = models.PositiveIntegerField("último número emitido", default=0)

    class Meta:
        verbose_name = "contador de referencia"
        verbose_name_plural = "contador de referencia"

    @classmethod
    def siguiente(cls):
        contador, _ = cls.objects.select_for_update().get_or_create(pk=1)
        contador.ultimo_numero += 1
        contador.save(update_fields=["ultimo_numero"])
        return contador.ultimo_numero
