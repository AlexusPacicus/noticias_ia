# Contrato de Sistema (Documento de Gobernanza Humana)

---

## 1. Propósito

### 1.1 Objetivo del Sistema

Dado un `query` y un `time_window`, el sistema selecciona y resume ítems recientes sobre IA a partir de fuentes reales y cerradas, produciendo un resultado **determinista, reproducible y contractual**.

El sistema prioriza y selecciona ítems mediante reglas mecánicas; el uso de LLM se limita a resumen de texto.

### 1.2 Delta explícito v1 respecto a v0

**v1 introduce:**

- Conexión a fuentes reales.
- Normalización efectiva de ítems (schema, deduplicación, fechas).
- Activación real de `published_at` como criterio principal de ranking.

**v1 mantiene sin cambios:**

- Contrato I/O.
- Ranking determinista (criterios y orden).
- Orden del pipeline.
- Rol no decisional del LLM.
- Condiciones de estabilidad como gate de avance.

### 1.3 Intención de diseño

v1 tiene el objetivo de corregir el error de diseño del nodo normalizado, el cual asumió demasiadas responsabilidades, y probar la arquitectura con datos reales.

En esta versión se realizará la recolección de datos de una única fuente (arXiv), para de esta forma comprobar la aparición de bugs básicos.

### 1.4 No-objetivos

No es objetivo de v1:

- Optimizar relevancia o cobertura.
- Evaluar calidad científica o impacto.
- Detectar tendencias o patrones.
- Introducir scoring semántico, embeddings o ML.
- Ajustar el sistema mediante feedback.
- Corregir, reinterpretar o "mejorar" outputs del LLM.

---

## 2. Alcance funcional

### 2.1 Qué hace

- Consulta fuentes reales, cerradas y versionadas.
- Normaliza ítems de forma mecánica y determinista:
  - schema
  - deduplicación
  - fechas (`published_at` o `NULL`)
- Prioriza ítems con ranking determinista (sin LLM).
- Selecciona top-K resultados.
- Genera resúmenes descriptivos mediante LLM como transformador de texto.
- Valida estrictamente el schema de salida; si falla → **ABORT**.
- Devuelve un conjunto y orden reproducibles.

### 2.2 Qué NO hace

- Evaluar relevancia, calidad, impacto o novedad.
- Detectar tendencias, comparativas o rankings "inteligentes".
- Permitir que el LLM filtre, reordene o descarte ítems.
- Corregir, reintentar o "arreglar" salidas inválidas del LLM.
- Degradar silenciosamente: ante violación → **ABORT**.

---

## 3. Invariantes del sistema

### 3.1 Determinismo

A igualdad de input y estado de fuentes, el sistema produce:

- El mismo conjunto de ítems.
- En el mismo orden.

La única variación permitida es la redacción de los campos generados por el LLM.

> **Nota de determinismo temporal:**
>
> El determinismo del sistema v1 se garantiza únicamente a igualdad de:
>
> - input del usuario
> - artefactos exógenos versionados
> - snapshot temporal de la fuente
>
> El sistema **no** garantiza determinismo inter-ejecución si la fuente externa modifica su contenido o metadatos.

### 3.2 Orden del pipeline

El pipeline se ejecuta en orden fijo y total. Ningún nodo puede:

- Saltarse pasos.
- Reordenar nodos.
- Reejecutar nodos anteriores.

Alterar el orden del pipeline constituye **violación contractual**.

### 3.3 Inmutabilidad de decisiones

Las decisiones tomadas en un nodo:

- No pueden ser reinterpretadas.
- No pueden ser corregidas por nodos posteriores.

Ejemplos:

- `rank` no puede verse afectado por `summarize`.
- `select` no puede ser alterado después de ejecutarse.

### 3.4 Uso del LLM

El LLM:

- Solo opera en el nodo `summarize`.
- Actúa exclusivamente como transformador de texto.
- No tiene acceso a contexto externo ni a decisiones previas.

El output del LLM es válido solo si cumple el schema contractual. Cualquier incumplimiento → **ABORT** total.

### 3.5 Validación estricta

- Todo input y output intermedio debe cumplir su contrato antes de avanzar.
- El sistema no aplica correcciones automáticas.
- No existen degradaciones silenciosas.

### 3.6 Manejo de errores

Ante cualquier violación contractual o error no contemplado:

- La ejecución se detiene.
- No se devuelven resultados parciales.
- El sistema falla de forma explícita y trazable.

### 3.7 Versionado

Cambiar:

