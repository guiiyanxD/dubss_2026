# CAPÍTULO 6: INFRAESTRUCTURA PARA LA PRODUCCIÓN DEL SOFTWARE EN LA NUBE

## 6.1. Gestión para la Configuración del Software

La gestión de configuración del software define el conjunto de herramientas, versiones, dependencias, archivos de configuración y procedimientos necesarios para que el sistema pueda ejecutarse de forma reproducible en desarrollo, pruebas y producción. En este proyecto se adoptó una estrategia basada en Docker, variables de entorno, control de versiones con Git y despliegue en la nube mediante Render.

El objetivo principal de esta configuración es evitar diferencias entre entornos, facilitar la instalación del sistema, permitir pruebas automatizadas y preparar una infraestructura adecuada para producción.

### 6.1.1. Python Django (Backend)

El backend del sistema fue desarrollado con Python y Django, utilizando una arquitectura MVT (Model-View-Template). Django centraliza la lógica del servidor, la gestión de usuarios, el acceso a base de datos, el renderizado de vistas HTML y la administración del sistema.

Se seleccionó Django por las siguientes razones:

- Permite desarrollar aplicaciones web robustas con un patrón arquitectónico claro.
- Incluye ORM para trabajar con PostgreSQL de forma segura y estructurada.
- Facilita la implementación de autenticación, autorización y administración.
- Permite organizar el sistema en aplicaciones independientes por dominio.
- Se integra con Celery para tareas asíncronas y programadas.
- Dispone de un ecosistema maduro para reportes, generación de PDF, Excel, dashboards y procesamiento de datos.

La configuración del proyecto se encuentra separada por ambientes:

| Archivo | Uso |
|---|---|
| `config/settings/base.py` | Configuración común del proyecto |
| `config/settings/development.py` | Configuración para desarrollo local |
| `config/settings/production.py` | Configuración para producción |
| `config/urls.py` | Enrutamiento principal |
| `config/wsgi.py` | Entrada WSGI para Gunicorn |
| `config/celery.py` | Configuración de Celery |

El sistema se encuentra modularizado por aplicaciones Django:

| Aplicación | Responsabilidad |
|---|---|
| `apps.acceso` | Autenticación, registro y perfil de estudiante |
| `apps.usuarios` | Administración de usuarios y roles |
| `apps.convocatorias` | Convocatorias, becas y documentos requeridos |
| `apps.configuracion` | Formulario socioeconómico |
| `apps.postulaciones` | Postulación, revisión y documentación |
| `apps.notificaciones` | Notificaciones del flujo de postulación |
| `apps.reportes` | Ranking, dashboard, reportes e IA |

#### Dependencias principales del backend

| Dependencia | Uso |
|---|---|
| `Django==5.2.*` | Framework principal |
| `psycopg[binary]==3.2.*` | Conexión a PostgreSQL |
| `python-decouple==3.8` | Variables de entorno |
| `celery==5.6.*` | Tareas asíncronas |
| `django-celery-beat==2.9.*` | Tareas programadas |
| `redis==5.2.*` | Broker de Celery |
| `django-allauth==65.*` | Autenticación extendida |
| `django-simple-history==3.7.*` | Auditoría de cambios |
| `pandas`, `numpy` | Procesamiento de datos |
| `openpyxl` | Exportación Excel |
| `weasyprint` | Generación PDF |
| `plotly`, `matplotlib` | Gráficos y reportes |

### 6.1.2. Django Templates, Bootstrap y HTMX (Frontend)

El frontend del sistema se implementa con Django Templates, Bootstrap 5 y componentes interactivos livianos. No se utiliza un frontend SPA separado, debido a que el sistema está orientado a formularios, listados, flujos administrativos y reportes.

Esta decisión reduce la complejidad de despliegue, ya que frontend y backend se ejecutan dentro de la misma aplicación Django.

