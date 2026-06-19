"""Cliente delgado sobre Ollama (LLM local). Sin lógica de negocio — solo I/O.

Lee `OLLAMA_BASE_URL`/`OLLAMA_MODEL` de settings. Quien procese esto debe ser un worker
con acceso de red al contenedor "ollama" (cola Celery "ia" — ver `CELERY_TASK_ROUTES`).
"""

import ollama
from django.conf import settings


def chat(mensajes, *, tools=None):
    """Envía una conversación al modelo local.

    Args:
        mensajes: Lista de dicts `{"role": "system"|"user"|"assistant"|"tool", "content": str}`.
        tools: Lista opcional de definiciones de tools (formato Ollama/OpenAI) para function calling.

    Returns:
        La respuesta de Ollama (incluye `message.content` y, si corresponde, `message.tool_calls`).
    """
    cliente = ollama.Client(host=settings.OLLAMA_BASE_URL)
    return cliente.chat(model=settings.OLLAMA_MODEL, messages=mensajes, tools=tools)
