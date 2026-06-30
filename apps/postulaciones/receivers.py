from django.dispatch import receiver

from apps.convocatorias.signals import convocatoria_cerrada

from .services import PostulacionService


@receiver(convocatoria_cerrada)
def handler_convocatoria_cerrada(sender, convocatoria, **kwargs):
    """Al cerrarse una convocatoria, rechaza las postulaciones sin presentación (CU11)."""
    PostulacionService.marcar_rechazadas_por_cierre(convocatoria=convocatoria)
