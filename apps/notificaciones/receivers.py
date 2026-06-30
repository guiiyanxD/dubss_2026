from django.dispatch import receiver

from apps.postulaciones.signals import (
    documentacion_procesada,
    identidad_verificada,
    postulacion_enviada,
    resultado_adjudicacion,
)

from .services import NotificacionService


@receiver(postulacion_enviada)
def handler_postulacion_enviada(sender, postulacion, **kwargs):
    NotificacionService.notificar_postulacion_enviada(postulacion=postulacion)


@receiver(identidad_verificada)
def handler_identidad_verificada(sender, postulacion, aprobada, **kwargs):
    NotificacionService.notificar_identidad_verificada(postulacion=postulacion, aprobada=aprobada)


@receiver(documentacion_procesada)
def handler_documentacion_procesada(sender, postulacion, aprobada, **kwargs):
    NotificacionService.notificar_documentacion_procesada(postulacion=postulacion, aprobada=aprobada)


@receiver(resultado_adjudicacion)
def handler_resultado_adjudicacion(sender, postulacion, **kwargs):
    NotificacionService.notificar_resultado_adjudicacion(postulacion=postulacion)
