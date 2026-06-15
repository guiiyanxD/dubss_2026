from django.db import models


class FormularioSocioeconomico(models.Model):
    class SituacionLaboral(models.TextChoices):
        EMPLEADO = "EMPLEADO", "Empleado/a"
        DESEMPLEADO = "DESEMPLEADO", "Desempleado/a"
        INDEPENDIENTE = "INDEPENDIENTE", "Trabajador/a independiente"
        NO_APLICA = "NO_APLICA", "No aplica"

    class SituacionHabitacional(models.TextChoices):
        PROPIETARIO = "PROPIETARIO", "Propietario/a"
        ALQUILANDO = "ALQUILANDO", "Alquilando"
        PRESTADA = "PRESTADA", "Vivienda prestada/cedida"
        OTRO = "OTRO", "Otro"

    usuario = models.OneToOneField(
        "acceso.Usuario",
        on_delete=models.CASCADE,
        related_name="formulario_socioeconomico",
        verbose_name="estudiante",
    )
    situacion_laboral = models.CharField(
        "situación laboral",
        max_length=20,
        choices=SituacionLaboral.choices,
    )
    ingreso_mensual_familiar = models.DecimalField(
        "ingreso mensual familiar (ARS)",
        max_digits=12,
        decimal_places=2,
    )
    cantidad_familiares = models.PositiveSmallIntegerField(
        "cantidad de miembros del grupo familiar"
    )
    situacion_habitacional = models.CharField(
        "situación habitacional",
        max_length=20,
        choices=SituacionHabitacional.choices,
    )
    tiene_beca_previa = models.BooleanField("¿posee otra beca actualmente?", default=False)
    observaciones = models.TextField("observaciones adicionales", blank=True)
    completado = models.BooleanField("completado", default=False)
    fecha_actualizacion = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "formulario socioeconómico"
        verbose_name_plural = "formularios socioeconómicos"

    def __str__(self):
        return f"Formulario de {self.usuario.get_full_name() or self.usuario.email}"
