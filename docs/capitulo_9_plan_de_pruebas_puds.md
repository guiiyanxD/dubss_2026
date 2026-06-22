# CAPÍTULO 9: PLAN DE PRUEBAS

## 9.1. Planificación de Pruebas

El plan de pruebas del Sistema de Gestión de Becas Universitarias se elaboró siguiendo el enfoque del Proceso Unificado de Desarrollo de Software (PUDS), considerando que las pruebas no se ejecutan únicamente al final del proyecto, sino que acompañan las fases de inicio, elaboración, construcción y transición.

En la fase de inicio se identificaron los actores, casos de uso críticos y reglas de negocio principales. En la fase de elaboración se analizaron los flujos de mayor riesgo, especialmente aquellos relacionados con postulación, validación documental, procesamiento socioeconómico, ranking y seguridad. En la fase de construcción se implementaron pruebas unitarias, pruebas funcionales y pruebas de caja blanca sobre los servicios de negocio. Finalmente, en la fase de transición se ejecutaron pruebas automatizadas, cobertura, análisis de vulnerabilidades con SonarQube y generación de evidencias descargables.

### Objetivo General

Verificar que los módulos principales del sistema cumplan los requisitos funcionales, reglas de negocio, restricciones de seguridad y criterios de calidad definidos para el proceso de gestión de becas universitarias.

### Objetivos Específicos

- Validar los casos de uso críticos del sistema mediante pruebas automatizadas.
- Comprobar reglas de negocio asociadas a postulación, documentación, usuarios, convocatorias y ranking.
- Evaluar funciones con complejidad ciclomática mayor a 3 mediante técnicas de caja blanca.
- Generar evidencias verificables de ejecución de pruebas unitarias, cobertura y análisis de vulnerabilidades.
- Integrar SonarQube como herramienta permanente de análisis de calidad y seguridad.
- Documentar el flujo de pruebas bajo el formato PUDS.

### Alcance de las Pruebas

El alcance incluye pruebas sobre los siguientes paquetes funcionales:

| Paquete | Módulo | Casos de uso relacionados |
|---|---|---|
| P1 Acceso y Seguridad | Registro, autenticación y roles | CU01, CU02, CU03 |
| P2 Administración de Usuarios | Gestión y filtrado de usuarios | CU04, CU05, CU06, CU07 |
| P3 Convocatorias | Convocatorias, becas y requisitos | CU09, CU10, CU11, CU12, CU13, CU14 |
| P5 Postulación y Documentación | Registro, envío, revisión y validación | CU16, CU17, CU18, CU19, CU20 |
| P6 Notificaciones | Notificación de eventos | CU27 |
| P7 Procesamiento y Reportes | Ranking, Excel, dashboard y reportes | CU23, CU24, CU25, CU26 |

### Criterios de Entrada

- El proyecto debe levantar correctamente en ambiente local mediante Docker Compose.
- Las migraciones de base de datos deben ejecutarse sin errores.
- El archivo `.env` debe contener las variables necesarias para Django, PostgreSQL, Redis y SonarQube.
- Los módulos principales deben contar con datos de prueba o fixtures.
- SonarQube debe estar disponible en `http://localhost:9000`.

### Criterios de Salida

- La suite automatizada debe ejecutarse sin errores.
- Los resultados de pytest deben generar reporte JUnit XML.
- Debe existir reporte de cobertura HTML y XML.
- SonarQube debe ejecutar el análisis estático correctamente.
- Deben registrarse métricas de pruebas, cobertura, vulnerabilidades, bugs, code smells y security hotspots.
- Las evidencias deben quedar disponibles en la carpeta `reports/`.

### Ambiente de Pruebas

| Componente | Tecnología / Herramienta |
|---|---|
| Lenguaje | Python 3.12 |
| Framework web | Django 5.2 |
| Base de datos | PostgreSQL 17 |
| Contenedores | Docker Compose |
| Pruebas unitarias | pytest, pytest-django |
| Cobertura | coverage.py |
| Calidad y vulnerabilidades | SonarQube Community + SonarScanner |
| Reportes visuales | HTML, XML, JSON |

### Herramientas Utilizadas

