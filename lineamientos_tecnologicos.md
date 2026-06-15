# Lineamientos Tecnológicos — Sistema de Gestión de Becas Universitarias

## 1. Decisión tecnológica

Tras la evaluación de alternativas (Laravel, Django, Spring Boot, Node.js/NestJS, ASP.NET Core), se selecciona **Django** como framework principal del proyecto. Las razones que sustentan la decisión son:

- **Estabilidad entre versiones**: las releases LTS de Django ofrecen tres años de soporte garantizado y migraciones predecibles, resolviendo la principal preocupación del equipo respecto a Laravel.
- **Encaje natural con los requisitos críticos**: procesos automáticos (Celery + Celery Beat), procesamiento numérico (Pandas/NumPy) y módulo de Business Intelligence (Plotly/Matplotlib) se integran sin fricción.
- **Django Admin**: aproximadamente el 40% de los casos de uso identificados son CRUD administrativos que pueden generarse semi-automáticamente, acelerando significativamente el desarrollo.
- **Ecosistema Python para IA**: en caso de avanzar con el módulo de reportería basada en LLM local, Python ofrece el ecosistema más maduro (Hugging Face, LangChain, Ollama, PyTorch).
- **Mapeo directo con el análisis previo**: el patrón MVT de Django es semánticamente equivalente al MVC, por lo que los diagramas de comunicación y secuencia ya elaborados se mantienen válidos.

## 2. Decisiones arquitectónicas

### 2.1 Arquitectura nativa de Django (no Arquitectura Limpia)

Se adopta la arquitectura nativa que propone Django (patrón MVT) en lugar de Arquitectura Limpia. La justificación es pragmática:

- Aproximadamente el 60% de los casos de uso son CRUD simples que no requieren capas adicionales de abstracción.
- Django Admin opera directamente sobre los modelos ORM; introducir entidades puras intermedias rompería este beneficio.
- El equipo prioriza velocidad de desarrollo y baja curva de aprendizaje sobre testabilidad extrema.
- La arquitectura nativa permite aprovechar al máximo el "magic" del framework (formularios, validadores, queries expresivos).

### 2.2 Modularización por dominio

Pese a usar arquitectura Django nativa, se preservará la modularización derivada del diagrama de paquetes UML. **Cada paquete funcional se materializa como una app Django independiente**:

| Paquete UML | App Django |
|---|---|
| P1 Acceso y Seguridad | `apps.acceso` |
| P2 Administración de Usuarios | `apps.usuarios` |
| P3 Convocatorias y Catálogos | `apps.convocatorias` |
| P4 Configuración Socioeconómica | `apps.configuracion` |
| P5 Postulación y Documentación | `apps.postulaciones` |
| P6 Notificaciones | `apps.notificaciones` |
| P7 Procesamiento, Ranking y Reportes | `apps.reportes` |

Esta separación facilita el desarrollo paralelo del equipo, respeta las dependencias identificadas en la matriz de paquetes, y permite que cada app sea testeable de forma independiente.

### 2.3 Capa de servicios

Para evitar la acumulación de lógica de negocio en `views.py` o en métodos del modelo (anti-patrones conocidos como "Fat View" o "Fat Model"), se introduce una **capa explícita de servicios** en cada app:

```
apps/postulaciones/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── views.py
├── urls.py
├── services.py        ← Capa de servicios (lógica de negocio)
├── forms.py
├── tasks.py           ← Tareas Celery (procesos asíncronos)
├── selectors.py       ← Consultas complejas (opcional)
└── templates/
    └── postulaciones/
```

**Responsabilidades de cada capa:**

- **`models.py`**: definición de entidades del dominio, validaciones a nivel de campo, métodos de instancia simples (`is_active()`, `__str__()`).
- **`services.py`**: lógica de negocio que orquesta múltiples modelos o aplica reglas complejas (`registrar_postulacion()`, `procesar_formulario()`).
- **`views.py`**: recepción de requests, validación de entrada, llamada al servicio correspondiente, retorno de respuesta. **Vistas delgadas**.
- **`forms.py`**: validación estructural de datos de entrada del usuario.
- **`tasks.py`**: tareas asíncronas ejecutadas por Celery (procesamiento batch, notificaciones, cierre automático de convocatoria).
- **`selectors.py`** (opcional): consultas complejas reutilizables (separación entre escritura y lectura).

