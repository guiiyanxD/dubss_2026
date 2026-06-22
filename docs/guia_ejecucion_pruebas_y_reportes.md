# Guía de Ejecución del Proyecto, Pruebas y Reportes

Esta guía explica cómo levantar el proyecto en local, ejecutar las pruebas automatizadas, correr el análisis de vulnerabilidades con SonarQube y ubicar los reportes generados.

## 1. Requisitos Previos

Antes de iniciar, verificar que estén disponibles:

- Docker Desktop.
- Docker Compose.
- PowerShell.
- Puerto `8000` libre para Django.
- Puerto `8080` libre para pgAdmin.
- Puerto `9000` libre para SonarQube.
- Puerto `5433` libre para PostgreSQL del proyecto.

El proyecto está preparado para ejecutarse principalmente con Docker, por lo que no es necesario instalar Python, PostgreSQL o Redis directamente en el equipo.

## 2. Levantar el Proyecto en Local

Desde la raíz del proyecto ejecutar:

```powershell
docker-compose up -d --build
```

Este comando levanta los servicios principales:

| Servicio | URL / Puerto | Descripción |
|---|---|---|
| Django web | `http://localhost:8000` | Aplicación principal |
| PostgreSQL | `localhost:5433` | Base de datos del proyecto |
| Redis | `localhost:6379` | Broker de Celery |
| pgAdmin | `http://localhost:8080` | Administración visual de base de datos |
| Ollama | Interno Docker | Servicio local para IA |
| SonarQube | `http://localhost:9000` | Calidad y vulnerabilidades |

Verificar estado:

```powershell
docker-compose ps
```

Ver logs de la aplicación:

```powershell
docker-compose logs -f web
```

## 3. Accesos Locales

### Aplicación Django

```text
http://localhost:8000
```

Credenciales de prueba:

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin@becas.com` | `admin123` |
| Director | `director@becas.com` | `director123` |
| Operador | `operador@becas.com` | `operador123` |

### pgAdmin

```text
http://localhost:8080
```

Credenciales:

| Campo | Valor |
|---|---|
| Email | `admin@ficct.com` |
| Password | `adminpassword` |

Datos de conexión PostgreSQL desde una herramienta externa:

| Campo | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5433` |
| Base de datos | `dubss_2026` |
| Usuario | `dubss` |
| Password | `dubss_password` |

### SonarQube

```text
http://localhost:9000/dashboard?id=becas-universitarias
```

Credenciales locales:

| Campo | Valor |
|---|---|
| Usuario | `admin` |
| Password | `Admin12345!Dubss` |

## 4. Ejecutar Pruebas Automatizadas