| Herramienta | Uso dentro del plan de pruebas |
|---|---|
| pytest | Ejecución de pruebas unitarias y funcionales automatizadas |
| pytest-django | Integración de pruebas con el ORM y configuración Django |
| coverage.py | Medición de cobertura y generación de `coverage.xml` |
| SonarQube | Análisis estático, vulnerabilidades, bugs y métricas de calidad |
| SonarScanner | Envío del análisis del proyecto hacia SonarQube |
| Ruff C901 | Identificación de funciones con alta complejidad ciclomática |
| Docker Compose | Reproducción del ambiente local de pruebas |
| PostgreSQL | Persistencia de datos durante pruebas de integración con ORM |

### Relación con PUDS

| Fase PUDS | Actividad de pruebas aplicada |
|---|---|
| Inicio | Identificación de actores, casos de uso y riesgos generales |
| Elaboración | Selección de casos de uso críticos y funciones complejas |
| Construcción | Implementación de pruebas automatizadas y caja blanca |
| Transición | Ejecución completa, reportes, cobertura y SonarQube |

## 9.2. Diseño de Pruebas

El diseño de pruebas se basó en los casos de uso, reglas de negocio y complejidad ciclomática del sistema. Se aplicaron pruebas de caja negra para validar entradas y salidas esperadas desde la perspectiva funcional, pruebas de caja blanca para cubrir caminos internos de decisión y pruebas de vulnerabilidad para revisar riesgos de seguridad con análisis estático.

### Estrategia de Diseño

| Tipo de prueba | Propósito | Evidencia generada |
|---|---|---|
| Caja negra | Validar comportamiento funcional sin considerar implementación interna | Resultado de pytest y casos funcionales |
| Caja blanca | Verificar decisiones internas, caminos básicos, ramas y excepciones | Tests por función, cobertura y complejidad |
| Vulnerabilidad | Detectar riesgos de seguridad, credenciales, XSS, HTTP inseguro y endpoints | Dashboard y JSON de SonarQube |
| Regresión | Confirmar que los cambios no rompen funcionalidades existentes | Suite completa de 107 tests |
| Cobertura | Medir porcentaje de código ejecutado por las pruebas | `coverage.xml` y HTML |

### Casos de Uso Priorizados

Los casos de uso priorizados fueron seleccionados por impacto funcional, criticidad y presencia de reglas de negocio.

| CU | Nombre | Motivo de priorización |
|---|---|---|
| CU03 | Autorregistrarse como Estudiante | Entrada principal de estudiantes al sistema |
| CU07 | Asignar Rol a Usuario | Control de acceso y permisos |
| CU10 | Publicar Convocatoria | Habilita postulaciones |
| CU16 | Completar Formulario Socioeconómico | Requisito previo para postulación |
| CU17 | Registrar Postulación | Flujo central del estudiante |
| CU18 | Verificar Identidad | Control presencial de validez |
| CU19 | Validar Documentación Física | Flujo crítico de aprobación/rechazo |
| CU23 | Procesar Formularios Socioeconómicos | Cálculo de puntajes |
| CU24 | Generar Ranking | Determina adjudicación |
| CU25 | Exportar Ranking | Evidencia administrativa descargable |
| CU26 | Visualizar Dashboard de Reportes | Consulta gerencial |

## 9.2.1. Identificación y Estructuración de Procedimiento de Prueba

El procedimiento de prueba se estructuró en pasos repetibles para asegurar trazabilidad entre caso de uso, función probada, técnica aplicada y evidencia generada.

### Procedimiento General

1. Levantar el entorno local:

```powershell
docker-compose up -d
```

2. Ejecutar migraciones:

```powershell
docker-compose exec -T web python manage.py migrate
```

3. Ejecutar pruebas unitarias y generar evidencias:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generar_reportes_pruebas.ps1
```

4. Levantar o configurar SonarQube:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_sonarqube.ps1
```

5. Ejecutar análisis SonarQube:

```powershell
docker-compose --profile quality run --rm sonar-scanner
```