**Ejemplo de uso:**

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
from . import services

def registrar_postulacion_view(request):
    try:
        postulacion = services.registrar_postulacion(
            estudiante=request.user,
            convocatoria=Convocatoria.objects.get(id=request.POST['convocatoria_id']),
            beca=Beca.objects.get(id=request.POST['beca_id']),
        )
        return render(request, 'postulaciones/constancia.html', {'postulacion': postulacion})
    except FormularioIncompletoError:
        return redirect('configuracion:completar-formulario')
```

## 3. Stack tecnológico

### 3.1 Componentes principales

| Componente | Tecnología | Versión recomendada | Justificación |
|---|---|---|---|
| Lenguaje | Python | **3.12.x** | Estable, soportado por Django 5.2 LTS y todas las dependencias críticas. |
| Framework web | Django | **5.2.x LTS** | LTS vigente hasta abril 2028, soportada por todas las librerías del ecosistema. |
| Base de datos | PostgreSQL | **17.x** | Versión estable actual con soporte hasta noviembre 2029. Requisito mínimo para Django 5.2: PostgreSQL 14+. |
| Cliente PostgreSQL | psycopg | **3.2.x** | Soporte nativo de Django 5.2; reemplaza a psycopg2. |
| Cola de tareas | Celery | **5.6.x** | Versión actual estable; integración nativa con Django. |
| Scheduler | Celery Beat | **2.7.x** | Para tareas periódicas (cierre automático de convocatorias). |
| Broker / Caché | Redis | **7.4.x** | Backend del broker de Celery y caché de Django. |
| Servidor WSGI | Gunicorn | **23.x** | Servidor de producción Python estándar. |
| Servidor ASGI (opcional) | Uvicorn | **0.30.x** | Solo si se requieren vistas asíncronas. |
| Proxy reverso | Nginx | **1.27.x** | Servir archivos estáticos y proxy a Gunicorn. |

### 3.2 Librerías de soporte

| Categoría | Librería | Versión | Uso |
|---|---|---|---|
| Variables de entorno | python-decouple | **3.8** | Gestión de configuración via `.env`. |
| Formularios | django-crispy-forms | **2.3** | Renderizado de formularios estilizados. |
| CSS framework integration | crispy-bootstrap5 | **2024.x** | Plantillas Bootstrap 5 para crispy-forms. |
| Autenticación extendida | django-allauth | **65.x** | Autenticación robusta, autorregistro con confirmación por correo. |
| Permisos avanzados | django-guardian | **2.4.x** | Permisos a nivel de objeto si se requieren. |
| Auditoría | django-simple-history | **3.7.x** | Histórico de cambios en modelos (Postulación, Usuario). |
| Filtros de consulta | django-filter | **24.x** | Filtros en vistas de listado (Consultar Postulaciones). |
| Tablas paginadas | django-tables2 | **2.7.x** | Renderizado de tablas con ordenamiento y paginación. |
| Procesamiento numérico | Pandas | **2.2.x** | Procesamiento de formularios socioeconómicos. |
| Cálculo científico | NumPy | **2.1.x** | Dependencia de Pandas. |
| Generación de PDF | WeasyPrint | **62.x** | Generación de constancias y reportes en PDF. |
| Generación de Excel | openpyxl | **3.1.x** | Exportación de ranking a Excel. |
| Visualización (BI) | Plotly | **5.24.x** | Dashboard interactivo del Director. |
| Visualización backend (BI) | Matplotlib | **3.9.x** | Gráficos estáticos en reportes PDF. |
| Imágenes | Pillow | **11.x** | Manipulación de imágenes (digitalización). |
| Testing | pytest-django | **4.9.x** | Framework de testing recomendado. |
| Linting | ruff | **0.7.x** | Linter y formateador unificado de Python. |

### 3.3 Frontend

Se utilizará **Django Templates + Bootstrap 5 + HTMX** para mantener la simplicidad y evitar la complejidad de un SPA separado:

| Componente | Versión | Justificación |
|---|---|---|
| Bootstrap | **5.3.x** | Framework CSS maduro, ampliamente conocido por el equipo. |
| HTMX | **2.0.x** | Interactividad sin SPA; ideal para CRUD y formularios dinámicos. |
| Alpine.js (opcional) | **3.14.x** | Pequeños componentes interactivos del lado del cliente. |

### 3.4 Resumen del archivo `requirements.txt` recomendado

```
# Core
Django==5.2.*
psycopg[binary]==3.2.*
python-decouple==3.8

