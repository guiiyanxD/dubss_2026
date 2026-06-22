# Reporte de pruebas por complejidad ciclomática, PUDS y caja blanca

Fecha de ejecución: 2026-06-22

Proyecto: Sistema de Gestión de Becas Universitarias

## 1. Alcance

Este reporte toma como base `docs/complejidad-ciclomatico.md` y cubre las funciones de negocio con complejidad ciclomática estrictamente mayor a 3. Se priorizaron funciones en `services.py`, porque concentran reglas de negocio y corresponden al criterio del documento original.

Funciones cubiertas:

| Complejidad | Función | Archivo | Proceso / CU |
|---:|---|---|---|
| 6 | `iniciar_postulacion` | `apps/postulaciones/services.py` | CU16 - Iniciar postulación |
| 6 | `validar_documento` | `apps/postulaciones/services.py` | CU19 - Validar documentación física |
| 6 | `listar_usuarios` | `apps/usuarios/services.py` | Gestión y filtrado de usuarios |
| 5 | `generar_ranking` | `apps/reportes/services.py` | CU24 - Generar ranking |
| 4 | `exportar_ranking_excel` | `apps/reportes/services.py` | CU25 - Exportar ranking Excel |
| 4 | `listar_convocatorias` | `apps/convocatorias/services.py` | Consulta de convocatorias |
| 4 / 5 actual | `autorregistrar_estudiante` | `apps/acceso/services.py` | CU02/CU03 - Autorregistro |

Nota: Ruff reporta actualmente `autorregistrar_estudiante` como complejidad 5 porque el servicio mantiene compatibilidad legacy con el parámetro `legajo` además de `nro_registro`.

## 2. Pruebas unitarias generadas o reforzadas

Se agregaron pruebas para caminos de decisión que no estaban cubiertos explícitamente:

| Función | Casos agregados/reforzados | Archivo de test |
|---|---|---|
| `iniciar_postulacion` | Beca no pertenece a convocatoria; formulario existente pero incompleto | `apps/postulaciones/tests/test_services.py` |
| `validar_documento` | Documento aprobado pero quedan pendientes; estado de postulación inválido | `apps/postulaciones/tests/test_services.py` |
| `listar_usuarios` | Filtro combinado por exclusión, rol, estado y búsqueda; filtro de inactivos | `apps/usuarios/tests/test_services.py` |
| `listar_convocatorias` | Vista de estudiante solo publicada; filtro staff por estado y búsqueda | `apps/convocatorias/tests/test_services.py` |

Funciones ya cubiertas antes de este refuerzo:

| Función | Evidencia existente |
|---|---|
| `generar_ranking` | `test_generar_ranking_adjudica_correctamente`, `test_generar_ranking_sin_espera` |
| `exportar_ranking_excel` | `test_exportar_excel_retorna_bytes` |
| `autorregistrar_estudiante` | 4 tests de camino básico: éxito, contraseñas distintas, email duplicado y número de registro duplicado |

## 3. Resultado de ejecución y reportes visuales

Comando principal:

```bash
docker-compose exec -T web pytest
```

Resultado:

```text
107 passed, 14 warnings
```

Ejecución con cobertura:

```bash
docker-compose exec -T web coverage run -m pytest
docker-compose exec -T web coverage xml -o coverage.xml
docker-compose exec -T web coverage report
```

Resultado global de cobertura de producto:

```text
TOTAL: 2325 statements, 789 missed, 66% coverage
```

Artefactos visuales generados:

| Reporte | Ruta |
|---|---|
| Panel visual de pruebas | `reports/index.html` |
| JUnit XML de pytest | `reports/pytest-junit.xml` |
| Cobertura HTML navegable | `reports/coverage-html/index.html` |
| Resumen de cobertura | `reports/coverage-summary.txt` |
| Coverage XML para SonarQube | `coverage.xml` |

Cobertura relevante por archivos de negocio:

| Archivo | Cobertura |
|---|---:|
| `apps/acceso/services.py` | 95% |
| `apps/postulaciones/services.py` | 86% |
| `apps/reportes/services.py` | 81% |
| `apps/convocatorias/services.py` | 83% |
| `apps/usuarios/services.py` | 67% |

