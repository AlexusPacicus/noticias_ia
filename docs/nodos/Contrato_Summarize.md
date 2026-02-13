# Contrato de Nodo — `summarize`

---

## 1. Propósito

Generar, para cada elemento de `selected_items`, exactamente dos campos textuales (`idea_clave`, `relacion_con_query`) usando un LLM exclusivamente como transformador de texto. Construir el `output` contractual del sistema.

---

## 2. Lecturas permitidas (State)

- `selected_items` (obligatorio).
- `input_validated` (acceso a `query`, `time_window`).

**Lecturas prohibidas:**

- `ranked_items`
- `normalized_items`
- `external_units`
- `abort_reason`
- Cualquier campo no listado en el State v1.
- Artefactos exógenos, red o filesystem.

**Restricción adicional:**

El LLM recibe únicamente el ítem individual que está siendo procesado. No puede recibir la lista completa ni contexto de otros ítems.

---

## 3. Escrituras permitidas

**Campo creado:** `output`

Debe cumplir el schema contractual del sistema v1.

**Estructura obligatoria:**

```json
{
  "topic": "string",
  "time_window": "string",
  "results": [
    {
      "title": "string",
      "idea_clave": "string (≤ 80 palabras)",
      "relacion_con_query": "string (≤ 30 palabras)",
      "link": "string"
    }
  ]
}
```

**Reglas contractuales de escritura:**

- `topic` ← copia literal de `input_validated.query`, sin normalización ni transformación.
- `time_window` ← copia literal de `input_validated.time_window`.
- `results` mantiene exactamente el orden de `selected_items`.
- `len(results) == len(selected_items)`.

Para cada elemento:

- `title` ← copia intacta.
- `link` ← copia intacta.
- `idea_clave` ← resumen descriptivo del contenido.
- `relacion_con_query` ← explicación descriptiva de cómo el contenido se relaciona con la query.

No se permiten campos adicionales.

**Caso vacío:**

Si `selected_items` es una lista vacía, el nodo produce `output` con `results: []` y finaliza correctamente sin invocar el LLM. No es abort.

**Reglas:**

- Se crea una única vez en este nodo.
- La escritura es atómica: o se escribe completo y válido, o no se escribe.

---

## 4. Invariantes locales

### 4.1 Cardinalidad

`len(output.results) == len(selected_items)`

No se permiten:

- Ítems adicionales.
- Ítems omitidos.
- Reordenación.

### 4.2 Procesamiento

- Procesamiento estrictamente 1:1.
- Una llamada LLM por ítem.
- El LLM recibe únicamente el ítem individual.
- No existe contexto cruzado entre ítems.

### 4.3 Inmutabilidad

Para cada resultado:

- `title` se copia intacto.
- `link` se copia intacto.
- No se alteran valores originales.

### 4.4 Restricciones del contenido generado

- `idea_clave` ≤ 80 palabras.
- `relacion_con_query` ≤ 30 palabras.
- Contenido exclusivamente descriptivo.
- No comparativas entre ítems.
- No juicios de valor.
- No información externa.
- No inferencias más allá del contenido del ítem.

### 4.5 Determinismo estructural

Eliminar el LLM no altera:

- Conjunto de resultados.
- Orden.
- Cardinalidad.

El LLM solo afecta a los campos textuales generados.

---

## 5. Aborts específicos

### `SUMMARY_LLM_RUNTIME_ERROR`

- Timeout, error de invocación, respuesta vacía o respuesta no parseable.
- No se reintenta.

### `SUMMARY_SCHEMA_VIOLATION`

Condición (cualquiera):

- Campo obligatorio ausente.
- Campo adicional no permitido.
- Tipo incorrecto.
- `len(output.results) != len(selected_items)`.
- Orden distinto al de `selected_items`.
- `idea_clave` > 80 palabras.
- `relacion_con_query` > 30 palabras.
- `title` o `link` no coinciden exactamente con el ítem original.

**Regla contractual:**
Ante cualquier abort:

- No se escribe `output`.
- El nodo señaliza abort lanzando excepción. El runtime escribe `abort_reason`.
- El pipeline se detiene.

No existen resultados parciales. No existe degradación silenciosa. No existe reintento automático.

**Mapeo contractual:**
↳ `SUMMARY_SCHEMA_VIOLATION`, `SUMMARY_LLM_RUNTIME_ERROR` → Abort general 4 — Imposibilidad de validación ex-post.
↳ Cualquier comportamiento que introduzca criterio → Abort general 2 — Asunción de criterio por parte del LLM.

---

## 6. Prohibiciones explícitas

### 6.1 Sobre estructura

- Reordenar los ítems.
- Eliminar ítems.
- Añadir ítems.
- Añadir campos adicionales.
- Omitir campos obligatorios.
- Modificar `title` o `link`.

### 6.2 Sobre comportamiento del LLM

- Recibir más de un ítem por llamada.
- Acceder a otros ítems como contexto.
- Comparar ítems entre sí.
- Introducir ranking, priorización o criterio.
- Emitir opinión o juicio de valor.
- Introducir información no presente en el ítem.
- Corregir o reinterpretar decisiones previas del pipeline.

### 6.3 Sobre sistema

- Acceder a red, filesystem o artefactos exógenos.
- Aplicar retries inteligentes.
- Aplicar post-procesado semántico.
- Modificar el orden del pipeline.
- Acceder al reloj del sistema.

**Regla dura:**
Cualquier violación activa **Abort 5 — Ambigüedad de responsabilidad**.

---

## 7. Notas de gobernanza

El LLM actúa exclusivamente como transformador textual acotado. El nodo no introduce criterio ni modifica decisiones previas.

El conjunto y orden de resultados están completamente determinados antes de este nodo.

Si el LLM se elimina, la estructura, cardinalidad y orden del resultado permanecen idénticos.

No existe corrección automática ni ajuste posterior del texto generado.

El cumplimiento del schema es condición necesaria para la validez del output.

Cualquier cambio en:

- límites de palabras,
- modo de invocación (individual → batch),
- estructura del output,
- rol del LLM,

implica **nueva versión contractual**.

---

## 8. Estado del contrato

- **Versión:** v1
- **Estado:** **FROZEN**
