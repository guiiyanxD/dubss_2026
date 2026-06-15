from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def tarea_enviar_email(self, notificacion_pk):
    """Envía el email de una Notificacion y actualiza su estado."""
    from .models import Notificacion

    try:
        notif = Notificacion.objects.get(pk=notificacion_pk)
    except Notificacion.DoesNotExist:
        return

    try:
        send_mail(
            subject=notif.asunto,
            message=notif.cuerpo,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "becas@universidad.edu"),
            recipient_list=[notif.usuario.email],
            fail_silently=False,
        )
        notif.estado = Notificacion.Estado.ENVIADA
        notif.fecha_envio = timezone.now()
        notif.save(update_fields=["estado", "fecha_envio"])
    except Exception as exc:
        notif.estado = Notificacion.Estado.ERROR
        notif.error_detalle = str(exc)
        notif.save(update_fields=["estado", "error_detalle"])
        raise self.retry(exc=exc)
