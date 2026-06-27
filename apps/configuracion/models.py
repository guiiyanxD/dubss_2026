from django.db import models

# ---------------------------------------------------------------------------
# Catálogos configurables por el Director (opciones y rangos de scoring)
# ---------------------------------------------------------------------------


class OpcionDependencia(models.Model):
    """Catálogo: opciones para '¿De quién depende usted?' (sección 2a°)."""

    nombre = models.CharField("nombre", max_length=150, unique=True)
    valor_puntaje = models.PositiveSmallIntegerField("valor de puntaje", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "opción de dependencia económica"
        verbose_name_plural = "opciones de dependencia económica"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class TipoOcupacionSosten(models.Model):
    """Catálogo: ocupaciones del sostén económico (sección 2b°)."""

    nombre = models.CharField("nombre", max_length=150, unique=True)
    documento_adjuntar = models.CharField(
        "documento a adjuntar", max_length=200, blank=True,
        help_text="Documento recomendado para acreditar esta ocupación."
    )
    valor_puntaje = models.PositiveSmallIntegerField("valor de puntaje", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "tipo de ocupación del sostén"
        verbose_name_plural = "tipos de ocupación del sostén"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class RangoIngreso(models.Model):
    """Catálogo: rangos de ingreso mensual familiar (sección 2c°)."""

    nombre = models.CharField("nombre", max_length=150, unique=True)
    monto_minimo = models.DecimalField(
        "monto mínimo (Bs.)", max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Dejar vacío para indicar 'sin límite inferior'."
    )
    monto_maximo = models.DecimalField(
        "monto máximo (Bs.)", max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Dejar vacío para indicar 'sin límite superior'."
    )
    valor_puntaje = models.PositiveSmallIntegerField("valor de puntaje", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "rango de ingreso familiar"
        verbose_name_plural = "rangos de ingreso familiar"
        ordering = ["monto_minimo"]

    def __str__(self):
        return self.nombre


class RangoGrupoFamiliar(models.Model):
    """Catálogo: rangos de cantidad de integrantes del grupo familiar (sección 3°)."""

    nombre = models.CharField("nombre", max_length=150, unique=True)
    cantidad_minima = models.PositiveSmallIntegerField("cantidad mínima")
    cantidad_maxima = models.PositiveSmallIntegerField(
        "cantidad máxima", null=True, blank=True,
        help_text="Dejar vacío para indicar 'sin límite superior'."
    )
    valor_puntaje = models.PositiveSmallIntegerField("valor de puntaje", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "rango de grupo familiar"
        verbose_name_plural = "rangos de grupo familiar"
        ordering = ["cantidad_minima"]

    def __str__(self):
        return self.nombre


class TipoTenenciaVivienda(models.Model):
    """Catálogo: tipos de tenencia de la vivienda (sección 6°)."""

    nombre = models.CharField("nombre", max_length=150, unique=True)
    documento_adjuntar = models.CharField(
        "documento a adjuntar", max_length=200, blank=True,
        help_text="Documento recomendado para acreditar este tipo de tenencia."
    )
    valor_puntaje = models.PositiveSmallIntegerField("valor de puntaje", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "tipo de tenencia de vivienda"
        verbose_name_plural = "tipos de tenencia de vivienda"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class RangoInfraestructura(models.Model):
    """Catálogo: rangos de ambientes totales de la vivienda (sección 7°).

    El scoring usa la suma de dormitorios + baños + comedores + salas + patios.
    """

    nombre = models.CharField("nombre", max_length=150, unique=True)
    total_minimo = models.PositiveSmallIntegerField("total mínimo de ambientes")
    total_maximo = models.PositiveSmallIntegerField(
        "total máximo de ambientes", null=True, blank=True,
        help_text="Dejar vacío para indicar 'sin límite superior'."
    )
    valor_puntaje = models.PositiveSmallIntegerField("valor de puntaje", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "rango de infraestructura"
        verbose_name_plural = "rangos de infraestructura"
        ordering = ["total_minimo"]

    def __str__(self):
        return self.nombre


class OpcionOtroBeneficio(models.Model):
    """Catálogo: opciones para '¿Posee otro beneficio universitario?' (sección 8°)."""

    nombre = models.CharField("nombre", max_length=150, unique=True)
    valor_puntaje = models.PositiveSmallIntegerField("valor de puntaje", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "opción de otro beneficio"
        verbose_name_plural = "opciones de otro beneficio"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class OpcionDiscapacidad(models.Model):
    """Catálogo: opciones para '¿Tiene algún tipo de discapacidad?' (sección 9°)."""

    nombre = models.CharField("nombre", max_length=150, unique=True)
    valor_puntaje = models.PositiveSmallIntegerField("valor de puntaje", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "opción de discapacidad"
        verbose_name_plural = "opciones de discapacidad"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ---------------------------------------------------------------------------
# Formulario socioeconómico
# ---------------------------------------------------------------------------


class FormularioSocioeconomico(models.Model):
    class ParentescoIntegrante(models.TextChoices):
        PADRE = "PADRE", "Padre"
        MADRE = "MADRE", "Madre"
        HERMANO = "HERMANO", "Hermano"
        HERMANA = "HERMANA", "Hermana"
        HIJO = "HIJO", "Hijo/a"
        ABUELO = "ABUELO", "Abuelo/a"
        TIO = "TIO", "Tío/a"
        PRIMO = "PRIMO", "Primo/a"
        OTRO = "OTRO", "Otro"

    usuario = models.OneToOneField(
        "acceso.Usuario",
        on_delete=models.CASCADE,
        related_name="formulario_socioeconomico",
        verbose_name="estudiante",
    )

    cantidad_familiares = models.PositiveSmallIntegerField(
        "cantidad de miembros del grupo familiar"
    )
    tiene_beca_previa = models.BooleanField("¿posee otra beca actualmente?", default=False)
    observaciones = models.TextField("observaciones adicionales", blank=True)
    completado = models.BooleanField("completado", default=False)
    fecha_actualizacion = models.DateTimeField("última actualización", auto_now=True)

    # 1° Datos del postulante (complementan a Usuario/PerfilEstudiante)
    numero_celular = models.CharField("número de celular", max_length=20, blank=True)
    telefono_referencia = models.CharField("teléfono de referencia", max_length=20, blank=True)

    # 2° Dependencia económica del postulante
    dependencia_economica = models.ForeignKey(
        OpcionDependencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formularios",
        verbose_name="¿de quién depende usted?",
    )
    tipo_ocupacion_sosten = models.ForeignKey(
        TipoOcupacionSosten,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formularios",
        verbose_name="ocupación de quien lo sostiene económicamente",
    )
    rango_ingreso = models.ForeignKey(
        RangoIngreso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formularios",
        verbose_name="rango de ingreso mensual familiar",
    )

    # 3° Grupo familiar
    tiene_hijos = models.BooleanField("¿tiene hijos?", default=False)
    cantidad_hijos = models.PositiveSmallIntegerField("cantidad de hijos", null=True, blank=True)

    # 4° Procedencia
    lugar_procedencia = models.CharField(
        "lugar de procedencia",
        max_length=150,
        blank=True,
        help_text="Solo si su procedencia es otra ciudad o provincia.",
    )

    # 5° Residencia
    residencia_lugar = models.CharField("lugar de residencia", max_length=150, blank=True)
    residencia_provincia = models.CharField("provincia", max_length=100, blank=True)
    residencia_zona_anillo = models.CharField("zona o anillo", max_length=100, blank=True)
    residencia_barrio = models.CharField("barrio", max_length=100, blank=True)
    residencia_calle = models.CharField("calle", max_length=150, blank=True)

    # 6° Tenencia de vivienda
    tipo_tenencia_vivienda = models.ForeignKey(
        TipoTenenciaVivienda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formularios",
        verbose_name="tenencia de la vivienda",
    )

    # 7° Infraestructura de la vivienda
    dormitorios = models.PositiveSmallIntegerField("dormitorios", default=0)
    banos = models.PositiveSmallIntegerField("baños", default=0)
    comedores = models.PositiveSmallIntegerField("comedores", default=0)
    salas = models.PositiveSmallIntegerField("salas", default=0)
    patios = models.PositiveSmallIntegerField("patios", default=0)

    # 8° Otro beneficio dentro de la universidad
    detalle_otro_beneficio = models.CharField("¿cuál otro beneficio?", max_length=200, blank=True)

    # 9° Discapacidad
    tiene_discapacidad = models.BooleanField("¿tiene algún tipo de discapacidad?", default=False)
    detalle_discapacidad = models.CharField(
        "tipo y grado de discapacidad", max_length=200, blank=True
    )

    class Meta:
        verbose_name = "formulario socioeconómico"
        verbose_name_plural = "formularios socioeconómicos"

    def __str__(self):
        return f"Formulario de {self.usuario.get_full_name() or self.usuario.email}"


class IntegranteFamiliar(models.Model):
    """Integrante del grupo familiar del postulante (sección 3° del formulario)."""

    formulario = models.ForeignKey(
        FormularioSocioeconomico,
        on_delete=models.CASCADE,
        related_name="integrantes_familiares",
        verbose_name="formulario socioeconómico",
    )
    nombre_completo = models.CharField("nombre completo", max_length=200)
    parentesco = models.CharField(
        "parentesco",
        max_length=20,
        choices=FormularioSocioeconomico.ParentescoIntegrante.choices,
    )
    edad = models.PositiveSmallIntegerField("edad")
    ocupacion = models.CharField("ocupación", max_length=100, blank=True)
    observacion = models.CharField("observación", max_length=200, blank=True)

    class Meta:
        verbose_name = "integrante familiar"
        verbose_name_plural = "integrantes familiares"

    def __str__(self):
        return f"{self.nombre_completo} ({self.parentesco})"
