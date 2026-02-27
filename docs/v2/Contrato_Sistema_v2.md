# Contrato de Sistema — v2

## 1. Estado

- Versión: v2
- Estado: FROZEN
- Runtime oficial: grafo compilado ejecutado exclusivamente vía `graph.invoke(input)`
- Sustituye semánticamente la capa de sistema de v1.1.

---

## 2. Propósito

Definir el comportamiento contractual del sistema multi-fuente determinista para descubrimiento y resumen de papers técnicos.

Este contrato:

- Congela orden del pipeline.
- Congela modelo I/O público.
- Congela política de fallo.
- Define modelo de concurrencia.
- Define invariantes estructurales.
- Define gates de abort.
- No define implementación interna.

---

## 3. Pipeline contractual (orden fijo)

```
collect_input
  → validate_input
  → fetch_router
  → fetch_*
  → merge_source_units
  → normalize
  → filter_by_time_window
  → dedupe
  → rank_bm25
  → select
  → summarize_map
  → summarize_reduce
```

Ningún nodo:

- MUST NOT alterar el orden.
- MUST NOT reejecutar nodos previos.
- MUST NOT introducir nodos no definidos en este pipeline.

---

## 4. Modelo de concurrencia

### 4.1 Concurrencia permitida

- Ejecución concurrente permitida únicamente en múltiples `fetch_*`.
- `summarize_map` MUST ejecutarse de forma secuencial determinista.
- La ejecución secuencial de `fetch_*` es contractualmente válida.
- Las invariantes de merge y orden aplican independientemente del modelo de ejecución.

### 4.2 Aislamiento

Cada rama paralela:

- MUST operar sobre copia inmutable de su input.
- MUST retornar solo su delta de state.
- MUST NOT mutar estado compartido.

### 4.3 Reestablecimiento de orden

- `merge_source_units` MUST imponer orden determinista según:

```python
SOURCE_PRIORITY = ["arxiv", "huggingface"]
```

Criterio de orden:

```
(SOURCE_PRIORITY.index(source), source_seq)
```

`source_seq` MUST ser un contador incremental 0-indexed por fuente, asignado en el orden exacto en que el endpoint devuelve los items.

- `summarize_reduce` MUST reordenar por `rank_position`.

El orden final contractual no depende del orden de finalización de ramas paralelas.

---

## 5. Fuentes contractuales activas

- `"arxiv"`
- `"huggingface"`

Lista cerrada. No se admiten fuentes adicionales sin nueva versión del contrato.

---

## 6. Input público

Campos permitidos:

- `query`: `str`
- `time_window`: `"last_24h"` | `"last_3_days"` | `"last_7_days"`
- `top_k`: `int` (opcional)

Restricciones:

- `query` MUST ser string no vacío.
- `top_k` MUST estar en rango `[1..5]`.
- Si ausente → default = `3`.

---

## 7. Output público

### 7.1 Éxito

```json
{
  "topic": "string",
  "time_window": "string",
  "requested_k": "int",
  "returned_k": "int",
  "failed_summaries": "int",
  "results": [
    {
      "title": "string",
      "summary": "string",
      "link": "string",
      "source": "string",
      "rank_position": "int"
    }
  ]
}
```

### 7.2 Reglas

- `returned_k` <= `requested_k`.
- `rank_position` MUST reflejar ranking previo a summarize.
- `rank_position` MUST NOT recalcularse.
- `output` y `abort_reason` MUST NOT coexistir.
- Coherencia de summary: `summary_stats.ok + summary_stats.failed == len(selected_items)` según `Contrato_State_v2` §7.11.

---

## 8. Snapshot determinista

- Snapshot := payload serializado íntegro devuelto por cada endpoint en el momento de fetch. El snapshot incluye contenido y orden recibido. Dos respuestas con mismo contenido pero distinto orden se consideran snapshots distintos.
- El sistema no preserva el orden del proveedor. El orden contractual se establece exclusivamente en `merge_source_units`.
- Mismo input + mismo snapshot MUST producir mismo conjunto y orden hasta `rank_bm25`.
- La redacción del LLM no forma parte del determinismo estructural.