| Tecnología | Función |
|---|---|
| Django Templates | Renderizado de páginas HTML desde el backend |
| Bootstrap 5 | Estilos visuales y componentes responsivos |
| Crispy Forms | Renderizado uniforme de formularios |
| HTMX | Interacciones parciales sin recargar toda la página |
| Plotly | Visualización interactiva del dashboard |

Ventajas de esta estrategia:

- Menor cantidad de servicios a desplegar.
- Menor consumo de recursos en producción.
- Integración directa con autenticación y permisos de Django.
- Facilidad para renderizar formularios y mensajes de validación.
- Reducción de riesgos de inconsistencia entre API y frontend.

### 6.1.3. Visual Studio Code

Visual Studio Code se utiliza como entorno de desarrollo integrado para edición de código, administración de archivos, terminal integrada, ejecución de comandos Docker y revisión de documentación.

Extensiones recomendadas:

| Extensión | Uso |
|---|---|
| Python | Soporte para desarrollo Python |
| Django | Resaltado y soporte para plantillas Django |
| Docker | Gestión visual de contenedores |
| GitLens | Revisión de historial Git |
| YAML | Edición de `docker-compose.yml` y `render.yaml` |
| Markdown All in One | Edición de documentación |
| PlantUML | Visualización de diagramas `.puml` |

VS Code permite centralizar el flujo de trabajo del equipo:

- Edición de código fuente.
- Ejecución de terminales PowerShell.
- Control de versiones con Git.
- Revisión de archivos de configuración.
- Visualización de documentación Markdown.
- Apertura de reportes HTML generados por pruebas.

### 6.1.4. Docker y Docker Compose

Docker se utiliza para encapsular la aplicación y sus dependencias en contenedores. Docker Compose permite orquestar múltiples servicios necesarios para el funcionamiento completo del sistema.

El archivo principal es:

```text
docker-compose.yml
```

Servicios definidos:

| Servicio | Imagen / origen | Función |
|---|---|---|
| `web` | Imagen construida desde `docker/Dockerfile` | Aplicación Django en desarrollo |
| `init` | Imagen del proyecto | Ejecución inicial de migraciones |
| `db` | `postgres:17-alpine` | Base de datos local |
| `redis` | `redis:7.4-alpine` | Broker de Celery |
| `pgadmin` | `dpage/pgadmin4` | Administración visual de base de datos |
| `ollama` | `ollama/ollama` | Modelo local para funciones IA |
| `worker` | Imagen del proyecto | Worker Celery |
| `beat` | Imagen del proyecto | Programador Celery Beat |
| `sonarqube` | `sonarqube:community` | Análisis de calidad y vulnerabilidades |
| `sonar-scanner` | `sonarsource/sonar-scanner-cli` | Envío de análisis a SonarQube |

El Dockerfile del proyecto utiliza `python:3.12-slim` como imagen base e instala dependencias del sistema necesarias para generación de PDF, gráficos e imágenes.

Comandos principales:

```powershell
docker-compose up -d
docker-compose ps
docker-compose logs -f web
docker-compose exec -T web python manage.py migrate
docker-compose exec -T web pytest
docker-compose down
```

## 6.2. Herramientas para el Control de Versiones

El control de versiones es un componente fundamental para el trabajo colaborativo, trazabilidad de cambios, recuperación de versiones y despliegue controlado. En este proyecto se emplean Git y GitHub como herramientas principales.

### 6.2.1. Git

Git es el sistema de control de versiones distribuido utilizado para registrar cambios sobre el código fuente, documentación, configuraciones y pruebas.

Funciones aplicadas:

- Registro histórico de cambios.
- Creación de ramas de trabajo.
- Comparación de modificaciones.
- Restauración de versiones anteriores.
- Trazabilidad de funcionalidades implementadas.
- Integración con GitHub y herramientas de revisión.

Comandos utilizados con mayor frecuencia:

```powershell
git status
git add .
git commit -m "mensaje"
git branch
git checkout -b feature/nombre
git diff
git log --oneline
```

