from django.db import models


class ResumenIA(models.Model):
    """Resumen narrativo de KPIs generado por el LLM local (Ollama, PC de mesa)."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PROCESANDO = "PROCESANDO", "Procesando"
        COMPLETADO = "COMPLETADO", "Completado"
        ERROR = "ERROR", "Error"

    convocatoria = models.ForeignKey(
        "convocatorias.Convocatoria",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resumenes_ia",
        verbose_name="convocatoria",
        help_text="Vacío = resumen agregado de todas las convocatorias.",
    )
    usuario = models.ForeignKey(
        "acceso.Usuario",
        on_delete=models.CASCADE,
        related_name="resumenes_ia",
        verbose_name="solicitado por",
    )
    prompt_adicional = models.TextField("instrucción adicional", blank=True)
    estado = models.CharField(
        "estado", max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )
    resultado = models.TextField("resultado", blank=True)
    error_detalle = models.TextField("detalle del error", blank=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_completado = models.DateTimeField("fecha de completado", null=True, blank=True)

    class Meta:
        verbose_name = "resumen con IA"
        verbose_name_plural = "resúmenes con IA"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        destino = self.convocatoria.nombre if self.convocatoria else "todas las convocatorias"
        return f"Resumen IA — {destino} ({self.get_estado_display()})"


class Conversacion(models.Model):
    """Conversación de chat con el LLM local, con tool calling sobre datos reales."""

    usuario = models.ForeignKey(
        "acceso.Usuario",
        on_delete=models.CASCADE,
        related_name="conversaciones_ia",
        verbose_name="usuario",
    )
    titulo = models.CharField("título", max_length=200, blank=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "conversación con IA"
        verbose_name_plural = "conversaciones con IA"
        ordering = ["-fecha_actualizacion"]

    def __str__(self):
        return self.titulo or f"Conversación #{self.pk}"


class MensajeChat(models.Model):
    """Mensaje individual dentro de una Conversacion."""

    class Rol(models.TextChoices):
        USUARIO = "USUARIO", "Usuario"
        ASISTENTE = "ASISTENTE", "Asistente"
        SISTEMA = "SISTEMA", "Sistema"

    conversacion = models.ForeignKey(
        Conversacion,
        on_delete=models.CASCADE,
        related_name="mensajes",
        verbose_name="conversación",
    )
    rol = models.CharField("rol", max_length=20, choices=Rol.choices)
    contenido = models.TextField("contenido")
    tools_usadas = models.JSONField("tools usadas", null=True, blank=True)
    archivo = models.FileField("archivo adjunto", upload_to="chat_ia/%Y/%m/", null=True, blank=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "mensaje de chat"
        verbose_name_plural = "mensajes de chat"
        ordering = ["fecha_creacion"]

    def __str__(self):
        return f"{self.get_rol_display()}: {self.contenido[:50]}"
