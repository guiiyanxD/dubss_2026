class ConvocatoriaNoModificableError(Exception):
    """La convocatoria no está en estado Borrador y no puede editarse."""


class FechaInvalidaError(Exception):
    """La fecha de cierre no es posterior a la fecha de apertura."""


class ConvocatoriaYaCerradaError(Exception):
    """La convocatoria ya se encuentra en estado Cerrada."""


class NombreDuplicadoError(Exception):
    """Ya existe un registro con ese nombre."""