- invariantes,
- orden del pipeline,
- rol del LLM,

implica **nueva versión** del sistema.

---

## 4. Contrato I/O (v1 — integrado)

### 4.1 Input (usuario)

| Campo         | Tipo              | Restricción                                     |
|---------------|-------------------|-------------------------------------------------|
| `query`       | `string`          | Mín. 2 palabras; sin operadores                 |
| `time_window` | `enum` (cerrado)  | `last_24h` \| `last_3_days` \| `last_7_days`    |
| `top_k`       | `int` (opcional)  | Rango `[1..10]`, default `5`                    |

**Reglas:**

- Validación previa a cualquier llamada externa.
- Cualquier violación → **ABORT**.

### 4.2 Configuración del sistema (fuera del input)

- Conjunto cerrado y versionado de fuentes.
- No modificable en runtime.
- Cambios → nueva versión.
- A igualdad de input y configuración, el resultado es determinista.

### 4.3 Output (schema cerrado)

```json
{
  "topic": "string",
  "time_window": "string",
  "generated_at": "datetime",
  "results": [
    {
      "kind": "paper | news | release",
      "title": "string",
      "idea_clave": "string (≤ 80 palabras)",
      "por_que_importa": "string (≤ 30 palabras)",
      "link": "string (único)"
    }
  ]
}
```

**Reglas:**

- Máx. `top_k` resultados.
- Orden contractual (derivado del ranking).
- Resúmenes descriptivos; sin opinión ni comparativa.
- Enlace canónico único.

### 4.4 Compatibilidad

- Compatible con v0 en estructura I/O.
- Ajustes de longitud no cambian semántica.
- Cambios estructurales → versión mayor.

### 4.5 Errores de I/O (ABORT)

| Código                      | Descripción                         |
|-----------------------------|-------------------------------------|
| `INVALID_QUERY`             | Query no cumple formato requerido   |
| `INVALID_TIME_WINDOW`       | Ventana temporal fuera de enum      |
| `INVALID_TOP_K`             | Valor fuera de rango `[1..10]`      |
| `EMPTY_RESULTS`             | Sin resultados tras pipeline        |
| `INVALID_KIND`              | Tipo de ítem no reconocido          |
| `SUMMARY_SCHEMA_VIOLATION`  | Schema de resumen no cumplido       |

---

## 5. Uso de modelos (LLM)

### 5.1 Alcance

El sistema utiliza un LLM únicamente en el nodo `summarize`. El LLM actúa exclusivamente como transformador de texto.

### 5.2 Prohibiciones explícitas

El LLM **no puede**:

- Participar en ranking, selección o filtrado.
- Introducir scoring, relevancia, impacto o comparativas.
- Acceder a contexto externo o a otros ítems.
- Reordenar resultados.
- Corregir, reintentar o "mejorar" su propia salida.

Cualquier intento de lo anterior constituye **violación contractual**.

### 5.3 Contrato de salida del LLM

El output del LLM es válido solo si cumple el schema contractual.

Validaciones:

- Campos presentes.
- Tipos correctos.
- Límites de longitud.
- No hay post-procesado semántico.

### 5.4 Manejo de errores

- Si el output no cumple el schema → `SUMMARY_SCHEMA_VIOLATION`.
- Ante error → **ABORT** total, sin resultados parciales.
- No existen retries inteligentes ni degradación silenciosa.

### 5.5 Invariante

El LLM no aporta criterio al sistema. Si se elimina el LLM, el conjunto y orden de resultados permanecen idénticos.

---

## 6. Artefactos exógenos (v1)

### 6.1 Principio

El sistema depende de un conjunto cerrado, explícito y versionado de artefactos exógenos.

Los artefactos exógenos:

- No son input del usuario.
- No son configurables en runtime.
- Son de solo lectura.
- Cambian exclusivamente mediante nueva versión del sistema.

### 6.2 Artefactos definidos (v1)

**Fuentes permitidas — Fuente primaria única:**

| Fuente | Categoría |
|--------|-----------|
| arXiv  | `cs.AI`   |

Este listado constituye un artefacto exógeno versionado.

### 6.3 Exclusiones explícitas

Quedan fuera de alcance en v1:

- Cualquier otra categoría de arXiv.
- Blogs oficiales.
- Medios periodísticos.
- Agregadores, newsletters y redes sociales.
- Fuentes dinámicas o no versionadas.

### 6.4 Invariante

A igualdad de input y artefactos exógenos, el sistema produce resultados deterministas y reproducibles.

