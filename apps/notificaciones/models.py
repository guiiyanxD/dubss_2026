from django.db import models


class Notificacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        ENVIADA = "ENVIADA", "Enviada"
        ERROR = "ERROR", "Error"

    usuario = models.ForeignKey(
        "acceso.Usuario",
        on_delete=models.CASCADE,
        related_name="notificaciones",
        verbose_name="destinatario",
    )
    asunto = models.CharField("asunto", max_length=250)
    cuerpo = models.TextField("cuerpo")
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    error_detalle = models.TextField("detalle del error", blank=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_envio = models.DateTimeField("fecha de envío", null=True, blank=True)

    class Meta:
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"[{self.estado}] {self.asunto} → {self.usuario.email}"