Archivos relevantes para control de versiones:

| Archivo | Propósito |
|---|---|
| `.gitignore` | Excluir archivos generados, entornos y secretos |
| `.gitattributes` | Normalización de archivos del repositorio |
| `sonar-project.properties` | Configuración de análisis estático |
| `requirements.txt` | Dependencias del proyecto |
| `docker-compose.yml` | Orquestación local |
| `render.yaml` | Infraestructura cloud declarativa |

### 6.2.2. GitHub

GitHub se utiliza como repositorio remoto del proyecto y como punto central de colaboración del equipo.

Usos principales:

- Almacenamiento remoto del código fuente.
- Colaboración entre integrantes del equipo.
- Revisión de cambios mediante pull requests.
- Historial de commits.
- Gestión de ramas.
- Integración con herramientas externas de calidad y despliegue.

Flujo recomendado:

1. Crear una rama por funcionalidad:

```powershell
git checkout -b feature/nombre-funcionalidad
```

2. Implementar cambios y ejecutar pruebas:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generar_reportes_pruebas.ps1
```

3. Validar calidad con SonarQube:

```powershell
docker-compose --profile quality run --rm sonar-scanner
```

4. Confirmar cambios:

```powershell
git add .
git commit -m "feat: descripcion del cambio"
```

5. Subir rama:

```powershell
git push origin feature/nombre-funcionalidad
```

6. Crear pull request en GitHub.

### 6.2.3. Estrategia de Ramas

Se recomienda aplicar una estrategia de ramas simple:

| Rama | Uso |
|---|---|
| `main` | Versión estable o lista para producción |
| `develop` | Integración de avances del equipo |
| `feature/*` | Nuevas funcionalidades |
| `fix/*` | Corrección de errores |
| `docs/*` | Cambios de documentación |

Antes de integrar cambios a `main` o `develop`, se debe comprobar:

- La suite de pruebas pasa correctamente.
- La cobertura se genera sin errores.
- SonarQube ejecuta el análisis.
- No existen secretos comprometidos.
- La documentación asociada está actualizada.

## 6.3. Infraestructura de la Nube

La infraestructura de nube se define de forma declarativa para facilitar el despliegue del sistema, mantener trazabilidad y permitir reproducibilidad. En este proyecto se utiliza Render como plataforma cloud principal, definida mediante el archivo:

```text
render.yaml
```

### 6.3.1. Plataforma Cloud Render

Render se utiliza como plataforma de despliegue para la aplicación web, base de datos PostgreSQL, Redis y procesos worker.

Recursos definidos:

| Recurso | Nombre | Tipo | Propósito |
|---|---|---|---|
| Base de datos | `becas-db` | PostgreSQL 17 | Persistencia del sistema |
| Key Value | `becas-redis` | Redis compatible | Broker y backend de Celery |
| Web Service | `becas-web` | Docker Web | Aplicación Django + Gunicorn |
| Worker | `becas-worker` | Docker Worker | Tareas Celery y Celery Beat |

La aplicación web se despliega desde Docker usando:

```text
docker/Dockerfile
```

Comando de producción:

```bash
python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

El worker ejecuta:

```bash
celery -A config.celery worker -B -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 6.3.2. Base de Datos PostgreSQL

PostgreSQL es el motor de base de datos principal del sistema. En producción se configura como servicio gestionado de Render y en desarrollo se ejecuta como contenedor local.

Configuración en producción:

| Variable | Origen |
|---|---|
| `POSTGRES_DB` | Base de datos gestionada |
| `POSTGRES_USER` | Usuario gestionado |
| `POSTGRES_PASSWORD` | Secreto generado por Render |
| `POSTGRES_HOST` | Host interno de Render |
| `POSTGRES_PORT` | Puerto PostgreSQL |

Ventajas:

- Integración nativa con Django ORM.
- Soporte para transacciones.
- Integridad referencial.
- Consultas relacionales complejas.
- Separación entre ambiente local y producción.

En desarrollo local el puerto externo se configuró en `5433` para evitar conflicto con otros contenedores PostgreSQL del equipo:

```yaml
ports:
  - "5433:5432"
```

### 6.3.3. Redis y Procesamiento Asíncrono

Redis se utiliza como broker y backend de resultados para Celery. Permite desacoplar procesos que no deben bloquear la experiencia del usuario.

Procesos asociados:

- Envío de notificaciones.
- Cierre automático de convocatorias.
- Procesamiento de mensajes del chat IA.
- Generación de resúmenes IA.
- Tareas programadas por Celery Beat.

Variables relevantes:

| Variable | Uso |
|---|---|
| `CELERY_BROKER_URL` | Conexión al broker Redis |
| `CELERY_RESULT_BACKEND` | Backend de resultados |
| `REDIS_URL` | Conexión general al servicio Redis |

En producción el archivo `render.yaml` usa un servicio `keyvalue` como fuente de conexión Redis.

### 6.3.4. Servicio Web con Gunicorn

En producción Django no se ejecuta con `runserver`, sino con Gunicorn, que actúa como servidor WSGI.

Comando de producción:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Responsabilidades:

- Atender peticiones HTTP.
- Ejecutar la aplicación Django.
- Gestionar concurrencia básica.
- Integrarse con el puerto dinámico provisto por Render.

Configuración de seguridad para producción:

| Variable | Valor esperado |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |

### 6.3.5. Worker de Celery en Producción

El worker ejecuta tareas asíncronas fuera del proceso web. En Render se define como servicio independiente de tipo `worker`.

Por economía de recursos, el proyecto combina worker y beat en el mismo proceso:

```bash
celery -A config.celery worker -B -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Esta decisión es válida mientras exista una sola instancia del worker. Si en el futuro se escalan múltiples réplicas, Celery Beat deberá separarse en un servicio único para evitar ejecución duplicada de tareas programadas.

### 6.3.6. Archivos Estáticos y Media

Los archivos estáticos corresponden a CSS, JavaScript, imágenes y recursos visuales de la interfaz. Los archivos media corresponden a documentos subidos o generados por usuarios.

Configuración base:

| Variable | Uso |
|---|---|
| `STATIC_URL` | Ruta pública de archivos estáticos |
| `STATIC_ROOT` | Directorio de recolección de estáticos |
| `MEDIA_URL` | Ruta pública para media |
| `MEDIA_ROOT` | Directorio de archivos subidos |

En desarrollo, Django puede servir estos archivos directamente. En producción se recomienda:

- Ejecutar `collectstatic`.
- Usar almacenamiento persistente o servicio externo para media.
- Servir estáticos con infraestructura optimizada.
- Evitar almacenar archivos críticos en contenedores efímeros.

### 6.3.7. Seguridad y Variables de Entorno

La seguridad de configuración se basa en variables de entorno y separación entre archivos versionados y secretos.

Buenas prácticas aplicadas:

- `.env` no se versiona.
- `.env.worker` no se versiona.
- `.env.example` sirve como plantilla.
- Render genera `DJANGO_SECRET_KEY`.
- Las credenciales de PostgreSQL se obtienen del servicio gestionado.
- Las credenciales SMTP no se sincronizan en el repositorio.
- `DJANGO_DEBUG=False` en producción.

Variables críticas:

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta de Django |
| `POSTGRES_PASSWORD` | Contraseña de base de datos |
| `EMAIL_HOST_PASSWORD` | Contraseña SMTP |
| `SONAR_TOKEN` | Token local para SonarScanner |
| `CELERY_BROKER_URL` | Conexión Redis |

## 6.4. Herramientas de Calidad y Análisis Estático

La infraestructura del proyecto no se limita a ejecutar la aplicación. También incluye herramientas para asegurar calidad, seguridad y trazabilidad de pruebas.

### 6.4.1. SonarQube

SonarQube se integró al proyecto como servicio permanente de Docker Compose. Permite analizar:

- Vulnerabilidades.
- Security hotspots.
- Bugs.
- Code smells.
- Cobertura.
- Complejidad.
- Resultado de pruebas.

URL local:

```text
http://localhost:9000/dashboard?id=becas-universitarias
```

Comando de análisis:

```powershell
docker-compose --profile quality run --rm sonar-scanner
```

Resultados registrados:

| Métrica | Valor |
|---|---:|
| Quality Gate | OK |
| Tests importados | 107 |
| Éxito de tests | 100% |
| Cobertura | 66.0% |
| Vulnerabilidades | 19 |
| Security hotspots | 16 |
| Bugs | 10 |
| Code smells | 34 |

### 6.4.2. Coverage y Pytest

Pytest se usa para ejecutar pruebas automatizadas. Coverage mide el porcentaje de código cubierto por las pruebas.

Comando:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generar_reportes_pruebas.ps1
```

Artefactos generados:

| Archivo | Propósito |
|---|---|
| `reports/index.html` | Resumen visual de pruebas |
| `reports/pytest-junit.xml` | Reporte compatible con herramientas CI |
| `reports/coverage-html/index.html` | Cobertura navegable |
| `coverage.xml` | Cobertura para SonarQube |
| `reports/coverage-summary.txt` | Resumen textual de cobertura |

### 6.4.3. Ruff

Ruff se utiliza como herramienta de linting y análisis de complejidad ciclomática.

Comando para identificar funciones complejas:

```powershell
docker-compose exec -T web ruff check --select C901 --config lint.mccabe.max-complexity=3 apps
```

Su uso permite detectar funciones que requieren mayor atención en pruebas de caja blanca y refactorización.

## 6.5. Flujo de Despliegue Propuesto

El flujo de despliegue recomendado integra control de versiones, pruebas, análisis estático y despliegue en la nube.

### 6.5.1. Flujo Local

1. Clonar repositorio.
2. Crear `.env` a partir de `.env.example`.
3. Levantar servicios:

```powershell
docker-compose up -d
```

4. Ejecutar pruebas:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generar_reportes_pruebas.ps1
```

5. Ejecutar SonarQube:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_sonarqube.ps1
docker-compose --profile quality run --rm sonar-scanner
```

6. Revisar dashboard y reportes.
7. Confirmar cambios en Git.

### 6.5.2. Flujo hacia Producción

1. Integrar cambios en rama estable.
2. Verificar que las pruebas pasen.
3. Revisar vulnerabilidades y Quality Gate.
4. Actualizar variables de entorno en Render.
5. Desplegar imagen Docker.
6. Ejecutar migraciones.
7. Validar aplicación en URL productiva.

### 6.5.3. Criterios de Aceptación para Despliegue

| Criterio | Estado esperado |
|---|---|
| Pruebas automatizadas | Sin fallos |
| Migraciones | Aplicadas correctamente |
| `DJANGO_DEBUG` | `False` |
| Variables secretas | Configuradas fuera del repositorio |
| SonarQube | Quality Gate revisado |
| Base de datos | Servicio gestionado activo |
| Redis | Servicio activo |
| Worker | En ejecución |
| Logs | Sin errores críticos |

## 6.6. Resumen del Capítulo

La infraestructura de producción del sistema se apoya en una arquitectura contenerizada con Docker, backend Django, PostgreSQL, Redis, Celery, Gunicorn y despliegue declarativo en Render. El control de versiones se gestiona con Git y GitHub, mientras que la calidad se valida mediante pytest, coverage, Ruff y SonarQube.

Esta configuración permite reproducir el sistema en desarrollo y producción, ejecutar pruebas automatizadas, revisar vulnerabilidades y mantener trazabilidad sobre los cambios realizados. Además, el uso de `render.yaml` facilita el despliegue en la nube y la administración de servicios asociados como base de datos, Redis, web service y worker.
