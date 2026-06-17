from django.db import transaction

from .models import FormularioSocioeconomico, IntegranteFamiliar


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
    numero_celular="",
    telefono_referencia="",
    dependencia_economica="",
    tipo_ocupacion_sosten="",
    tiene_hijos=False,
    cantidad_hijos=None,
    lugar_procedencia="",
    residencia_lugar="",
    residencia_provincia="",
    residencia_zona_anillo="",
    residencia_barrio="",
    residencia_calle="",
    tipo_tenencia_vivienda="",
    dormitorios=0,
    banos=0,
    comedores=0,
    salas=0,
    patios=0,
    detalle_otro_beneficio="",
    tiene_discapacidad=False,
    detalle_discapacidad="",
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
        numero_celular, telefono_referencia: Contacto del postulante.
        dependencia_economica: Valor de DependenciaEconomica choices.
        tipo_ocupacion_sosten: Valor de TipoOcupacionSosten choices.
        tiene_hijos, cantidad_hijos: Datos del grupo familiar del postulante.
        lugar_procedencia: Ciudad/provincia de origen, si difiere de la residencia actual.
        residencia_lugar, residencia_provincia, residencia_zona_anillo, residencia_barrio,
            residencia_calle: Dirección de residencia actual.
        tipo_tenencia_vivienda: Valor de TipoTenenciaVivienda choices.
        dormitorios, banos, comedores, salas, patios: Infraestructura de la vivienda.
        detalle_otro_beneficio: Detalle de otro beneficio universitario, si aplica.
        tiene_discapacidad, detalle_discapacidad: Datos de discapacidad, si aplica.

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
            "numero_celular": numero_celular,
            "telefono_referencia": telefono_referencia,
            "dependencia_economica": dependencia_economica,
            "tipo_ocupacion_sosten": tipo_ocupacion_sosten,
            "tiene_hijos": tiene_hijos,
            "cantidad_hijos": cantidad_hijos,
            "lugar_procedencia": lugar_procedencia,
            "residencia_lugar": residencia_lugar,
            "residencia_provincia": residencia_provincia,
            "residencia_zona_anillo": residencia_zona_anillo,
            "residencia_barrio": residencia_barrio,
            "residencia_calle": residencia_calle,
            "tipo_tenencia_vivienda": tipo_tenencia_vivienda,
            "dormitorios": dormitorios,
            "banos": banos,
            "comedores": comedores,
            "salas": salas,
            "patios": patios,
            "detalle_otro_beneficio": detalle_otro_beneficio,
            "tiene_discapacidad": tiene_discapacidad,
            "detalle_discapacidad": detalle_discapacidad,
            "completado": True,
        },
    )
    return formulario


@transaction.atomic
def guardar_integrantes_familiares(*, formulario, integrantes):
    """Reemplaza la lista de integrantes familiares del formulario (sección 3°).

    Args:
        formulario: Instancia de FormularioSocioeconomico.
        integrantes: Lista de dicts con nombre_completo, parentesco, edad,
            ocupacion y observacion.

    Returns:
        Lista de instancias de IntegranteFamiliar creadas.
    """
    formulario.integrantes_familiares.all().delete()
    nuevos = [IntegranteFamiliar(formulario=formulario, **datos) for datos in integrantes]
    return IntegranteFamiliar.objects.bulk_create(nuevos)
