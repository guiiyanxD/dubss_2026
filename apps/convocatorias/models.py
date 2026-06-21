from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class Beca(models.Model):
    nombre = models.CharField("nombre", max_length=150, unique=True)
    descripcion = models.TextField("descripción", blank=True)
    activa = models.BooleanField("activa", default=True)

    # CU15 — Ponderación configurable por beca. Los defaults reproducen exactamente
    # la fórmula que estaba hardcodeada en apps.reportes.services antes de CU15.
    peso_ingreso = models.PositiveSmallIntegerField("peso: ingreso familiar (%)", default=40)
    peso_desempleo = models.PositiveSmallIntegerField("peso: desempleo (%)", default=20)
    peso_familiares = models.PositiveSmallIntegerField(
        "peso: cantidad de familiares (%)", default=20
    )
    peso_no_propietario = models.PositiveSmallIntegerField(
        "peso: no propietario de vivienda (%)", default=10
    )
    peso_sin_beca_previa = models.PositiveSmallIntegerField("peso: sin beca previa (%)", default=10)

    class Meta:
        verbose_name = "beca"
        verbose_name_plural = "becas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def clean(self):
        suma = (
            self.peso_ingreso
            + self.peso_desempleo
            + self.peso_familiares
            + self.peso_no_propietario
            + self.peso_sin_beca_previa
        )
        if suma != 100:
            raise ValidationError(
                f"La suma de los pesos de ponderación debe ser 100 (actual: {suma})."
            )


class TipoDocumento(models.Model):
    nombre = models.CharField("nombre", max_length=150, unique=True)
    descripcion = models.TextField("descripción", blank=True)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "tipo de documento"
        verbose_name_plural = "tipos de documento"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Convocatoria(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        PUBLICADA = "PUBLICADA", "Publicada"
        CERRADA = "CERRADA", "Cerrada"

    nombre = models.CharField("nombre", max_length=200)
    descripcion = models.TextField("descripción", blank=True)
    fecha_apertura = models.DateTimeField("fecha de apertura")
    fecha_cierre = models.DateTimeField("fecha de cierre")
    estado = models.CharField(
        "estado", max_length=20, choices=Estado.choices, default=Estado.BORRADOR
    )
    becas = models.ManyToManyField(Beca, verbose_name="becas disponibles", blank=True)
    documentos_requeridos = models.ManyToManyField(
        TipoDocumento, verbose_name="documentos requeridos", blank=True
    )
    creada_por = models.ForeignKey(
        "acceso.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        related_name="convocatorias_creadas",
        verbose_name="creada por",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "convocatoria"
        verbose_name_plural = "convocatorias"
        ordering = ["-fecha_apertura"]

    def __str__(self):
        return self.nombre

    def esta_vigente(self):
        now = timezone.now()
        return (
            self.estado == self.Estado.PUBLICADA and self.fecha_apertura <= now <= self.fecha_cierre
        )