---

## 9. Política de fallo

Principios:

- Fallos parciales MAY ser absorbidos según fase.
- Abort solo ocurre en condiciones explícitamente definidas.
- En abort no se emiten resultados parciales.

### Abort dominante

- Si un nodo retorna `abort_reason`, el flujo MUST terminar inmediatamente.
- Nodos posteriores MUST NOT ejecutarse tras `abort_reason`.
- `output` MUST NOT crearse en una ejecución abortada.

---

## 10. Gates de abort

### Gate A — Input

- `EMPTY_INPUT_PAYLOAD`
- `INVALID_QUERY`
- `INVALID_TIME_WINDOW`
- `INVALID_TOP_K`

### Gate B — Fetch

- `FETCH_ALL_SOURCES_FAILED`
- `UNKNOWN_SOURCE_PRIORITY`

Reglas:

- Si al menos una fuente produce items → MUST continuar con las fuentes disponibles.
- Los nodos `fetch_*` individuales MUST NOT emitir `abort_reason`.
- Si existe en `source_units` una clave no incluida en SOURCE_PRIORITY → abort.

### Gate C — Pre-ranking estructural

- `NO_ITEMS_IN_TIME_WINDOW`
- `NO_ITEMS_AFTER_DEDUPE`

Regla: Ranking MUST NOT ejecutarse con lista vacía.

### Gate D — Ranking

- `RANK_QUERY_EMPTY_AFTER_NORMALIZATION`

### Gate E — Select

- `SELECT_MISSING_RANKED_ITEMS`
- `SELECT_TOPK_INVALID`

### Gate F — Summarize

- `SUMMARY_ALL_ITEMS_FAILED`

Reglas:

- Fallos individuales MUST ser absorbidos.
- Abort solo si todos los summaries fallan.

---

## 11. Ruptura formal con v1.1

En v1.1 existían aborts por fallo individual de summary.

En v2:

- Los fallos individuales MUST ser absorbidos.
- Solo se permite `SUMMARY_ALL_ITEMS_FAILED`.
- Cambio semántico deliberado.

---

## 12. Invariantes estructurales

- MUST producir determinismo estructural hasta ranking.
- MUST deduplicar exclusivamente por `canonical_id`.
- MUST rankear mediante BM25 puramente textual. Parámetros congelados: `k1 = 1.5`, `b = 0.75`. El orden total MUST ser:

```
(-bm25_score, title ASC, link ASC)
```
- MUST NOT usar embeddings.
- MUST NOT usar similitud semántica.
- MUST NOT usar señales sociales.
- MUST NOT usar reranking por LLM.
- MUST NOT recalcular ranking tras summarize.
- MUST NOT depender del orden de finalización en concurrencia.
- MUST NOT mutar state in-place.
- Cada clave del state MUST tener creador único, salvo excepciones declaradas en el Contrato de State correspondiente.

---

## 13. State gobernado

Lista cerrada de 16 claves permitidas.

Claves inyectadas por runtime (`graph.invoke`):

- `query`
- `time_window`
- `top_k`

Claves internas (creadas por nodos del pipeline):

- `input_raw`
- `input_validated`
- `source_units`
- `merged_source_units`
- `normalized_items`
- `filtered_items`
- `deduped_items`
- `ranked_items`
- `selected_items`
- `summary_items`
- `summary_stats`
- `output`
- `abort_reason`

Todas las claves están sujetas a los invariantes de §12. Claves fuera de esta lista MUST NOT existir.

---

## 14. Compatibilidad histórica

- v1 permanece FROZEN.
- v1.1 permanece FROZEN.
- v2 redefine la capa de sistema con modelo multi-fuente y concurrencia formal.
