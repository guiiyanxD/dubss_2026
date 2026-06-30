from celery import shared_task
from celery.utils.log import get_task_logger

from .services import ConvocatoriaService

logger = get_task_logger(__name__)


@shared_task
def tarea_cerrar_convocatorias_vencidas():
    """CU11 — Cierra convocatorias cuya fecha de cierre ya pasó."""
    count = ConvocatoriaService.cerrar_convocatorias_vencidas()
    logger.info("Convocatorias cerradas automáticamente: %d", count)
    return f"Convocatorias cerradas: {count}"