6. Exportar reporte de SonarQube:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\exportar_reporte_sonarqube.ps1
```

### Matriz de Trazabilidad de Pruebas

| ID prueba | CU | Función / módulo | Tipo | Técnica | Resultado esperado |
|---|---|---|---|---|---|
| PT-CU03-01 | CU03 | `autorregistrar_estudiante` | Caja blanca | Camino básico | Usuario y perfil creados |
| PT-CU03-02 | CU03 | `autorregistrar_estudiante` | Caja blanca | Excepción | Error por contraseñas distintas |
| PT-CU03-03 | CU03 | `autorregistrar_estudiante` | Caja blanca | Excepción | Error por email duplicado |
| PT-CU03-04 | CU03 | `autorregistrar_estudiante` | Caja blanca | Excepción | Error por número de registro duplicado |
| PT-CU07-01 | CU07 | `asignar_rol` | Caja negra | Partición válida | Usuario cambia de rol |
| PT-CU16-01 | CU16/CU17 | `iniciar_postulacion` | Caja blanca | Camino básico | Postulación en borrador |
| PT-CU16-02 | CU16/CU17 | `iniciar_postulacion` | Caja blanca | Rama negativa | Error por convocatoria cerrada |
| PT-CU16-03 | CU16/CU17 | `iniciar_postulacion` | Caja blanca | Rama negativa | Error por beca no disponible |
| PT-CU16-04 | CU16/CU17 | `iniciar_postulacion` | Caja blanca | Rama negativa | Error por formulario incompleto |
| PT-CU17-01 | CU17 | `enviar_postulacion` | Caja negra | Estado válido | Estado cambia a enviada |
| PT-CU18-01 | CU18 | `verificar_identidad` | Caja blanca | Decisión | Identidad aprobada |
| PT-CU18-02 | CU18 | `verificar_identidad` | Caja blanca | Decisión | Identidad rechazada |
| PT-CU19-01 | CU19 | `validar_documento` | Caja blanca | Rama | Aprueba último documento |
| PT-CU19-02 | CU19 | `validar_documento` | Caja blanca | Rama | Rechaza documentación |
| PT-CU19-03 | CU19 | `validar_documento` | Caja blanca | Rama | Aprueba con documentos pendientes |
| PT-CU19-04 | CU19 | `validar_documento` | Caja blanca | Excepción | Documento ya validado |
| PT-CU19-05 | CU19 | `validar_documento` | Caja blanca | Excepción | Estado de postulación inválido |
| PT-CU24-01 | CU24 | `generar_ranking` | Caja blanca | Bucles y ramas | Adjudicada y lista de espera |
| PT-CU24-02 | CU24 | `generar_ranking` | Caja blanca | Rama alternativa | Adjudicada y no adjudicada |
| PT-CU25-01 | CU25 | `exportar_ranking_excel` | Caja negra | Salida descargable | Archivo XLSX válido |
| PT-SEG-01 | Seguridad | SonarQube | Vulnerabilidad | Análisis estático | Hallazgos registrados |

### Evidencias del Procedimiento

Las evidencias deben colocarse como anexos o figuras dentro del documento final. Se recomienda insertar capturas de pantalla y debajo una breve descripción.

| Evidencia | Archivo / ubicación | Cómo colocarla en el documento |
|---|---|---|
| Resultado general de pruebas | `reports/index.html` | Captura como “Figura 9.1. Panel general de pruebas unitarias” |
| Cobertura visual | `reports/coverage-html/index.html` | Captura como “Figura 9.2. Reporte HTML de cobertura” |
| XML de pruebas | `reports/pytest-junit.xml` | Referenciar como anexo técnico |
| Cobertura XML | `coverage.xml` | Referenciar como insumo de SonarQube |
| SonarQube dashboard | `http://localhost:9000/dashboard?id=becas-universitarias` | Captura como “Figura 9.3. Dashboard de SonarQube” |
| Resumen SonarQube | `reports/sonarqube-summary.html` | Captura como “Figura 9.4. Reporte exportado de vulnerabilidades” |
| Vulnerabilidades JSON | `reports/sonarqube-vulnerabilities.json` | Referenciar como anexo de seguridad |

## 9.3. Pruebas Realizadas

Las pruebas realizadas se agrupan en pruebas de caja negra, caja blanca y vulnerabilidad. La ejecución completa de la suite automatizada produjo el siguiente resultado:

```text
107 passed, 14 warnings
```