### 6.5 Regla de cambio

Cualquier modificación en los artefactos exógenos implica:

- Actualización explícita del contrato.
- Nueva versión del sistema.

No existen excepciones temporales.

---

## 7. Pipeline contractual

### 7.1 Orden del pipeline (inmutable)

```
collect_input
  → validate_input
    → fetch
      → normalize_schema
        → normalize_dedupe
          → normalize_dates
            → rank
              → select
                → summarize
```

Este orden es **total y obligatorio**.

### 7.2 Responsabilidad por nodo (mínima)

| Nodo               | Responsabilidad                                                        |
|--------------------|------------------------------------------------------------------------|
| `collect_input`    | Ingesta del input bruto del usuario.                                   |
| `validate_input`   | Validación del contrato de input y aplicación de defaults.             |
| `fetch`            | Obtención de ítems desde las fuentes definidas como artefactos exógenos.|
| `normalize_schema` | Garantiza presencia y tipo de campos contractuales.                    |
| `normalize_dedupe` | Eliminación determinista de duplicados.                                |
| `normalize_dates`  | Determinar un único campo `published_at` por ítem (ver reglas abajo). |
| `rank`             | Ordenación determinista según criterios contractuales.                 |
| `select`           | Selección de los `top_k` ítems según ranking.                          |
| `summarize`        | Generación de resúmenes descriptivos mediante LLM.                     |

**Reglas de `normalize_dates`:**

- Si existe una única fecha parseable → usarla.
- Si existen múltiples fechas → aplicar prioridad fija:
  1. `published`
  2. `updated`
  3. `submitted`
- Si ninguna fecha es parseable → `published_at = NULL`.

**No se permite:**

- Inferencia semántica.
- Heurísticas implícitas.
- Uso de contexto externo.

### 7.3 Reglas contractuales

Ningún nodo puede:

- Reordenar el pipeline.
- Saltarse pasos.
- Reinterpretar decisiones previas.

Un nodo solo consume outputs validados del nodo anterior.

Alterar el número de nodos, su orden o su responsabilidad implica **nueva versión** del sistema.

### 7.4 Invariante

El pipeline define el comportamiento completo del sistema. Cualquier ejecución que no siga este orden es **inválida**.

---

## 8. Aborts generales del sistema

Este apartado define condiciones bajo las cuales el flujo v1 se considera inválido como sistema gobernado, independientemente de que pueda ejecutarse correctamente o producir resultados.

Estos aborts **no** describen errores operativos, **no** se evalúan en runtime y **no** prescriben comportamiento de ejecución; su función es delimitar los límites de validez del flujo como referencia estable.

Los contratos específicos pueden declarar causas concretas siempre que estén explícitamente adscritas a un abort general, sin introducir nuevas clases de invalidez.

---

### Abort 1 — Pérdida de determinismo estructural

- **Premisa:** El flujo v1 es estructuralmente determinista ante entradas y artefactos versionados idénticos.
- **Violación:** Cualquier variación no controlada en el conjunto o el orden de los ítems, incluida la dependencia de inferencias, supuestos implícitos o criterios no expresados contractualmente, así como la derivada de transformaciones intermedias declaradas en contratos específicos.
- **Consecuencia:** El flujo se considera no reproducible ni auditable y queda invalidado como referencia estable en v1.

### Abort 2 — Asunción de criterio por parte del LLM

- **Premisa:** El LLM opera exclusivamente como transformador textual, sin capacidad para decidir, evaluar, inferir ni mejorar la estructura del resultado.
- **Violación:** El LLM introduce decisiones o modificaciones estructurales (inclusión, exclusión, priorización, orden, inferencia o mejora implícita), incluidas aquellas declaradas como causas específicas en contratos particulares. Quedan excluidas las transformaciones textuales explícitamente declaradas y acotadas por contrato (p. ej., generación de resúmenes en campos predefinidos).
- **Consecuencia:** El flujo pierde gobernanza y la separación entre criterio humano y ejecución automática, quedando invalidado como referencia estable en v1.

### Abort 3 — Acoplamiento semántico entre componentes

- **Premisa:** Los componentes del flujo interactúan únicamente mediante el estado y contratos explícitos, sin dependencia de decisiones internas de otros componentes.
- **Violación:** Un componente requiere conocer, inferir o asumir decisiones internas, criterios o estados no contractuales de otro componente para operar correctamente.
- **Consecuencia:** El flujo pierde composabilidad y versionado estable, quedando invalidado como referencia gobernable en v1.