Para ejecutar todas las pruebas y generar reportes visuales:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generar_reportes_pruebas.ps1
```

Este script ejecuta:

```powershell
docker-compose exec -T web coverage run -m pytest --junitxml=reports/pytest-junit.xml
docker-compose exec -T web coverage xml -o coverage.xml
docker-compose exec -T web coverage html -d reports/coverage-html
docker-compose exec -T web coverage report
```

Resultado esperado:

```text
107 passed
```

## 5. Tipos de Pruebas Incluidas

### 5.1. Pruebas Unitarias

Validan funciones específicas de la lógica de negocio.

Ubicación:

```text
apps/*/tests/test_services.py
```

Ejemplos:

| Módulo | Qué valida |
|---|---|
| `apps/acceso/tests/test_services.py` | Autorregistro de estudiantes |
| `apps/usuarios/tests/test_services.py` | Registro, roles y filtros de usuarios |
| `apps/convocatorias/tests/test_services.py` | Convocatorias, becas y documentos |
| `apps/postulaciones/tests/test_services.py` | Postulación, envío, identidad y documentos |
| `apps/reportes/tests/test_services.py` | Procesamiento, ranking, Excel, PDF e IA |

### 5.2. Pruebas de Caja Negra

Validan entradas, salidas y reglas de negocio sin considerar la implementación interna.

Ejemplos:

- Crear convocatoria con fechas válidas.
- Rechazar convocatoria con fechas inválidas.
- Crear beca con ponderación correcta.
- Rechazar beca con ponderación que no suma 100.
- Enviar una postulación en estado borrador.
- Descargar una constancia PDF.
- Exportar ranking Excel.

### 5.3. Pruebas de Caja Blanca

Validan caminos internos, ramas, condiciones, bucles y excepciones.

Funciones principales:

| Función | Archivo | Técnica aplicada |
|---|---|---|
| `autorregistrar_estudiante` | `apps/acceso/services.py` | Camino básico |
| `iniciar_postulacion` | `apps/postulaciones/services.py` | Caminos independientes |
| `validar_documento` | `apps/postulaciones/services.py` | Cobertura de decisión |
| `listar_usuarios` | `apps/usuarios/services.py` | Condiciones múltiples |
| `listar_convocatorias` | `apps/convocatorias/services.py` | Condiciones múltiples |
| `generar_ranking` | `apps/reportes/services.py` | Bucles y ramas |
| `exportar_ranking_excel` | `apps/reportes/services.py` | Bucles y salida de archivo |

### 5.4. Pruebas de Vulnerabilidad

Se ejecutan mediante SonarQube y SonarScanner.

Validan:

- Vulnerabilidades.
- Security hotspots.
- Bugs.
- Code smells.
- Cobertura.
- Complejidad.
- Resultado importado de pruebas.

## 6. Ubicación de Reportes

Los reportes se generan en la carpeta:

```text
reports/
```

| Reporte | Ruta | Descripción |
|---|---|---|
| Panel general de pruebas | `reports/index.html` | Resumen visual de tests ejecutados |
| JUnit XML | `reports/pytest-junit.xml` | Resultado de pytest en formato XML |
| Cobertura HTML | `reports/coverage-html/index.html` | Reporte navegable línea por línea |
| Resumen de cobertura | `reports/coverage-summary.txt` | Cobertura textual por archivo |
| Coverage XML | `coverage.xml` | Archivo usado por SonarQube |
| SonarQube HTML | `reports/sonarqube-summary.html` | Resumen visual exportado de SonarQube |
| Quality Gate JSON | `reports/sonarqube-quality-gate.json` | Estado del Quality Gate |
| Métricas SonarQube JSON | `reports/sonarqube-measures.json` | Cobertura, bugs, vulnerabilidades, tests |
| Vulnerabilidades JSON | `reports/sonarqube-vulnerabilities.json` | Vulnerabilidades detectadas |
| Security hotspots JSON | `reports/sonarqube-hotspots.json` | Hotspots pendientes de revisión |

## 7. Ejecutar SonarQube

Levantar y configurar SonarQube:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_sonarqube.ps1
```

Ejecutar análisis:

```powershell
docker-compose --profile quality run --rm sonar-scanner
```

Exportar reporte local:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\exportar_reporte_sonarqube.ps1
```

Dashboard:

```text
http://localhost:9000/dashboard?id=becas-universitarias
```

## 8. Resultados Actuales

Última ejecución registrada:

| Métrica | Resultado |
|---|---:|
| Tests ejecutados | 107 |
| Tests exitosos | 107 |
| Fallos | 0 |
| Errores | 0 |
| Cobertura general | 66% |
| Quality Gate SonarQube | OK |
| Vulnerabilidades | 19 |
| Security hotspots | 16 |
| Bugs | 10 |
| Code smells | 34 |

## 9. Flujo Recomendado para el Equipo

Cada vez que se modifique código relevante:

1. Levantar el proyecto:

```powershell
docker-compose up -d
```

2. Ejecutar pruebas y cobertura:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generar_reportes_pruebas.ps1
```

3. Ejecutar SonarQube:

```powershell
docker-compose --profile quality run --rm sonar-scanner
```

4. Exportar reporte de SonarQube:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\exportar_reporte_sonarqube.ps1
```

5. Revisar:

```text
reports/index.html
reports/coverage-html/index.html
reports/sonarqube-summary.html
```

6. Si todo está correcto, registrar cambios en Git.

## 10. Apagar el Entorno

Para detener los servicios:

```powershell
docker-compose down
```

Para eliminar también volúmenes de datos locales:

```powershell
docker-compose down -v
```

Usar `down -v` solo si se desea borrar la base de datos local y empezar desde cero.