La cobertura general reportada fue:

```text
TOTAL: 2325 statements, 789 missed, 66% coverage
```

En SonarQube se importaron 107 pruebas con 100% de éxito, 0 fallos y 0 errores.

## 9.3.1. Pruebas de Caja Negra

Las pruebas de caja negra validan el comportamiento externo del sistema sin revisar la estructura interna del código. Se diseñaron a partir de entradas, salidas esperadas, estados del sistema y reglas de negocio.

### Técnicas de Caja Negra Aplicadas

| Técnica | Aplicación |
|---|---|
| Partición de equivalencia | Datos válidos e inválidos para registro, roles, convocatorias y becas |
| Valores límite | Fechas de apertura/cierre y ponderaciones que deben sumar 100 |
| Tabla de decisión | Estados de postulación y resultado esperado |
| Transición de estados | Borrador, Enviada, En revisión, Aprobada, Rechazada |
| Validación de salida | Archivos PDF/XLSX generados correctamente |

### Casos Representativos

| Caso | Entrada | Salida esperada | Resultado |
|---|---|---|---|
| Registro de usuario interno | Email nuevo, rol Director | Usuario creado sin contraseña usable | Aprobado |
| Registro con rol inválido | Rol Superadmin | Excepción `RolInvalidoError` | Aprobado |
| Convocatoria con fechas inválidas | Cierre anterior a apertura | Excepción `FechaInvalidaError` | Aprobado |
| Publicar convocatoria | Estado Borrador | Estado Publicada | Aprobado |
| Crear beca con pesos incorrectos | Suma distinta de 100 | Excepción `PonderacionInvalidaError` | Aprobado |
| Enviar postulación | Estado Borrador | Estado Enviada y número de referencia | Aprobado |
| Descargar constancia | Postulación enviada | PDF válido `%PDF` | Aprobado |
| Exportar ranking | Ranking generado | XLSX válido `PK` | Aprobado |

### Evidencia Sugerida

Insertar una captura de `reports/index.html` mostrando:

- Total de pruebas: 107.
- Pruebas pasadas.
- Pruebas fallidas: 0.
- Errores: 0.

Texto sugerido para el documento:

> Figura 9.1. Resultado visual de la ejecución de pruebas unitarias y funcionales. Se observa que la suite automatizada finalizó con 107 pruebas exitosas, sin fallos ni errores.

## 9.3.2. Pruebas de Caja Blanca

Las pruebas de caja blanca se aplicaron revisando la lógica interna de las funciones con mayor complejidad ciclomática, especialmente aquellas identificadas en `docs/complejidad-ciclomatico.md`. El objetivo fue cubrir caminos independientes, decisiones, ramas, bucles y excepciones.

### Funciones con Complejidad Mayor a 3

| Complejidad | Función | Archivo | Pruebas asociadas |
|---:|---|---|---|
| 6 | `iniciar_postulacion` | `apps/postulaciones/services.py` | 6 pruebas |
| 6 | `validar_documento` | `apps/postulaciones/services.py` | 5 pruebas |
| 6 | `listar_usuarios` | `apps/usuarios/services.py` | 2 pruebas específicas + pruebas de usuario |
| 5 | `generar_ranking` | `apps/reportes/services.py` | 2 pruebas |
| 4 | `exportar_ranking_excel` | `apps/reportes/services.py` | 1 prueba |
| 4 | `listar_convocatorias` | `apps/convocatorias/services.py` | 2 pruebas específicas |
| 5 | `autorregistrar_estudiante` | `apps/acceso/services.py` | 4 pruebas |

### Técnicas de Caja Blanca Aplicadas

#### 1. Prueba de Camino Básico

Se utilizó la complejidad ciclomática para identificar el número mínimo de caminos independientes. Para `autorregistrar_estudiante`, los caminos son:

| Camino | Condición | Test |
|---|---|---|
| C1 | Datos válidos | `test_autorregistrar_estudiante_exitoso` |
| C2 | Contraseñas distintas | `test_autorregistrar_estudiante_contrasenas_distintas` |
| C3 | Email duplicado | `test_autorregistrar_estudiante_email_duplicado` |
| C4 | Número de registro duplicado | `test_autorregistrar_estudiante_nro_registro_duplicado` |

