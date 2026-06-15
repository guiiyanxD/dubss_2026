from django.db import transaction

from .models import FormularioSocioeconomico


@transaction.atomic
def guardar_formulario(
    *,
    estudiante,
    situacion_laboral,
    ingreso_mensual_familiar,
    cantidad_familiares,
    situacion_habitacional,
    tiene_beca_previa,
    observaciones="",
):
    """Crea o actualiza el formulario socioeconómico del estudiante y lo marca como completado.

    Args:
        estudiante: Instancia de Usuario (rol Estudiante).
        situacion_laboral: Valor de SituacionLaboral choices.
        ingreso_mensual_familiar: Decimal con el ingreso mensual del grupo familiar.
        cantidad_familiares: Número de integrantes del grupo familiar.
        situacion_habitacional: Valor de SituacionHabitacional choices.
        tiene_beca_previa: Bool indicando si ya posee otra beca.
        observaciones: Texto opcional.

    Returns:
        La instancia de FormularioSocioeconomico creada o actualizada.
    """
    formulario, _ = FormularioSocioeconomico.objects.update_or_create(
        usuario=estudiante,
        defaults={
            "situacion_laboral": situacion_laboral,
            "ingreso_mensual_familiar": ingreso_mensual_familiar,
            "cantidad_familiares": cantidad_familiares,
            "situacion_habitacional": situacion_habitacional,
            "tiene_beca_previa": tiene_beca_previa,
            "observaciones": observaciones,
            "completado": True,
        },
    )
    return formulario
