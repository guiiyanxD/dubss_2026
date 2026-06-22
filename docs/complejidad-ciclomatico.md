## Índice

1. [Complejidad Ciclomática](#complejidad-ciclomatica)
   1. [Qué es](#que-es)
   2. [Tabla: procesos de negocio con complejidad ≥ 3](#tabla-complejidad)
   3. [Justificación (puntos de decisión por función)](#justificacion-funciones)
      - `iniciar_postulacion`, `validar_documento`, `listar_usuarios`, `generar_ranking`, `exportar_ranking_excel`, `listar_convocatorias`, `autorregistrar_estudiante`, `enviar_postulacion`, `verificar_identidad`, `procesar_formularios_socioeconomicos`, `registrar_usuario`, `asignar_rol`, `notificar_identidad_verificada`, `notificar_resultado_adjudicacion`, `tarea_enviar_email`
2. [Pruebas de Caja Blanca: Prueba de Camino Básico](#pruebas-caja-blanca)
   1. [Teoría básica](#teoria-basica)
   2. [Justificación teórica de la aplicación a `autorregistrar_estudiante`](#justificacion-teorica-aplicacion)
   3. [Aplicación práctica](#aplicacion-practica)
      - Grafo de flujo, cálculo de V(G), conjunto base de caminos, casos de prueba derivados, verificación contra tests reales
3. [Análisis con SonarQube](#analisis-sonarqube)
   1. [Objetivo](#sonar-objetivo)
   2. [Paso 1 — Levantar SonarQube Community Edition (local, Docker)](#sonar-paso-1)
   3. [Paso 2 — Crear proyecto y token de autenticación](#sonar-paso-2)
   4. [Paso 3 — Generar reporte de cobertura local](#sonar-paso-3)
   5. [Paso 4 — Configurar `sonar-project.properties`](#sonar-paso-4)
   6. [Paso 5 — Ejecutar el scanner](#sonar-paso-5)
   7. [Paso 6 — Consultar resultados (API y dashboard)](#sonar-paso-6)
   8. [Resultados obtenidos sobre `autorregistrar_estudiante`](#sonar-resultados)
   9. [Detener el entorno local](#sonar-limpieza)

---

<a id="complejidad-ciclomatica"></a>
# Complejidad Ciclomática

<a id="que-es"></a>
## Qué es

Métrica de McCabe que cuenta caminos de ejecución independientes en una función. Fórmula práctica:

**M = D + 1**

Donde `D` es la cantidad de puntos de decisión (`if`, `elif`, `for`, `while`, `except`). El proyecto usa `ruff` (ya en `requirements.txt`) como herramienta de medición, vía su regla `C901` (mccabe), corrida así:

```bash
docker compose exec web ruff check --select C901 --config "lint.mccabe.max-complexity=2" apps/
```

Nota de metodología: expresiones ternarias (`x if cond else y`), comprensiones de listas/diccionarios y la rama `else` **no** suman un punto — McCabe las trata como continuación del mismo camino, no como un camino nuevo. Solo cuentan los puntos donde el camino se *bifurca* (`if`/`elif`/`for`/`while`/`except`).

<a id="tabla-complejidad"></a>
## Tabla: procesos de negocio (`services.py`) con complejidad ≥ 3

| Complejidad | Función | Archivo | CU / Proceso |
|---|---|---|---|
| 6 | `iniciar_postulacion` | `postulaciones/services.py` | CU16 — Iniciar postulación |
| 6 | `validar_documento` | `postulaciones/services.py` | CU19 — Validar documentación física |
| 6 | `listar_usuarios` | `usuarios/services.py` | Filtro de usuarios (rol/estado/búsqueda) |
| 5 | `generar_ranking` | `reportes/services.py` | CU24 — Generar ranking |
| 4 | `exportar_ranking_excel` | `reportes/services.py` | CU25 — Exportar Excel |
| 4 | `listar_convocatorias` | `convocatorias/services.py` | Filtro de convocatorias |
| 4 | `autorregistrar_estudiante` | `acceso/services.py` | CU02/CU03 — Autorregistro de estudiante |
| 3 | `enviar_postulacion` | `postulaciones/services.py` | CU17 — Enviar postulación |
| 3 | `verificar_identidad` | `postulaciones/services.py` | CU18 — Verificar identidad |
| 3 | `procesar_formularios_socioeconomicos` | `reportes/services.py` | CU23 — Procesar formularios (Pandas) |
| 3 | `registrar_usuario` | `usuarios/services.py` | Alta de Director/Operador |
| 3 | `asignar_rol` | `usuarios/services.py` | Cambio de rol de un usuario |
| 3 | `notificar_identidad_verificada` | `notificaciones/services.py` | Notificación de CU18 |
| 3 | `notificar_resultado_adjudicacion` | `notificaciones/services.py` | Notificación de CU26 |
| 3 | `tarea_enviar_email` | `notificaciones/tasks.py` | Envío async de email (Celery) |

De los 8 CU críticos documentados en `CLAUDE.md` (con diagramas de comunicación/secuencia propios), 5 caen en esta tabla: **CU17, CU18, CU19, CU23, CU24**. Los otros tres (CU01, CU11, CU20) tienen complejidad 1-2 — son lineales o con una sola condición.

<a id="justificacion-funciones"></a>
## Justificación (puntos de decisión por función)

### `iniciar_postulacion` — CU16 (complejidad 6)
1. `if not convocatoria.esta_vigente():` → `ConvocatoriaNoVigenteError`
2. `if not convocatoria.becas.filter(pk=beca.pk).exists():` → `BecaNoDisponibleError`
3. `if Postulacion.objects.filter(estudiante=..., estado__in=ESTADOS_ACTIVOS).exists():` → `PostulacionActivaExistenteError`
4. `except FormularioSocioeconomico.DoesNotExist:` → `FormularioIncompletoError`
5. `if not formulario.completado:` → `FormularioIncompletoError`

5 decisiones + 1 = 6. Es la función con más reglas de negocio encadenadas: vigencia de la convocatoria, pertenencia de la beca, unicidad de postulación activa, y completitud del formulario socioeconómico.

### `validar_documento` — CU19 (complejidad 6)
1. `if documento.validado is not None:` → `DocumentoNoPendienteError`
2. `if postulacion.estado != EN_REVISION:` → `TransicionEstadoInvalidaError`
3. `if not aprobar:` (rama de rechazo)
4. `if not pendientes:` (dentro del `else`, evalúa si era el último documento pendiente)
5. `if estado_final is not None:` (decide si dispara la señal `documentacion_procesada`)

5 decisiones + 1 = 6. La complejidad viene de que la validación de UN documento puede cerrar el estado de TODA la postulación si era el último pendiente, requiriendo verificar el estado de los demás documentos.

### `listar_usuarios` (complejidad 6)
1. `if excluir_pk:`
2. `if rol:`
3. `if estado == "activo":`
4. `elif estado == "inactivo":`
5. `if busqueda:`

5 decisiones + 1 = 6. Es un filtro combinable de 4 criterios independientes (excluir, rol, estado, búsqueda de texto).

### `generar_ranking` — CU24 (complejidad 5)
1. `if cupo_espera is None:` (default = cupo)
2. `for i, p in enumerate(postulaciones):` (recorre todas las postulaciones a clasificar)
3. `if i < cupo:` → `ADJUDICADA`
4. `elif i < cupo + cupo_espera:` → `LISTA_ESPERA`
   (la rama `else` → `NO_ADJUDICADA` no suma)

4 decisiones + 1 = 5. Clasifica cada postulación en 3 resultados posibles según su posición en el orden de puntaje.

### `exportar_ranking_excel` — CU25 (complejidad 4)
1. `for col, (header, width) in enumerate(zip(headers, col_widths), ...)` (encabezados)
2. `for pos, p in enumerate(postulaciones, start=1):` (filas del ranking)
3. `for col, valor in enumerate(fila, start=1):` (celdas de cada fila)

3 bucles anidados + 1 = 4. Complejidad puramente estructural (armado de la planilla), no de reglas de negocio.

### `listar_convocatorias` (complejidad 4)
1. `if para_estudiante:`
2. `elif estado:`
3. `if busqueda:`

3 decisiones + 1 = 4. Filtro combinable similar a `listar_usuarios`, con la regla de negocio de que un estudiante solo puede ver convocatorias `PUBLICADA`.

### `autorregistrar_estudiante` — CU02/CU03 (complejidad 4)
1. `if password1 != password2:` → `ContrasenasNoCoincidenceError`
2. `if Usuario.objects.filter(email=email).exists():` → `EmailYaRegistradoError`
3. `if PerfilEstudiante.objects.filter(legajo=legajo).exists():` → `LegajoYaRegistradoError`

3 decisiones + 1 = 4. Tres validaciones de unicidad/consistencia antes de crear el `Usuario` + `PerfilEstudiante`.

### `enviar_postulacion` — CU17 (complejidad 3)
1. `if postulacion.estado != BORRADOR:` → `TransicionEstadoInvalidaError`
2. `for tipo_doc in postulacion.convocatoria.documentos_requeridos.all():` (crea un `DocumentoPostulacion` por cada tipo requerido)

2 decisiones + 1 = 3.

### `verificar_identidad` — CU18 (complejidad 3)
1. `if postulacion.estado != ENVIADA:` → `TransicionEstadoInvalidaError`
2. `if aprobar:` / `else:` (aprobar pasa a EN_REVISION o APROBADA; rechazar pasa a RECHAZADA_IDENTIDAD)

2 decisiones + 1 = 3.

### `procesar_formularios_socioeconomicos` — CU23 (complejidad 3)
1. `if not postulaciones:` (corte temprano si no hay nada que procesar)
2. `for _, row in df.iterrows():` (graba el puntaje calculado de vuelta en cada `Postulacion`)

2 decisiones + 1 = 3. El cálculo del puntaje en sí (normalización y ponderación con Pandas) es vectorizado, sin ramas — la complejidad de control de flujo es baja aunque el cálculo numérico no sea trivial.

### `registrar_usuario` (complejidad 3)
1. `if rol not in ROLES_INTERNOS:` → `RolInvalidoError`
2. `if Usuario.objects.filter(email=email).exists():` → `EmailYaRegistradoError`

2 decisiones + 1 = 3.

### `asignar_rol` (complejidad 3)
1. `if rol not in ROLES_VALIDOS:` → `RolInvalidoError`
2. `if not grupo:` → `RolInvalidoError` (grupo no existe en la tabla `auth_group`)

2 decisiones + 1 = 3.

### `notificar_identidad_verificada` (complejidad 3)
1. `if aprobada:` / `else:`
2. `if tiene_docs:` (anidado dentro de la rama `aprobada`, decide el texto del mensaje)

2 decisiones + 1 = 3.

### `notificar_resultado_adjudicacion` (complejidad 3)
1. `if postulacion.estado == "ADJUDICADA":`
2. `elif postulacion.estado == "LISTA_ESPERA":`
   (rama `else` → no adjudicada, no suma)

2 decisiones + 1 = 3.

### `tarea_enviar_email` (complejidad 3)
1. `except Notificacion.DoesNotExist:` (la notificación fue borrada antes de procesarse)
2. `except Exception as exc:` (falla el envío real del email → reintento vía `self.retry`)

2 decisiones + 1 = 3. Es la única tarea Celery del proyecto con manejo explícito de reintentos.

---

<a id="pruebas-caja-blanca"></a>
# Pruebas de Caja Blanca: Prueba de Camino Básico

<a id="teoria-basica"></a>
## Teoría básica

La **prueba de camino básico** (basis path testing) es la técnica de caja blanca propuesta por Thomas McCabe — la misma persona detrás de la complejidad ciclomática — y es la razón por la que esa métrica importa más allá de "medir qué tan complicado es el código": **V(G) no es solo un número de calidad, es la cantidad exacta de casos de prueba que hacen falta para cubrir toda la lógica de decisión de una función, ni uno más ni uno menos.**

### Procedimiento (4 pasos)

1. **Construir el grafo de flujo** de la función a partir del código fuente: cada bloque de sentencias secuenciales es un nodo, cada posible transferencia de control (una rama de un `if`, la entrada/salida de un `for`/`while`, una cláusula `except`) es una arista dirigida.
2. **Calcular la complejidad ciclomática** del grafo: `V(G) = E - N + 2P` (E=aristas, N=nodos, P=componentes conexos, P=1 para una función). Es la misma fórmula y el mismo número que ya calculamos con `ruff` en la sección anterior — el grafo es solo la representación visual de esa cuenta.
3. **Determinar el conjunto base** de `V(G)` caminos *linealmente independientes*: cada camino del conjunto debe introducir al menos una arista nueva que ningún camino anterior del conjunto haya recorrido. Un camino es "independiente" si no es combinación de los otros — no significa que sean todos los caminos posibles del programa (eso sería explosivo con bucles o decisiones anidadas), sino el conjunto **mínimo** que, combinado, genera cualquier otro camino posible.
4. **Diseñar un caso de prueba por cada camino** del conjunto base, eligiendo datos de entrada concretos que fuercen la ejecución de ese camino específico.

### Por qué garantiza cobertura con el mínimo esfuerzo

El teorema de McCabe dice que `V(G)` es simultáneamente:
- el número de caminos en el conjunto base, y
- una cota superior segura: ejecutando esos `V(G)` caminos, **cada decisión del código queda evaluada en ambos sentidos (verdadero y falso) al menos una vez** — es decir, el conjunto base garantiza cobertura de decisión completa (branch coverage 100%) sin necesidad de enumerar todos los caminos posibles del programa, que en funciones con bucles o condiciones anidadas pueden ser infinitos o exponenciales.

Esto es lo que separa esta técnica de simplemente "escribir tests hasta que parezca suficiente": da una cota objetiva y verificable (`V(G)`) de cuántos casos hacen falta como mínimo, y un método sistemático (seguir las aristas del grafo) para no dejar ningún camino de decisión sin probar.

<a id="justificacion-teorica-aplicacion"></a>
## Justificación teórica de la aplicación a `autorregistrar_estudiante`

Elegimos esta función como primer ejemplo por tres razones:

1. **Ya está en nuestra tabla de complejidad ≥3** (complejidad 4, sección anterior) — es uno de los procesos que el propio análisis de McCabe identificó como candidato a probar formalmente, en vez de elegir una función al azar.
2. **Sus decisiones son reglas de negocio reales, no detalles de implementación**: cada uno de los 3 `if` de la función corresponde a una validación de negocio distinta (contraseñas coincidentes, unicidad de email, unicidad de legajo) que ya tiene su propia excepción de dominio (`ContrasenasNoCoincidenceError`, `EmailYaRegistradoError`, `LegajoYaRegistradoError`). Esto significa que los caminos básicos que va a producir el método **no son artificios de cobertura de código** — coinciden exactamente con los escenarios que un analista de QA diseñaría manualmente mirando solo los requisitos. Es la prueba de que la métrica de complejidad, bien aplicada, encuentra los mismos casos de prueba que el análisis funcional, pero de forma sistemática y verificable.
3. **Es estructuralmente simple** (sin bucles, sin anidamiento de más de un nivel): el grafo de flujo tiene una sola cadena de decisiones secuenciales, ideal como primer ejemplo antes de aplicar la técnica a funciones con más complejidad (`iniciar_postulacion` o `validar_documento`, ambas con V(G)=6), donde el conjunto base de caminos es más difícil de enumerar a simple vista.

<a id="aplicacion-practica"></a>
## Aplicación práctica

### Código y sus puntos de decisión (recordatorio de la sección anterior)

```python
def autorregistrar_estudiante(*, email, password1, password2, ...):
    if password1 != password2:                                    # D1
        raise ContrasenasNoCoincidenceError(...)
    if Usuario.objects.filter(email=email).exists():               # D2
        raise EmailYaRegistradoError(...)
    if PerfilEstudiante.objects.filter(legajo=legajo).exists():     # D3
        raise LegajoYaRegistradoError(...)
    usuario = Usuario.objects.create_user(...)                      # camino feliz
    PerfilEstudiante.objects.create(...)
    usuario.groups.add(Group.objects.get(name="Estudiante"))
    return usuario
```

### 1. Grafo de flujo

| Nodo | Representa |
|---|---|
| N1 | Entrada de la función |
| N2 | Decisión D1: `password1 != password2` |
| N3 | `raise ContrasenasNoCoincidenceError` |
| N4 | Decisión D2: `Usuario.objects.filter(email=...).exists()` |
| N5 | `raise EmailYaRegistradoError` |
| N6 | Decisión D3: `PerfilEstudiante.objects.filter(legajo=...).exists()` |
| N7 | `raise LegajoYaRegistradoError` |
| N8 | Camino feliz: crear `Usuario` + `PerfilEstudiante` + asignar grupo + `return` |
| N9 | Salida (todas las ramas convergen acá) |

```
N1 → N2 ──(Sí)──→ N3 ──────────────────────┐
      │(No)                                │
      ▼                                     │
     N4 ──(Sí)──→ N5 ─────────────────────┐ │
      │(No)                               │ │
      ▼                                    │ │
     N6 ──(Sí)──→ N7 ───────────────────┐  │ │
      │(No)                             │  │ │
      ▼                                  ▼  ▼ ▼
     N8 ─────────────────────────────→  N9 (SALIDA)
```

Aristas (E): N1→N2, N2→N3, N2→N4, N4→N5, N4→N6, N6→N7, N6→N8, N3→N9, N5→N9, N7→N9, N8→N9 → **E = 11**
Nodos (N): N1…N9 → **N = 9**

### 2. Cálculo de V(G)

> V(G) = E − N + 2P = 11 − 9 + 2(1) = **4**

Coincide exactamente con el valor que `ruff` reportó por conteo de decisiones (D=3, V(G)=D+1=4) — confirma que el grafo está bien construido.

### 3. Conjunto base de caminos independientes

| # | Camino (nodos) | Condición que fuerza |
|---|---|---|
| **C1** (camino feliz) | N1→N2(No)→N4(No)→N6(No)→N8→N9 | Contraseñas iguales, email no registrado, legajo no registrado |
| **C2** | N1→N2(Sí)→N3→N9 | Contraseñas distintas |
| **C3** | N1→N2(No)→N4(Sí)→N5→N9 | Contraseñas iguales, email ya registrado |
| **C4** | N1→N2(No)→N4(No)→N6(Sí)→N7→N9 | Contraseñas iguales, email libre, legajo ya registrado |

Cada camino introduce exactamente una arista no usada por los anteriores (C2 introduce N2→N3; C3 introduce N4→N5; C4 introduce N6→N7), cumpliendo la condición de independencia lineal. Con estos 4 casos, **las 3 decisiones quedan evaluadas en Sí y en No al menos una vez** → cobertura de decisión 100%.

### 4. Casos de prueba derivados

| Caso | Entrada relevante | Resultado esperado |
|---|---|---|
| C1 | `password1=password2="Segura123!"`, `email` nuevo, `legajo` nuevo | Se crea `Usuario` + `PerfilEstudiante`, queda en grupo `Estudiante` |
| C2 | `password1="Segura123!"`, `password2="Diferente999!"` | `ContrasenasNoCoincidenceError` |
| C3 | contraseñas iguales, `email` ya existente en la BD | `EmailYaRegistradoError` |
| C4 | contraseñas iguales, `email` nuevo, `legajo` ya existente en la BD | `LegajoYaRegistradoError` |

### 5. Verificación contra los tests reales

El archivo `apps/acceso/tests/test_services.py` ya tiene, sin que lo hayamos planeado así, una función de test por cada camino del conjunto base:

| Camino básico | Test existente |
|---|---|
| C1 | `test_autorregistrar_estudiante_exitoso` |
| C2 | `test_autorregistrar_estudiante_contrasenas_distintas` |
| C3 | `test_autorregistrar_estudiante_email_duplicado` |
| C4 | `test_autorregistrar_estudiante_legajo_duplicado` |

**Conclusión:** `autorregistrar_estudiante` ya tiene cobertura de camino básico completa (4/4) — el análisis formal confirma con una técnica de caja blanca lo que el equipo había logrado de forma intuitiva al testear cada regla de negocio por separado.

---

<a id="analisis-sonarqube"></a>
# Análisis con SonarQube

<a id="sonar-objetivo"></a>
## Objetivo

Validar con una herramienta de análisis estático independiente (distinta de `ruff`) los números de complejidad ciclomática ya calculados, y cruzar esos datos con la cobertura real de los 4 casos de prueba de camino básico diseñados para `autorregistrar_estudiante`. Toda esta guía se ejecutó en local sobre este proyecto — los comandos y resultados de abajo son reales, no hipotéticos.

Herramienta: **SonarQube Community Edition**, corrida 100% en Docker, sin tocar `docker-compose.yml` del proyecto (es un análisis puntual, no un servicio permanente del stack).

<a id="sonar-paso-1"></a>
## Paso 1 — Levantar SonarQube Community Edition (local, Docker)

```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
```

Requiere ~2GB de RAM libres (este equipo tenía 7.9GB asignados a Docker con ~1.5GB ya en uso por el stack del proyecto — sobra margen). Esperar a que el endpoint de salud responda `"status":"UP"` (tarda 1-2 minutos, levanta Elasticsearch internamente):

```bash
curl -s http://localhost:9000/api/system/status
# {"id":"...","version":"26.6.0.123539","status":"UP"}
```

<a id="sonar-paso-2"></a>
## Paso 2 — Crear proyecto y token de autenticación

SonarQube viene con usuario `admin`/`admin` y obliga a cambiar la contraseña en el primer uso. Se puede hacer todo por API, sin pasar por la interfaz web:

```bash
# Cambiar password por defecto
curl -s -u admin:admin -X POST "http://localhost:9000/api/users/change_password" \
  --data-urlencode "login=admin" \
  --data-urlencode "previousPassword=admin" \
  --data-urlencode "password=<password-nueva>"

# Crear el proyecto
curl -s -u admin:<password-nueva> -X POST "http://localhost:9000/api/projects/create" \
  --data-urlencode "name=Sistema de Gestion de Becas Universitarias" \
  --data-urlencode "project=becas-universitarias"

# Generar un token para el scanner (no usar la password directamente)
curl -s -u admin:<password-nueva> -X POST "http://localhost:9000/api/user_tokens/generate" \
  --data-urlencode "name=scanner-token-cli"
# devuelve: {"login":"admin","name":"scanner-token-cli","token":"squ_xxxxxxxx...", ...}
```

<a id="sonar-paso-3"></a>
## Paso 3 — Generar reporte de cobertura local

SonarQube no ejecuta los tests — necesita que `pytest` ya haya corrido y haya dejado un reporte de cobertura en XML (formato `coverage.py`, que `sonar-python` entiende de forma nativa). El proyecto no tenía `coverage`/`pytest-cov` instalado, así que se agregó de forma temporal dentro del contenedor `web` (no se modificó `requirements.txt`; si se quiere dejar de forma permanente, agregar `pytest-cov` a la sección de dependencias de desarrollo):

```bash
docker compose exec web pip install coverage
docker compose exec web coverage run -m pytest -q
docker compose exec web coverage xml -o coverage.xml
```

Resultado real obtenido (51 tests, todo el proyecto):

```
51 passed in 32.47s
Wrote XML report to coverage.xml
```

`coverage.xml` queda en la raíz del proyecto (el bind mount de Docker lo refleja directo en el filesystem del host). Está agregado a `.gitignore` — es un artefacto generado, no se commitea.

<a id="sonar-paso-4"></a>
## Paso 4 — Configurar `sonar-project.properties`

Archivo creado en la raíz del proyecto (`sonar-project.properties`):

```properties
sonar.projectKey=becas-universitarias
sonar.projectName=Sistema de Gestion de Becas Universitarias
sonar.sources=apps,config
sonar.exclusions=**/migrations/**,**/tests/**
sonar.tests=apps
sonar.test.inclusions=**/tests/**
sonar.python.version=3.12
sonar.python.coverage.reportPaths=coverage.xml
sonar.sourceEncoding=UTF-8
```

`sonar.python.coverage.reportPaths` es la línea que conecta el `coverage.xml` del Paso 3 con el análisis — sin ella, SonarQube mediría complejidad y code smells, pero no cobertura real.

<a id="sonar-paso-5"></a>
## Paso 5 — Ejecutar el scanner

Se usa la imagen oficial `sonarsource/sonar-scanner-cli`, montando el proyecto en `/usr/src` (convención de esa imagen) y apuntando a SonarQube vía `host.docker.internal` (para que el contenedor del scanner alcance el contenedor de SonarQube publicado en el puerto 9000 del host):

```bash
docker run --rm \
  -v "<ruta-del-proyecto>:/usr/src" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.host.url=http://host.docker.internal:9000 \
  -Dsonar.token=<token-generado-en-paso-2>
```

Salida real (resumida):

```
INFO  25 source files to be analyzed
INFO  25/25 source files have been analyzed
INFO  ANALYSIS SUCCESSFUL, you can find the results at: http://host.docker.internal:9000/dashboard?id=becas-universitarias
INFO  EXECUTION SUCCESS
INFO  Total time: 1:02.828s
```

<a id="sonar-paso-6"></a>
## Paso 6 — Consultar resultados (API y dashboard)

El análisis se procesa de forma asíncrona en el servidor (Compute Engine). Se puede consultar el estado del procesamiento y luego las métricas, todo vía API (o entrando a `http://localhost:9000/dashboard?id=becas-universitarias` desde el navegador):

```bash
# Confirmar que el servidor terminó de procesar el reporte subido
curl -s -u admin:<password-nueva> "http://localhost:9000/api/ce/task?id=<id-de-la-tarea>"

# Métricas puntuales del archivo de ejemplo
curl -s -u admin:<password-nueva> \
  "http://localhost:9000/api/measures/component?component=becas-universitarias:apps/acceso/services.py&metricKeys=complexity,cognitive_complexity,coverage,line_coverage,code_smells,duplicated_lines_density,ncloc"

# Quality Gate del proyecto completo
curl -s -u admin:<password-nueva> "http://localhost:9000/api/qualitygates/project_status?projectKey=becas-universitarias"
```

<a id="sonar-resultados"></a>
## Resultados obtenidos sobre `autorregistrar_estudiante`

`apps/acceso/services.py` contiene únicamente esta función, así que la métrica a nivel archivo equivale a la métrica de la función:

| Métrica | Valor reportado por SonarQube | Comparación |
|---|---|---|
| **Complexity** (ciclomática) | **4** | Coincide exactamente con `ruff`/mccabe y con el cálculo manual del grafo de flujo (V(G)=4) de la sección de [prueba de camino básico](#aplicacion-practica) |
| **Cognitive Complexity** | **3** | Menor que la ciclomática — esperable, porque las 3 decisiones de la función son secuenciales (ningún `if` anidado dentro de otro), y la complejidad cognitiva solo penaliza extra por anidamiento |
| **Coverage** | **100.0%** | Confirma de forma objetiva que los 4 casos de prueba de camino básico (C1-C4) cubren el 100% de las líneas, no es una inferencia manual |
| **Line Coverage** | **100.0%** | Idem |
| **Code Smells** | **0** | Sin advertencias de mantenibilidad sobre esta función |
| **Duplicated Lines Density** | **0.0%** | Sin duplicación de código |
| **Lines of Code (ncloc)** | **32** | — |
| **Quality Gate del proyecto** | **OK** | `{"status":"OK","conditions":[],"caycStatus":"compliant"}` |

**Conclusión del análisis:** SonarQube confirma de forma independiente tanto el valor de complejidad ciclomática (4) calculado con `ruff` y con el grafo de flujo manual, como la cobertura completa (100%) que predijo el análisis de caminos básicos al mapear los 4 caminos del conjunto base contra los 4 tests existentes. La complejidad cognitiva (3 < 4) es información adicional que `ruff` no provee: indica que, aunque la función tiene 4 caminos de ejecución, su lectura es relativamente simple porque no hay anidamiento — lo cual es consistente con haberla elegido como primer ejemplo de la técnica.

<a id="sonar-limpieza"></a>
## Detener el entorno local

SonarQube no forma parte del stack permanente del proyecto (no está en `docker-compose.yml`); quedó corriendo como contenedor suelto para esta guía. Para liberar los recursos:

```bash
docker stop sonarqube
docker rm sonarqube
```

El dashboard deja de estar disponible al borrar el contenedor; los valores ya quedaron documentados en la tabla de resultados de esta sección. Si se quiere volver a analizar el proyecto más adelante (por ejemplo, después de escribir los casos de prueba de camino básico para `iniciar_postulacion` o `validar_documento`), basta repetir los Pasos 1 a 6 — el `sonar-project.properties` ya queda commiteado en el repo.