La cobertura menor en `usuarios/services.py` se explica porque el archivo también contiene CRUD de roles no incluido en el alcance de complejidad > 3 solicitado.

## 4. Pruebas de vulnerabilidad con SonarQube

SonarQube quedó aplicado de manera directa en `docker-compose.yml`, como servicio persistente del proyecto:

```bash
docker-compose up -d sonarqube
```

URL visual:

```text
http://localhost:9000/dashboard?id=becas-universitarias
```

Credenciales locales configuradas por `scripts/setup_sonarqube.ps1`:

```text
Usuario: admin
Password: Admin12345!Dubss
```

El scanner también quedó definido como servicio de Compose:

```bash
docker-compose --profile quality run --rm sonar-scanner
```

Resultado real del scanner:

```text
EXECUTION SUCCESS
ANALYSIS SUCCESSFUL
```

Métricas actuales exportadas desde SonarQube:

| Métrica | Valor |
|---|---:|
| Quality Gate | OK |
| Tests importados | 107 |
| Éxito de tests | 100.0% |
| Fallos de test | 0 |
| Errores de test | 0 |
| Cobertura SonarQube | 66.0% |
| Vulnerabilidades | 19 |
| Security hotspots | 16 |
| Bugs | 10 |
| Code smells | 34 |
| Complejidad total | 513 |

Reportes SonarQube exportados:

| Reporte | Ruta |
|---|---|
| Resumen visual HTML | `reports/sonarqube-summary.html` |
| Quality Gate JSON | `reports/sonarqube-quality-gate.json` |
| Métricas JSON | `reports/sonarqube-measures.json` |
| Vulnerabilidades JSON | `reports/sonarqube-vulnerabilities.json` |
| Security hotspots JSON | `reports/sonarqube-hotspots.json` |

Hallazgos principales:

| Tipo | Ejemplo | Acción sugerida |
|---|---|---|
| Vulnerabilidad `python:S2068` | Credenciales hardcodeadas en `apps/acceso/management/commands/crear_datos_prueba.py` | Mantener solo si son datos semilla de desarrollo o mover a variables de entorno |
| Vulnerabilidad `python:S3752` | Views sin métodos HTTP explícitos | Agregar decoradores como `@require_GET`, `@require_POST` o `@require_http_methods` |
| Vulnerabilidad `Web:S5725` | Recursos externos sin Subresource Integrity | Agregar `integrity`/`crossorigin` o servir assets localmente |
| Security hotspot `Web:S5247` | Uso de `safe` en templates de dashboard | Revisar que el HTML provenga solo de generadores controlados |
| Security hotspot `python:S5332` | URL HTTP para Ollama en settings | Aceptable en desarrollo local; revisar para producción |

### Flujo directo recomendado

1. Generar reportes de pruebas:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generar_reportes_pruebas.ps1
```

2. Levantar/configurar SonarQube:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_sonarqube.ps1
```

3. Ejecutar análisis de vulnerabilidades:

```bash
docker-compose --profile quality run --rm sonar-scanner
```