### Abort 4 — Imposibilidad de validación ex-post

- **Premisa:** La corrección del output del flujo puede evaluarse únicamente contra el contrato de salida, sin conocimiento de la ejecución interna.
- **Violación:** Determinar si el resultado es correcto requiere inspeccionar decisiones internas, pasos intermedios o razonamiento no expresado en el output contractual, aunque el comportamiento sea determinista.
- **Consecuencia:** El flujo deja de ser auditable y no puede considerarse una referencia estable en v1.

### Abort 5 — Ambigüedad de responsabilidad

- **Premisa:** Cada componente del flujo tiene un rol único, explícito y no solapado.
- **Violación:** Un componente asume múltiples responsabilidades, responsabilidades implícitas o un rol no delimitado contractualmente.
- **Consecuencia:** El flujo pierde gobernanza y previsibilidad, quedando invalidado como referencia estable en v1.

---

## 9. Tests y gates (validez de versión)

Este apartado **no** define tests técnicos ni unitarios. Define las condiciones contractuales que determinan si v1 es una versión válida, cerrable y congelable.

Los tests y gates:

- No evalúan calidad funcional ni utilidad.
- No miden rendimiento ni cobertura.
- No validan "si funciona bien".
- Solo determinan si la versión puede declararse válida como referencia estable v1.

### 9.1 Naturaleza de los tests

Los tests definidos en este punto:

- Son tests de **validez contractual**, no de implementación.
- Se evalúan sobre:
  - input
  - output
  - artefactos exógenos
  - comportamiento observable del flujo
- Producen un resultado binario: **VÁLIDO / INVÁLIDO** como versión v1.

Un test fallido no implica bug: implica **versión no válida**.

### 9.2 Qué invalida la versión v1

La versión v1 queda invalidada como referencia estable si ocurre cualquiera de las siguientes condiciones:

1. El conjunto u orden de resultados no es determinista a igualdad de input y artefactos.
2. El LLM introduce criterio, inferencia o modificación estructural.
3. El comportamiento del sistema no puede evaluarse solo desde el output contractual.
4. Existen decisiones implícitas no descritas en el contrato.
5. El pipeline ejecutado no coincide exactamente con el pipeline contractual.
6. El sistema degrada silenciosamente ante errores.
7. Se requiere inspección interna para justificar corrección.

Cualquiera de estos puntos activa un **abort general** y v1 queda invalidada.

### 9.3 Gates de cierre de versión

Los gates determinan si v1 puede cerrarse y congelarse.

- No son automáticos.
- No son interpretativos.
- Son criterios explícitos de decisión humana.

---

**Gate A — Consistencia contractual**

- **Condición:** El comportamiento observado del sistema está completamente descrito por este contrato.
- **Si falla →** Abort 4.

**Gate B — Determinismo**

- **Condición:** Mismo input + mismos artefactos → mismo conjunto y orden de resultados en ejecuciones repetidas.
- **Si falla →** Abort 1.

**Gate C — Rol del LLM**

- **Condición:** Eliminar el LLM no altera selección, ranking ni orden. El LLM solo afecta a campos textuales descriptivos.
- **Si falla →** Abort 2.

**Gate D — Cierre v1**

- **Condición:**
  - Artefactos exógenos cerrados y versionados.
  - Pipeline congelado.
  - Contrato actualizado refleja límites reales, no aspiracionales.
  - Tests y gates documentados.
- **Si pasa →** v1 **FROZEN**.

### 9.4 Regla de avance

- Mientras cualquier gate esté fallido, **no existe v1**.
- Añadir fuentes, lógica o excepciones sin nueva versión invalida v1.
- v1 no se "mejora": se sustituye por v2.

---

## 10. Estado del contrato

Este apartado define el estado formal del contrato del sistema.

### 10.1 Versión del contrato

- **Versión:** v1
- **Alcance:** definido íntegramente en este documento.
- La versión v1 es auto-contenida y no depende de documentación externa no referenciada.

### 10.2 Estado actual

- **Estado del contrato:** **FROZEN**

### 10.3 Efectos del estado FROZEN

- El contrato v1 constituye una referencia estable del sistema.
- No se permiten modificaciones:
  - de invariantes
  - del pipeline
  - del rol del LLM
  - de los artefactos exógenos
- sin incremento explícito de versión.

### 10.4 Regla de cambio de estado

- Cualquier modificación del contenido de este contrato invalida el estado FROZEN.
- Los cambios deberán introducirse exclusivamente mediante una nueva versión (v2).
