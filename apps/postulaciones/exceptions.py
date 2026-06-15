class PostulacionActivaExistenteError(Exception):
    """El estudiante ya tiene una postulación activa."""


class ConvocatoriaNoVigenteError(Exception):
    """La convocatoria no está publicada o su período ha vencido."""


class BecaNoDisponibleError(Exception):
    """La beca no pertenece a la convocatoria seleccionada."""


class FormularioIncompletoError(Exception):
    """El formulario socioeconómico no está completo."""


class TransicionEstadoInvalidaError(Exception):
    """La transición de estado no está permitida."""


class DocumentoNoPendienteError(Exception):
    """El documento ya fue validado."""


class DocumentoNoAprobadoError(Exception):
    """El documento no fue aprobado; no se puede digitalizar."""