4. Exportar resumen descargable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\exportar_reporte_sonarqube.ps1
```

## 5. Herramientas usadas

| Herramienta | Uso |
|---|---|
| Docker Compose | Levantar Django, PostgreSQL, Redis y servicios locales |
| PostgreSQL 17 | Base de datos de pruebas y desarrollo |
| pytest | Ejecución de pruebas unitarias |
| pytest-django | Integración de pytest con Django |
| coverage.py | Generación de `coverage.xml` y reporte de cobertura |
| Ruff C901 / McCabe | Verificación de complejidad ciclomática |
| SonarQube Community | Servidor local para análisis estático y vulnerabilidades |
| SonarScanner CLI | Análisis estático de vulnerabilidades, bugs, code smells y cobertura |
| OpenPyXL | Verificación indirecta de exportación XLSX |
| WeasyPrint | Verificación indirecta de generación PDF en pruebas existentes |

## 6. Lista de comprobaciones

| Comprobación | Resultado |
|---|---|
| La app levanta en local | OK |
| Migraciones aplicadas | OK |
| Tests unitarios focalizados | OK, 43 passed |
| Suite completa | OK, 107 passed |
| Coverage XML generado | OK |
| Funciones con complejidad > 3 identificadas | OK |
| Pruebas agregadas para caminos faltantes | OK |
| SonarQube levantado | OK |
| SonarScanner ejecutado hasta dashboard final | OK |
| Reporte SonarQube HTML/JSON exportado | OK |
| Reporte descargable generado | OK |

## 7. Casos de uso aplicados con las pruebas

| Caso de uso / proceso | Funciones probadas | Tipo de prueba |
|---|---|---|
| CU02/CU03 - Autorregistro de estudiante | `autorregistrar_estudiante` | Camino básico, validación de excepciones |
| CU16 - Iniciar postulación | `iniciar_postulacion` | Caminos independientes, reglas de negocio negativas |
| CU19 - Validar documentación física | `validar_documento` | Decisión/ramas, estados válidos e inválidos |
| CU24 - Generar ranking | `generar_ranking` | Clasificación por ramas: adjudicada, lista espera, no adjudicada |
| CU25 - Exportar ranking | `exportar_ranking_excel` | Prueba de bucles estructurales y salida XLSX |
| Gestión de usuarios | `listar_usuarios` | Combinación de condiciones de filtrado |
| Consulta de convocatorias | `listar_convocatorias` | Reglas diferenciadas estudiante/staff |

## 8. Aplicación al flujo de trabajo PUDS

Interpretación usada: PUDS como Proceso Unificado de Desarrollo de Software aplicado al ciclo de pruebas.

| Fase PUDS | Aplicación en este trabajo |
|---|---|
| Inicio / requisitos | Se parte de los CU y del archivo de complejidad ciclomática para detectar procesos críticos |
| Elaboración / análisis | Se identifican puntos de decisión y caminos independientes por función |
| Construcción | Se agregan pruebas unitarias para caminos faltantes sin modificar reglas de negocio |
| Transición / validación | Se ejecuta suite completa, cobertura y análisis estático |
| Retroalimentación | Se documentan huecos, riesgos y comandos reproducibles para SonarQube |

## 9. Técnicas de caja blanca aplicadas

1. Prueba de camino básico:
   Se usa la complejidad ciclomática V(G) para definir caminos independientes. Ejemplo principal: `autorregistrar_estudiante` con caminos de éxito, contraseñas distintas, email duplicado y número de registro duplicado.

2. Cobertura de decisión/rama:
   Se prueban ramas verdaderas y falsas de decisiones críticas. Ejemplos: `validar_documento` con aprobación final, aprobación con pendientes, rechazo y estado inválido.

3. Prueba de condiciones múltiples:
   Se validan filtros combinables. Ejemplos: `listar_usuarios(excluir_pk, rol, estado, busqueda)` y `listar_convocatorias(para_estudiante, estado, busqueda)`.

4. Prueba de bucles:
   Se ejercitan funciones con iteración sobre colecciones. Ejemplos: `generar_ranking` recorre postulaciones procesadas; `exportar_ranking_excel` recorre encabezados, filas y celdas.

5. Prueba de manejo de excepciones:
   Se verifican salidas por errores de dominio. Ejemplos: `BecaNoDisponibleError`, `FormularioIncompletoError`, `TransicionEstadoInvalidaError`, `DocumentoNoPendienteError`.

## 10. Conclusión

Se reforzó la suite de pruebas unitarias para las funciones de negocio con complejidad ciclomática mayor a 3 indicadas en el documento base. La suite completa queda en verde con 107 pruebas exitosas, se generaron reportes visuales descargables y SonarQube quedó integrado de forma directa al flujo del proyecto.

El análisis de vulnerabilidades con SonarQube concluyó correctamente. El Quality Gate queda en estado OK, pero existen 19 vulnerabilidades y 16 security hotspots abiertos que deben revisarse. La mayor parte de los hallazgos corresponde a credenciales hardcodeadas en datos semilla de desarrollo, métodos HTTP no explicitados en views, recursos externos sin SRI y uso de `safe` en templates de reportes.


--usuario de sonarcube
user:admin
pass: Admin12345!Dubss