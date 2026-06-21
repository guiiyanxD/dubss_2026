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

    class DependenciaEconomica(models.TextChoices):
        INDEPENDIENTE = "INDEPENDIENTE", "Independiente"
        PADRE_MADRE = "PADRE_MADRE", "Solo de padre o madre"
        OTRO_FAMILIAR = "OTRO_FAMILIAR", "Otro familiar"
        PAREJA = "PAREJA", "De la pareja"
        AMBOS_PADRES = "AMBOS_PADRES", "Ambos padres"

    class TipoOcupacionSosten(models.TextChoices):
        ASALARIADO_FORMAL = "ASALARIADO_FORMAL", "Asalariado formal"
        ASALARIADO_INFORMAL = "ASALARIADO_INFORMAL", "Asalariado informal"
        COMERCIANTE_MAYORISTA = "COMERCIANTE_MAYORISTA", "Comerciante mayorista"
        RENTISTA = "RENTISTA", "Rentista"
        COMERCIANTE_MINORISTA = "COMERCIANTE_MINORISTA", "Comerciante minorista"
        AGRICULTOR = "AGRICULTOR", "Agricultor"

    class TipoTenenciaVivienda(models.TextChoices):
        HERENCIA = "HERENCIA", "Herencia"
        DE_LOS_PADRES = "DE_LOS_PADRES", "De los padres"
        CEDIDA = "CEDIDA", "Cedida"
        ANTICRETICO = "ANTICRETICO", "Anticrético"
        ALQUILER = "ALQUILER", "Alquiler"

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

    # 1° Datos del postulante (complementan a Usuario/PerfilEstudiante)
    numero_celular = models.CharField("número de celular", max_length=20, blank=True)
    telefono_referencia = models.CharField("teléfono de referencia", max_length=20, blank=True)

    # 2° Dependencia económica del postulante
    dependencia_economica = models.CharField(
        "¿de quién depende usted?",
        max_length=20,
        choices=DependenciaEconomica.choices,
        blank=True,
    )
    tipo_ocupacion_sosten = models.CharField(
        "ocupación de quien lo sostiene económicamente",
        max_length=25,
        choices=TipoOcupacionSosten.choices,
        blank=True,
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
    tipo_tenencia_vivienda = models.CharField(
        "tenencia de la vivienda",
        max_length=20,
        choices=TipoTenenciaVivienda.choices,
        blank=True,
    )

    # 7° Infraestructura de la vivienda
    dormitorios = models.PositiveSmallIntegerField("dormitorios", default=0)
    banos = models.PositiveSmallIntegerField("baños", default=0)
    comedores = models.PositiveSmallIntegerField("comedores", default=0)
    salas = models.PositiveSmallIntegerField("salas", default=0)
    patios = models.PositiveSmallIntegerField("patios", default=0)

    # 8° Otro beneficio dentro de la universidad (complementa tiene_beca_previa)
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