#### 2. Cobertura de Decisión

Se probaron ramas verdaderas y falsas de condiciones críticas.

| Función | Decisión | Test |
|---|---|---|
| `validar_documento` | Documento ya validado | `test_validar_documento_ya_validado` |
| `validar_documento` | Estado de postulación inválido | `test_validar_documento_estado_postulacion_invalido` |
| `validar_documento` | Aprobar o rechazar | `test_validar_documento_aprueba_ultimo_y_cierra`, `test_validar_documento_rechaza_y_cierra` |
| `verificar_identidad` | Aprobar o rechazar identidad | `test_verificar_identidad_aprobada_sin_docs`, `test_verificar_identidad_rechazada` |

#### 3. Cobertura de Condiciones Múltiples

Se aplicó en filtros con varias condiciones opcionales.

| Función | Condiciones probadas | Test |
|---|---|---|
| `listar_usuarios` | `excluir_pk`, `rol`, `estado`, `busqueda` | `test_listar_usuarios_filtra_por_excluir_rol_estado_y_busqueda` |
| `listar_usuarios` | estado inactivo | `test_listar_usuarios_filtra_inactivos` |
| `listar_convocatorias` | estudiante + búsqueda | `test_listar_convocatorias_para_estudiante_solo_publicadas` |
| `listar_convocatorias` | staff + estado + búsqueda | `test_listar_convocatorias_staff_filtra_por_estado_y_busqueda` |

#### 4. Prueba de Bucles

Se ejercitaron funciones con iteración interna.

| Función | Bucle | Test |
|---|---|---|
| `generar_ranking` | Recorre postulaciones procesadas | `test_generar_ranking_adjudica_correctamente` |
| `generar_ranking` | Clasifica con y sin cupo de espera | `test_generar_ranking_sin_espera` |
| `exportar_ranking_excel` | Recorre encabezados, filas y celdas | `test_exportar_excel_retorna_bytes` |

#### 5. Prueba de Manejo de Excepciones

Se verificó que las reglas de negocio corten el flujo cuando corresponde.

| Excepción | Escenario | Test |
|---|---|---|
| `ConvocatoriaNoVigenteError` | Convocatoria cerrada | `test_iniciar_postulacion_convocatoria_cerrada` |
| `BecaNoDisponibleError` | Beca fuera de convocatoria | `test_iniciar_postulacion_beca_no_pertenece_a_convocatoria` |
| `FormularioIncompletoError` | Formulario ausente o incompleto | `test_iniciar_postulacion_sin_formulario`, `test_iniciar_postulacion_formulario_incompleto` |
| `TransicionEstadoInvalidaError` | Estado incorrecto | `test_enviar_postulacion_invalida`, `test_validar_documento_estado_postulacion_invalido` |
| `DocumentoNoPendienteError` | Documento ya validado | `test_validar_documento_ya_validado` |

### Evidencias de Caja Blanca

Para evidenciar las pruebas de caja blanca se recomienda incluir:

1. Captura del reporte de cobertura HTML:

```text
reports/coverage-html/index.html
```

2. Tabla de cobertura por archivo:

| Archivo | Cobertura |
|---|---:|
| `apps/acceso/services.py` | 95% |
| `apps/postulaciones/services.py` | 86% |
| `apps/reportes/services.py` | 81% |
| `apps/convocatorias/services.py` | 83% |
| `apps/usuarios/services.py` | 67% |

3. Captura de tests en verde desde `reports/index.html`.

Texto sugerido:

> Figura 9.2. Reporte de cobertura HTML generado con coverage.py. La evidencia permite revisar visualmente qué líneas fueron ejecutadas por las pruebas unitarias y qué secciones permanecen sin cubrir.

## 9.3.3. Pruebas de Vulnerabilidad

Las pruebas de vulnerabilidad se realizaron con SonarQube Community Edition integrado directamente al proyecto mediante Docker Compose. Esta herramienta ejecuta análisis estático para detectar vulnerabilidades, security hotspots, bugs, code smells, duplicación y cobertura.

### Configuración Aplicada

SonarQube se agregó como servicio permanente:

```yaml
sonarqube:
  image: sonarqube:community
  restart: unless-stopped
  ports:
    - "9000:9000"
```