# Async tasks
celery==5.6.*
django-celery-beat==2.7.*
redis==5.2.*

# Forms & UI
django-crispy-forms==2.3
crispy-bootstrap5==2024.10
django-htmx==1.19.*

# Auth
django-allauth==65.*

# Audit & filters
django-simple-history==3.7.*
django-filter==24.*
django-tables2==2.7.*

# Data processing
pandas==2.2.*
numpy==2.1.*

# Reports
weasyprint==62.*
openpyxl==3.1.*
matplotlib==3.9.*
plotly==5.24.*

# Media
Pillow==11.*

# Production server
gunicorn==23.*

# Development
pytest-django==4.9.*
ruff==0.7.*
django-debug-toolbar==4.4.*
```

## 4. Entorno de desarrollo y despliegue

### 4.1 Estrategia: Docker para todo

Se adopta **Docker + Docker Compose** como única estrategia de entorno, tanto para desarrollo local como para producción. Las razones son:

- **Reproducibilidad absoluta**: el mismo contenedor que pasa los tests en local es el que se despliega.
- **Eliminación del "funciona en mi máquina"**: el equipo trabaja con versiones idénticas de Python, PostgreSQL, Redis sin instalar nada globalmente en sus máquinas.
- **Aislamiento**: ningún miembro del equipo necesita Python, PostgreSQL ni Redis instalados localmente.
- **Onboarding rápido**: un nuevo desarrollador clona el repositorio, ejecuta `docker compose up` y tiene el entorno listo en minutos.
- **Despliegue simplificado**: la imagen Docker se publica en un registry y se ejecuta igual en cualquier servidor.

**Se descartan explícitamente:**

- Python global en el dispositivo (genera conflictos entre proyectos).
- Virtual environments locales (válido para experimentos rápidos, no para un proyecto de equipo).
- Instalación nativa de PostgreSQL/Redis en cada máquina (sesgo de configuraciones inconsistentes).

### 4.2 Arquitectura de contenedores

El sistema se compone de **cinco contenedores** orquestados por Docker Compose:

```
┌─────────────────────────────────────────────────────────────┐
│                    docker-compose.yml                        │
└─────────────────────────────────────────────────────────────┘
        │
        ├─→ [web]            Aplicación Django + Gunicorn
        │
        ├─→ [worker]         Celery Worker (procesos async)
        │
        ├─→ [beat]           Celery Beat (scheduler)
        │
        ├─→ [db]             PostgreSQL 17
        │
        └─→ [redis]          Redis 7.4 (broker + caché)
```

**Responsabilidades de cada contenedor:**

| Contenedor | Imagen base | Función |
|---|---|---|
| `web` | `python:3.12-slim` | Sirve la aplicación Django con Gunicorn. |
| `worker` | `python:3.12-slim` | Ejecuta tareas asíncronas Celery (notificaciones, procesamiento). |
| `beat` | `python:3.12-slim` | Programa tareas periódicas (cierre automático de convocatoria CU11). |
| `db` | `postgres:17-alpine` | Base de datos PostgreSQL. |
| `redis` | `redis:7.4-alpine` | Broker de mensajes para Celery y caché para Django. |

Los contenedores `web`, `worker` y `beat` comparten la misma imagen construida desde el `Dockerfile` del proyecto; solo difieren en el comando de inicio.

### 4.3 Estructura de archivos sugerida

```
sistema_becas/
├── apps/
│   ├── acceso/                    # P1
│   ├── usuarios/                  # P2
│   ├── convocatorias/             # P3
│   ├── configuracion/             # P4
│   ├── postulaciones/             # P5
│   ├── notificaciones/            # P6
│   └── reportes/                  # P7
├── config/                        # Configuración Django
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py                  # Configuración Celery
├── static/                        # Archivos estáticos (CSS/JS/img)
├── media/                         # Archivos subidos por usuarios
├── templates/                     # Plantillas base globales
├── docker/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── nginx.conf                 # Solo producción
├── docker-compose.yml             # Desarrollo
├── docker-compose.prod.yml        # Producción
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

