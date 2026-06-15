from django.dispatch import receiver

from apps.convocatorias.signals import convocatoria_cerrada

from . import services


@receiver(convocatoria_cerrada)
def handler_convocatoria_cerrada(sender, convocatoria, **kwargs):
    """Al cerrarse una convocatoria, rechaza las postulaciones sin presentación (CU11)."""
    services.marcar_rechazadas_por_cierre(convocatoria=convocatoria)
