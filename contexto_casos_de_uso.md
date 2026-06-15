# Contexto de Casos de Uso — Sistema de Gestión de Becas Universitarias

## Actores del sistema

| Actor | Tipo | Acceso |
|---|---|---|
| Director | Humano | Total |
| Operador | Humano | Alto |
| Estudiante | Humano | Básico |
| Sistema | No humano (temporizador) | Interno |

## Catálogo completo de Casos de Uso

| ID | Caso de Uso | Actor | RF | Prioridad | Paquete |
|---|---|---|---|---|---|
| CU01 | Autenticarse en el Sistema | Todos | RF01 | Alta | P1 Acceso y Seguridad |
| CU02 | Cerrar Sesión | Todos | RF01 | Alta | P1 Acceso y Seguridad |
| CU03 | Autorregistrarse como Estudiante | Estudiante | RF03 | Alta | P1 Acceso y Seguridad |
| CU04 | Registrar Usuario | Director | RF03 | Alta | P2 Admin Usuarios |
| CU05 | Modificar Usuario | Director | RF03 | Alta | P2 Admin Usuarios |
| CU06 | Dar de Baja Usuario | Director | RF03 | Alta | P2 Admin Usuarios |
| CU07 | Asignar Rol a Usuario | Director | RF02, RF03 | Alta | P2 Admin Usuarios |
| CU08 | Gestionar Roles y Permisos | Director | RF02 | Alta | P2 Admin Usuarios |
| CU09 | Gestionar Convocatoria | Operador | RF04 | Alta | P3 Convocatorias |
| CU10 | Publicar Convocatoria | Operador | RF04 | Alta | P3 Convocatorias |
| CU11 | Cerrar Convocatoria | Sistema (temporizador) | RF04 | Alta | P3 Convocatorias |
| CU12 | Gestionar Becas | Operador | RF05 | Alta | P3 Convocatorias |
| CU13 | Gestionar Requisitos | Operador | RF06 | Alta | P3 Convocatorias |
| CU14 | Asociar Requisitos a Convocatoria | Operador | RF06, RF04 | Alta | P3 Convocatorias |
| CU15 | Configurar Criterios y Ponderación | Director | RF11 | Alta | P4 Config Socioeconómica |
| CU16 | Completar Formulario Socioeconómico | Estudiante | RF08 | Alta | P5 Postulación |
| CU17 | Registrar Postulación | Estudiante | RF07 | Alta | P5 Postulación |
| CU18 | Verificar Identidad del Postulante | Operador | RF09 | Alta | P5 Postulación |
| CU19 | Validar Documentación Física | Operador | RF09 | Alta | P5 Postulación |
| CU20 | Digitalizar Documentación | Operador | RF09 | Media | P5 Postulación |
| CU21 | Consultar Postulaciones | Operador / Director | RF07 | Alta | P5 Postulación |
| CU22 | Consultar Estado de mi Postulación | Estudiante | RF07 | Alta | P5 Postulación |
| CU23 | Procesar Formularios Socioeconómicos | Operador | RF12 | Media | P7 Procesamiento |
| CU24 | Generar Ranking | Operador | RF13 | Media | P7 Procesamiento |
| CU25 | Exportar Ranking | Director / Operador | RF14 | Baja | P7 Procesamiento |
| CU26 | Visualizar Dashboard de Reportes | Director | RF15 | Media | P7 Procesamiento |
| CU27 | Notificar Avance de Postulación | Sistema → Estudiante | RF10 | Media | P6 Notificaciones |

## Relaciones entre CU

### «include» (inclusión obligatoria)

- CU04 → CU07 (Registrar Usuario incluye Asignar Rol)
- CU10 → CU14 (Publicar Convocatoria incluye Asociar Requisitos)
- CU11 → CU27 (Cerrar Convocatoria incluye Notificar)
- CU17 → CU16 (Registrar Postulación incluye Completar Formulario)
- CU18 → CU27 (Verificar Identidad incluye Notificar)
- CU19 → CU20 (Validar Documentación incluye Digitalizar)
- CU19 → CU27 (Validar Documentación incluye Notificar)
- CU24 → CU23 (Generar Ranking incluye Procesar Formularios)

### «extend» (extensión condicional)

- CU10 → CU09 (Publicar extiende Gestionar Convocatoria)
- CU25 → CU24 (Exportar Ranking extiende Generar Ranking)

## Estados de la Postulación

```
[Borrador] → [Enviada] → [En Revisión] → [Aprobada] → [Procesada] → [Adjudicada | No Adjudicada | Lista de Espera]
                ↓             ↓               ↓
        [Rechazada -    [Rechazada -    [Rechazada -
        No Presentación] Identidad]    Documentación]
```

## Reglas de negocio clave

- Un estudiante solo puede tener **una postulación activa** a la vez.
- Si una postulación es rechazada y la convocatoria sigue vigente, el estudiante puede **re-postular**.
- El formulario socioeconómico es **único por estudiante** y reutilizable.
- El cierre de convocatoria es **automático** al vencer la fecha.
- La validación documental es **presencial**, sin estado de "observada" (binario: Aprobada/Rechazada).
- Solo se **digitaliza documentación aprobada** (optimización de almacenamiento).
- Pueden coexistir **múltiples convocatorias activas** simultáneamente.

## Paquetes funcionales y dependencias

| Paquete | Depende de |
|---|---|
| P1 Acceso y Seguridad | — (base) |
| P2 Admin Usuarios | P1 |
| P3 Convocatorias y Catálogos | P1 |
| P4 Config Socioeconómica | P2 |
| P5 Postulación y Documentación | P1, P3, P4 |
| P6 Notificaciones | P2, P5 |
| P7 Procesamiento, Ranking y Reportes | P2, P3, P4, P5 |

## CU con análisis profundo (comunicación + secuencia)

CU01, CU11, CU17, CU18, CU19, CU20, CU23, CU24 — los arquitectónicamente significativos. Los CU CRUD restantes siguen el patrón base.