### 4.4 Variables de entorno

Las variables sensibles se gestionan mediante un archivo `.env` (nunca commiteado) y se cargan vía `python-decouple`. Variables mínimas requeridas:

```ini
# Django
DJANGO_SECRET_KEY=clave-secreta-larga-y-aleatoria
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
POSTGRES_DB=becas_db
POSTGRES_USER=becas_user
POSTGRES_PASSWORD=clave-fuerte
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis / Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Email (notificaciones CU27)
EMAIL_HOST=smtp.ejemplo.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@ejemplo.com
EMAIL_HOST_PASSWORD=clave-email
EMAIL_USE_TLS=True
```

### 4.5 Comandos básicos del entorno

```bash
# Levantar todo el stack en desarrollo
docker compose up -d

# Ver logs de la aplicación
docker compose logs -f web

# Ejecutar migraciones
docker compose exec web python manage.py migrate

# Crear superusuario
docker compose exec web python manage.py createsuperuser

# Acceder a shell de Django
docker compose exec web python manage.py shell

# Detener todo
docker compose down

# Detener y eliminar volúmenes (reset completo)
docker compose down -v
```

### 4.6 Diferencias entre desarrollo y producción

| Aspecto | Desarrollo | Producción |
|---|---|---|
| `DEBUG` | `True` | `False` |
| Servidor de aplicación | `runserver` (Django) | Gunicorn detrás de Nginx |
| Volúmenes | Código montado en hot-reload | Código embebido en imagen |
| Base de datos | Contenedor `postgres:17-alpine` | Contenedor o servicio gestionado |
| Archivos estáticos | Servidos por Django | Servidos por Nginx + WhiteNoise |
| Email | Backend de consola (`console.EmailBackend`) | SMTP real |
| Variables de entorno | Archivo `.env` local | Secretos del orquestador |

## 5. Convenciones de desarrollo

Para mantener consistencia en el equipo, se adoptan las siguientes convenciones:

- **Estilo de código**: PEP 8 aplicado mediante `ruff format` y `ruff check`.
- **Nomenclatura**: snake_case para funciones y variables; PascalCase para clases; UPPER_CASE para constantes.
- **Imports**: ordenados con `ruff` (stdlib, terceros, locales).
- **Commits**: convención Conventional Commits (`feat:`, `fix:`, `refactor:`, etc.).
- **Branching**: GitFlow simplificado (`main`, `develop`, `feature/*`).
- **Migrations**: una migración por funcionalidad; nunca editar migraciones aplicadas.
- **Testing**: cobertura mínima del 70% en `services.py` (lógica de negocio crítica).
- **Documentación**: docstrings estilo Google en funciones públicas y servicios.

## 6. Consideraciones futuras

Aunque no se aborda en esta fase, el documento contempla las siguientes extensiones potenciales:

- **Módulo de Reportería con LLM local**: pendiente de evaluación. Se considerará un contenedor adicional con Ollama si se confirma el requisito.
- **API REST**: si se requiere consumo desde una aplicación móvil, se incorporará Django REST Framework como capa adicional sobre los servicios.
- **WebSockets**: si se requieren notificaciones en tiempo real, se evaluará Django Channels.
- **Observabilidad**: se evaluará la incorporación de Sentry para tracking de errores y Prometheus + Grafana para métricas de infraestructura.

## 7. Referencias

- Django 5.2 LTS documentation: https://docs.djangoproject.com/en/5.2/
- Celery 5.6 documentation: https://docs.celeryq.dev/en/stable/
- PostgreSQL 17 documentation: https://www.postgresql.org/docs/17/
- Docker Compose specification: https://docs.docker.com/compose/
