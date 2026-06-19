from celery import shared_task
from celery.utils.log import get_task_logger

from . import services

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def tarea_generar_resumen_ia(self, resumen_pk):
    """Genera el resumen narrativo de KPIs con el LLM local (cola "ia")."""
    try:
        services.generar_resumen_con_llm(resumen_pk=resumen_pk)
    except Exception as exc:
        logger.exception("Error generando resumen IA %s", resumen_pk)
        raise self.retry(exc=exc)


@shared_task
def tarea_marcar_resumenes_ia_vencidos():
    """Marca como ERROR los ResumenIA atascados en PENDIENTE/PROCESANDO (LLM no disponible)."""
    count = services.marcar_resumenes_ia_vencidos()
    logger.info("Resúmenes IA marcados como error por timeout: %d", count)
    return f"Resúmenes vencidos: {count}"


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def tarea_procesar_mensaje_chat(self, mensaje_pk):
    """Genera la respuesta del asistente para un mensaje de chat (cola "ia")."""
    try:
        services.procesar_mensaje_con_llm(mensaje_pk=mensaje_pk)
    except Exception as exc:
        logger.exception("Error procesando mensaje de chat %s", mensaje_pk)
        raise self.retry(exc=exc)


@shared_task
def tarea_marcar_chats_vencidos():
    """Responde con un mensaje de error las conversaciones sin respuesta (LLM no disponible)."""
    count = services.marcar_chats_vencidos()
    logger.info("Conversaciones marcadas como vencidas: %d", count)
    return f"Conversaciones vencidas: {count}"
