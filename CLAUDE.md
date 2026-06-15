# CLAUDE.md — Sistema de Gestión de Becas Universitarias

## Proyecto

Sistema web para gestión de convocatorias de becas universitarias. Cubre el flujo completo: autorregistro de estudiantes, postulación con validación presencial, procesamiento socioeconómico automático, generación de ranking y reportería.

**Actores:** Director (total), Operador (alto), Estudiante (básico), Sistema (temporizador).

## Stack tecnológico

| Componente | Versión |
|---|---|
| Python | 3.12 |
| Django | 5.2 LTS |
| PostgreSQL | 17 |
| psycopg | 3.2 (binary) |
| Celery | 5.6 |
| django-celery-beat | 2.7 |
| Redis | 7.4 |
| Gunicorn | 23 |
| Bootstrap | 5.3 |
| HTMX | 2.0 |

**Librerías clave:** `django-allauth`, `django-crispy-forms` + `crispy-bootstrap5`, `django-filter`, `django-tables2`, `django-simple-history`, `pandas`, `numpy`, `weasyprint`, `openpyxl`, `plotly`, `matplotlib`, `Pillow`, `python-decouple`.

**Dev/test:** `pytest-django`, `ruff`, `django-debug-toolbar`.

## Arquitectura

- **Patrón:** Django nativo (MVT). **No se usa Arquitectura Limpia.**
- **Modularización:** una app Django por cada paquete funcional (P1–P7).
- **Capa de servicios obligatoria** en cada app para la lógica de negocio.
- **Vistas delgadas, modelos delgados, servicios gruesos.**

### Apps del proyecto

```
apps/acceso/         → P1 Acceso y Seguridad (CU01, CU02, CU03)
apps/usuarios/       → P2 Admin Usuarios (CU04-CU08)
apps/convocatorias/  → P3 Convocatorias y Catálogos (CU09-CU14)
apps/configuracion/  → P4 Config Socioeconómica (CU15)
apps/postulaciones/  → P5 Postulación y Documentación (CU16-CU22)
apps/notificaciones/ → P6 Notificaciones (CU27)
apps/reportes/       → P7 Procesamiento, Ranking y Reportes (CU23-CU26)
```

### Dependencias entre apps

```
acceso          → (ninguna, capa base)
usuarios        → acceso
convocatorias   → acceso
configuracion   → usuarios
postulaciones   → acceso, convocatorias, configuracion
notificaciones  → usuarios, postulaciones
reportes        → usuarios, convocatorias, configuracion, postulaciones
```

**Regla:** una app NO puede importar de otra app que esté arriba en esta jerarquía.

### Estructura interna de cada app

```
apps/<nombre>/
├── apps.py
├── admin.py          # Configuración Django Admin
├── models.py         # Entidades del dominio (delgadas)
├── views.py          # Vistas delgadas: validan entrada, llaman a services, retornan respuesta
├── urls.py
├── forms.py          # Validación estructural de entrada
├── services.py       # LÓGICA DE NEGOCIO (orquesta modelos, aplica reglas)
├── tasks.py          # Tareas Celery asíncronas
├── selectors.py      # Consultas complejas reutilizables (opcional)
├── exceptions.py     # Excepciones de dominio
└── templates/<nombre>/
```

## Reglas de capas (CRÍTICO)

### `models.py`
- Solo definición de campos, relaciones, validaciones a nivel de campo y métodos triviales (`__str__`, `is_active()`).
- **NO** poner lógica de negocio compleja aquí.

### `views.py`
- Reciben request → validan con `forms.py` → llaman a `services.py` → retornan response.
- **NO** acceder a `Model.objects` directamente para mutaciones complejas.
- **NO** orquestar varios modelos.
- Vistas máximo ~20 líneas.

### `services.py`
- Toda la lógica de negocio vive aquí.
- Funciones puras siempre que sea posible.
- Usar `@transaction.atomic` cuando se modifican múltiples modelos.
- Lanzar excepciones de dominio definidas en `exceptions.py`.

### `tasks.py`
- Solo tareas Celery (`@shared_task`).
- Las tareas llaman a `services.py`, no duplican lógica.

### Ejemplo correcto

```python
# apps/postulaciones/services.py
from django.db import transaction
from .models import Postulacion
from .exceptions import FormularioIncompletoError

@transaction.atomic
def registrar_postulacion(estudiante, convocatoria, beca):
    formulario = estudiante.formulario_socioeconomico
    if not formulario.esta_completo():
        raise FormularioIncompletoError()
    return Postulacion.objects.create(
        estudiante=estudiante,
        convocatoria=convocatoria,
        beca=beca,
        formulario=formulario,
        estado='ENVIADA',
    )
```