El scanner se ejecuta con:

```powershell
docker-compose --profile quality run --rm sonar-scanner
```

### Resultado del Análisis

| Métrica | Resultado |
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

### Hallazgos Principales

| Categoría | Descripción | Acción recomendada |
|---|---|---|
| Credenciales hardcodeadas | Sonar detecta valores con nombre `password` en datos semilla | Mantener solo en desarrollo o mover a variables de entorno |
| Métodos HTTP no explícitos | Algunas vistas no restringen método HTTP mediante decoradores | Usar `@require_GET`, `@require_POST` o `@require_http_methods` |
| Recursos externos sin SRI | Templates cargan recursos sin Subresource Integrity | Agregar `integrity` y `crossorigin` |
| Uso de `safe` en templates | Posible riesgo XSS si el contenido no está controlado | Justificar origen seguro o sanitizar |
| HTTP en configuración local | URL de Ollama usa `http://` | Aceptable en desarrollo, revisar para producción |

### Evidencias de Vulnerabilidad

| Evidencia | Ruta / URL |
|---|---|
| Dashboard SonarQube | `http://localhost:9000/dashboard?id=becas-universitarias` |
| Reporte HTML exportado | `reports/sonarqube-summary.html` |
| Métricas JSON | `reports/sonarqube-measures.json` |
| Vulnerabilidades JSON | `reports/sonarqube-vulnerabilities.json` |
| Security hotspots JSON | `reports/sonarqube-hotspots.json` |

Texto sugerido para el documento:

> Figura 9.3. Dashboard de SonarQube con el resultado del Quality Gate, métricas de cobertura, vulnerabilidades, bugs y code smells del proyecto.

> Figura 9.4. Reporte exportado de vulnerabilidades donde se muestran los hallazgos abiertos y los security hotspots pendientes de revisión.

## 9.4. Gestión de Evidencias

Para cumplir el formato PUDS, las evidencias deben vincularse con la fase, actividad y resultado esperado.

| Fase PUDS | Evidencia | Archivo / captura |
|---|---|---|
| Inicio | Catálogo de casos de uso | `contexto_casos_de_uso.md` |
| Elaboración | Complejidad ciclomática y selección de funciones críticas | `docs/complejidad-ciclomatico.md` |
| Construcción | Pruebas unitarias implementadas | Archivos `apps/*/tests/test_*.py` |
| Construcción | Reporte de ejecución pytest | `reports/index.html` |
| Construcción | Reporte JUnit XML | `reports/pytest-junit.xml` |
| Transición | Cobertura HTML | `reports/coverage-html/index.html` |
| Transición | Análisis SonarQube | `reports/sonarqube-summary.html` |
| Transición | Vulnerabilidades exportadas | `reports/sonarqube-vulnerabilities.json` |

### Formato Recomendado para Insertar Evidencias

Cada evidencia debe colocarse con:

- Número de figura.
- Título.
- Fuente.
- Interpretación breve.

Ejemplo:

```text
Figura 9.1. Resultado de ejecución de pruebas automatizadas.
Fuente: Reporte generado por pytest en reports/index.html.
Interpretación: La suite presenta 107 pruebas ejecutadas, 107 aprobadas, 0 fallidas y 0 errores, cumpliendo el criterio de salida definido para la fase de transición.
```

## 9.5. Conclusiones del Plan de Pruebas

El plan de pruebas permitió validar los módulos críticos del sistema bajo un enfoque PUDS, relacionando los casos de uso con pruebas automatizadas, cobertura de código, caja blanca y análisis de vulnerabilidades.

La ejecución final demostró que la suite automatizada se encuentra estable, con 107 pruebas aprobadas. Las pruebas de caja blanca cubren funciones con alta complejidad ciclomática mediante camino básico, decisiones, condiciones múltiples, bucles y excepciones. Además, SonarQube quedó integrado directamente al proyecto, permitiendo visualizar el estado de calidad y seguridad desde un dashboard local.

Aunque el Quality Gate se encuentra en estado OK, el análisis identificó vulnerabilidades, bugs, code smells y security hotspots que deben ser tratados como tareas de mejora antes de un despliegue productivo.