```python
# apps/postulaciones/views.py
from django.shortcuts import render, redirect
from . import services
from .exceptions import FormularioIncompletoError

def registrar_postulacion_view(request):
    try:
        postulacion = services.registrar_postulacion(
            estudiante=request.user,
            convocatoria=request.POST['convocatoria_id'],
            beca=request.POST['beca_id'],
        )
        return render(request, 'postulaciones/constancia.html', {'postulacion': postulacion})
    except FormularioIncompletoError:
        return redirect('configuracion:completar-formulario')
```

## Entorno

**Docker es la única forma de correr el proyecto.** No usar Python global, no usar virtualenv local.

### Contenedores

| Contenedor | Imagen | Rol |
|---|---|---|
| `web` | `python:3.12-slim` | Django + Gunicorn |
| `worker` | `python:3.12-slim` | Celery Worker |
| `beat` | `python:3.12-slim` | Celery Beat (scheduler) |
| `db` | `postgres:17-alpine` | Base de datos |
| `redis` | `redis:7.4-alpine` | Broker + caché |

### Comandos frecuentes

```bash
docker compose up -d                                    # Levantar stack
docker compose logs -f web                              # Ver logs
docker compose exec web python manage.py migrate        # Migraciones
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
docker compose exec web pytest                          # Tests
docker compose exec web ruff check .                    # Linter
docker compose exec web ruff format .                   # Formatear
docker compose down                                     # Detener
docker compose down -v                                  # Reset total
```

## Reglas de negocio críticas

- Un estudiante solo puede tener **una postulación activa** a la vez (estados: Borrador, Enviada, En Revisión, Aprobada).
- Si una postulación es **rechazada** y la convocatoria sigue vigente, el estudiante puede re-postular.
- El **formulario socioeconómico es único por estudiante** y reutilizable entre postulaciones.
- El **cierre de convocatoria es automático** (Celery Beat detecta vencimiento) — CU11.
- La validación documental es **binaria** (Aprobada/Rechazada), no existe "Observada".
- Solo se **digitaliza documentación aprobada** (optimización de almacenamiento).
- Pueden coexistir **múltiples convocatorias activas** simultáneamente.

## Estados de la Postulación

```
[Borrador] → [Enviada] → [En Revisión] → [Aprobada] → [Procesada] →
    → [Adjudicada | No Adjudicada | Lista de Espera]

Estados de rechazo terminales:
- Rechazada - No Presentación   (desde Enviada al vencer convocatoria)
- Rechazada - Identidad         (desde En Revisión)
- Rechazada - Documentación     (desde En Revisión)
```

## Convenciones de código

- **PEP 8** vía `ruff` (linter + formateador).
- **snake_case** para funciones/variables, **PascalCase** para clases, **UPPER_CASE** para constantes.
- **Imports** ordenados por `ruff` (stdlib → terceros → locales).
- **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`).
- **Branching:** `main`, `develop`, `feature/<nombre>`.
- **Docstrings** estilo Google en funciones públicas y todos los servicios.
- **Tests:** cobertura mínima 70% en `services.py`.
- Una **migración por funcionalidad**, nunca editar migraciones ya aplicadas.

## Configuración

- Settings divididos en `config/settings/{base,development,production}.py`.
- Variables sensibles en `.env` (nunca commitear) cargadas con `python-decouple`.
- `DJANGO_SETTINGS_MODULE` se define en `docker-compose.yml` por servicio.

## Variables de entorno requeridas

```
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_HOST / POSTGRES_PORT
REDIS_URL
CELERY_BROKER_URL / CELERY_RESULT_BACKEND
EMAIL_HOST / EMAIL_PORT / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD / EMAIL_USE_TLS
```

## CU críticos a respetar

Estos 8 CU tienen análisis profundo (diagramas de comunicación + secuencia). Cualquier cambio debe respetar el flujo modelado:

- **CU01** Autenticarse (patrón base)
- **CU11** Cerrar Convocatoria (disparado por Celery Beat)
- **CU17** Registrar Postulación
- **CU18** Verificar Identidad del Postulante
- **CU19** Validar Documentación Física (incluye CU20 y CU27)
- **CU20** Digitalizar Documentación
- **CU23** Procesar Formularios Socioeconómicos (usa Pandas)
- **CU24** Generar Ranking

## Lo que NO se debe hacer

- ❌ Poner lógica de negocio en `models.py` o `views.py`.
- ❌ Importar entre apps violando la jerarquía de dependencias.
- ❌ Instalar Python o dependencias localmente fuera de Docker.
- ❌ Hacer commits con migraciones manualmente editadas.
- ❌ Acceder al ORM directamente desde `views.py` para mutaciones complejas.
- ❌ Crear SPA o frontend separado: el proyecto usa Django Templates + HTMX.
- ❌ Aplicar Arquitectura Limpia, repositorios o entidades puras.
- ❌ Agregar dependencias sin actualizar `requirements.txt`.
