# Contrato de State — v2

## 1. Estado

- Version: v2
- Estado: FROZEN
- Complementa:
  - Contrato de Sistema v2 → `Contrato_Sistema_v2`
  - Documento de Diseño v2 → `Diseno_v2`

---

## 2. Propósito

Definir el state gobernado del runtime LangGraph para v2.

Este contrato:

- Cierra la lista de claves permitidas.
- Define creador único por clave.
- Define reglas de mutación.
- Define matriz de lectura.
- Formaliza condiciones de existencia por fase.
- Refuerza abort dominante.
- Asegura compatibilidad con concurrencia multi-fuente.
- No define implementación interna.

---

## 3. Lista cerrada de claves permitidas

El state gobernado contractual contiene exactamente 16 claves.

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

Todas las claves están sujetas a los invariantes de §4–§10. Claves fuera de esta lista MUST NOT existir. → `Contrato_Sistema_v2` §13

---

## 4. Reglas operativas

### 4.1 Reglas base

- No existe mutación in-place del state.
- Cada nodo retorna su delta.
- LangGraph realiza el merge del estado.
- El state crece monótonamente (solo adición de claves).
- Una clave, una vez creada, es inmutable por defecto.
- Ningún nodo puede sobrescribir una clave existente.
- Cada clave MUST tener un único creador contractual, salvo las categorías declaradas en §4.2, §4.3 y §4.4. → `Contrato_Sistema_v2` §12

### 4.2 Claves inyectadas por runtime

`query`, `time_window` y `top_k` son inyectadas por el runtime (`graph.invoke`) antes de la ejecución del primer nodo. Su creador contractual es el runtime, no un nodo del pipeline. Son inmutables tras inyección: ningún nodo del pipeline puede sobrescribirlas.

### 4.3 Clave reducible (`source_units`)

Una clave reducible admite escrituras parciales de múltiples nodos concurrentes. El runtime MUST combinar las escrituras mediante una estrategia de merge declarada.

En v2, `source_units` es la única clave reducible:

- Cada `fetch_*` escribe exclusivamente su subclave de fuente (`source_units["arxiv"]`, `source_units["huggingface"]`).
- El merge permitido es deep-merge por subclave de fuente.
- No se permite overwrite total de `source_units`.
- El merge del runtime MUST preservar ambas subclaves.
- Compatible con el modelo de aislamiento definido en `Contrato_Sistema_v2` §4.
- El resto de claves siguen la regla de inmutabilidad por defecto (§4.1).

### 4.4 Clave terminal multi-origen (`abort_reason`)

`abort_reason` es excepción al principio de writer único:

- Es una clave terminal multi-origen: cualquier nodo con gate de abort contractual puede crearla.
- Solo puede existir una instancia por ejecución.
- Su creación impide la materialización de claves posteriores al nodo que aborta.
- `abort_reason` y `output` son mutuamente excluyentes. → `Contrato_Sistema_v2`

---

## 5. Matriz de creación (writers)

| Clave | Creador contractual |
|---|---|
| `query` | runtime (`graph.invoke`) |
| `time_window` | runtime (`graph.invoke`) |
| `top_k` | runtime (`graph.invoke`) |
| `input_raw` | `collect_input` |
| `input_validated` | `validate_input` |
| `source_units` | `fetch_*` (clave reducible, ver §4.3) |
| `merged_source_units` | `merge_source_units` |
| `normalized_items` | `normalize` |
| `filtered_items` | `filter_by_time_window` |
| `deduped_items` | `dedupe` |
| `ranked_items` | `rank_bm25` |
| `selected_items` | `select` |
| `summary_stats` | `summarize_map` |
| `summary_items`| `summarize_map` |
| `output` | `summarize_reduce` |
| `abort_reason` | Terminal multi-origen (ver §4.4) |

---

## 6. Matriz de lectura (readers permitidos)

Un nodo solo puede leer claves ya materializadas previamente en el pipeline fijo. → `Contrato_Sistema_v2`

| Nodo | Lecturas permitidas |
|---|---|
| `collect_input` | `query`, `time_window`, `top_k` |
| `validate_input` | `input_raw` |
| `fetch_router` | `input_validated` |
| `fetch_*` | `input_validated` |
| `merge_source_units` | `source_units[*].status`, `source_units[*].items` |
| `normalize` | `merged_source_units` |
| `filter_by_time_window` | `normalized_items`, `input_validated.time_window` |
| `dedupe` | `filtered_items` |
| `rank_bm25` | `deduped_items`, `input_validated.query` |
| `select` | `ranked_items`, `input_validated.top_k` |
| `summarize_map` | `selected_items` |
| `summarize_reduce` | `summary_stats`, `summary_items`, `input_validated.query`, `input_validated.time_window`, `input_validated.top_k` |

### Prohibiciones explícitas

- `normalize` no puede leer `query`.
- `rank_bm25` no puede leer `selected_items`.
- `summarize_map` no puede leer `ranked_items`.
- Ningún nodo puede leer `output`.
- Los nodos MUST NOT leer `abort_reason`.

---

## 7. Shapes mínimos contractuales

### 7.1 `query`, `time_window`, `top_k`

Claves inyectadas por runtime. Shape y restricciones definidas en `Contrato_Sistema_v2` §6.

### 7.2 `input_raw`

Resultado de la lectura de `query`, `time_window` y `top_k` por `collect_input`:

```json
{
  "query": "any",
  "time_window": "any",
  "top_k": "any"
}
```

Contiene exactamente esas tres claves tal como fueron inyectadas por el runtime. No se aplica coerción de tipos, defaults ni validaciones.

### 7.3 `input_validated`

Input validado con defaults aplicados:

```json
{
  "query": "string",
  "time_window": "last_24h | last_3_days | last_7_days",
  "top_k": "int"
}
```

Reglas:

- `query` MUST ser string no vacío.
- `time_window` MUST pertenecer al conjunto cerrado de ventanas válidas.
- `top_k` MUST estar en rango `[1..5]`. Si ausente en `input_raw` → default = `3`.
- `top_k` siempre presente tras validación.

→ `Contrato_Sistema_v2` §6

### 7.4 `source_units` (por fuente, con trazabilidad)

Estructura:

```json
{
  "arxiv": {
    "status": "ok | failed",
    "error": null | { "code": "string", "message": "string" },
    "items": [ "SourceUnit" ]
  },
  "huggingface": {
    "status": "ok | failed",
    "error": null | { "code": "string", "message": "string" },
    "items": [ "SourceUnit" ]
  }
}
```

Reglas:

- Si `status="ok"`:
  - `error` MUST ser `null`.
  - `items` puede ser lista vacía.
- Si `status="failed"`:
  - `items` MUST ser `[]`.
  - `error` MUST existir.
- No puede existir combinación inconsistente.

### 7.5 `merged_source_units`

Shape mínimo contractual:

```json
[
  {
    "source": "string",
    "source_seq": "int",
    "payload": "object"
  }
]
```

Reglas:

- MUST ser `List[SourceUnit]`.
- Cada elemento MUST preservar `source` y `source_seq` de `source_units`.
- El contenido de `payload` MUST corresponder al item original de la fuente.
- MUST estar ordenada determinísticamente por:

```
(SOURCE_PRIORITY.index(source), source_seq)
```

→ `Diseno_v2`

### 7.6 `normalized_items`

Cada item MUST contener:

- `title`
- `content`
- `published_at`
- `link`
- `source`
- `canonical_id`

`normalize` MUST preservar el orden de `merged_source_units`.

→ `Diseno_v2`

### 7.7 `filtered_items`

Lista de items con la misma shape que `normalized_items` (§7.6).

- Subconjunto de `normalized_items` que cumple la ventana temporal.
- Conserva orden heredado de `normalized_items`.
- Puede ser lista vacía (→ abort `NO_ITEMS_IN_TIME_WINDOW`).

### 7.8 `deduped_items`

- Subconjunto de `filtered_items`.
- Dedupe exclusivo por `canonical_id`.
- Conserva orden.

→ `Diseno_v2`

### 7.9 `ranked_items`

Cada item MUST incluir además:

- `bm25_score`
- `rank_position`

Orden total:

```
(-bm25_score, title ASC, link ASC)
```

→ `Diseno_v2`

### 7.10 `selected_items`

- Prefijo de `ranked_items`.
- No reordenado.

### 7.11 `summary_items`

Estructura cerrada:

```json
[
  {
    "rank_position": "int",
    "title": "string",
    "summary": "string",
    "link": "string",
    "source": "string"
  }
]
```
Reglas:

- len(summary_items) == summary_stats.ok
- summary_stats.ok + summary_stats.failed == len(selected_items)
- Cada elemento corresponde a un selected_item válido
- `rank_position` MUST preservarse
- Orden no contractual (reduce reordena)


### 7.12 `summary_stats`

Estructura cerrada:

```json
{
  "ok": "int",
  "failed": "int"
}
```

### 7.13 `output`

Shape definida en `Contrato_Sistema_v2` §7. No se duplica aquí.

Reglas:

- MUST existir solo en ejecución exitosa.
- MUST NOT coexistir con `abort_reason`.

### 7.14 `abort_reason`

Tipo: `string`.

Valor MUST corresponder a un código del conjunto cerrado definido en `Contrato_Sistema_v2` §10.

---

## 8. Abort dominante

Si `abort_reason` existe:

- El flujo termina.
- `output` no puede existir.
- No se crean claves posteriores.

→ `Contrato_Sistema_v2`

---

## 9. Condiciones de existencia por fase

### 9.1 Regla general

En cualquier abort, existen todas las claves hasta el nodo que aborta inclusive, y ninguna posterior.

- Claves anteriores: todas las claves creadas por nodos previos al que aborta MUST existir.
- Nodo que aborta: MUST crear `abort_reason`. MAY crear su clave de output según la semántica del gate.
- Claves posteriores: MUST NOT existir.

### 9.2 Ejecución exitosa

Existen: `query`, `time_window`, `top_k`, `input_raw`, `input_validated`, `source_units`, `merged_source_units`, `normalized_items`, `filtered_items`, `deduped_items`, `ranked_items`, `selected_items`, `summary_items`, `summary_stats`, `output`.

MUST NOT existir `abort_reason`.

### 9.3 Abort en input

Gate A. Códigos: `EMPTY_INPUT_PAYLOAD`, `INVALID_QUERY`, `INVALID_TIME_WINDOW`, `INVALID_TOP_K`.

Nodos: `collect_input`, `validate_input`. → `Contrato_Sistema_v2` §10

Existen: `query`, `time_window`, `top_k`, `input_raw`, `abort_reason`.

No existe `input_validated` ni claves posteriores.

### 9.4 Abort global de fetch

Gate B. Códigos: `FETCH_ALL_SOURCES_FAILED`, `UNKNOWN_SOURCE_PRIORITY`.

Nodo: `merge_source_units`. → `Contrato_Sistema_v2` §10

Existen: `query`, `time_window`, `top_k`, `input_raw`, `input_validated`, `source_units`, `abort_reason`.

No existe `merged_source_units` ni claves posteriores.

### 9.5 Abort pre-ranking estructural

Gate C. → `Contrato_Sistema_v2` §10

**`NO_ITEMS_IN_TIME_WINDOW`** (`filter_by_time_window`):

Existen: `query`, `time_window`, `top_k`, `input_raw`, `input_validated`, `source_units`, `merged_source_units`, `normalized_items`, `filtered_items`, `abort_reason`.

No existe `deduped_items` ni claves posteriores.

**`NO_ITEMS_AFTER_DEDUPE`** (`dedupe`):

Existen: `query`, `time_window`, `top_k`, `input_raw`, `input_validated`, `source_units`, `merged_source_units`, `normalized_items`, `filtered_items`, `deduped_items`, `abort_reason`.

No existe `ranked_items` ni claves posteriores.

### 9.6 Abort en ranking

Gate D. Código: `RANK_QUERY_EMPTY_AFTER_NORMALIZATION`.

Nodo: `rank_bm25`. → `Contrato_Sistema_v2` §10

Existen: `query`, `time_window`, `top_k`, `input_raw`, `input_validated`, `source_units`, `merged_source_units`, `normalized_items`, `filtered_items`, `deduped_items`, `abort_reason`.

No existe `ranked_items` ni claves posteriores.

Regla explícita de Gate D:

- `rank_bm25` MUST NOT crear `ranked_items` cuando emite `RANK_QUERY_EMPTY_AFTER_NORMALIZATION`.

### 9.7 Abort en select

Gate E. Códigos: `SELECT_MISSING_RANKED_ITEMS`, `SELECT_TOPK_INVALID`.

Nodo: `select`. → `Contrato_Sistema_v2` §10

Existen: `query`, `time_window`, `top_k`, `input_raw`, `input_validated`, `source_units`, `merged_source_units`, `normalized_items`, `filtered_items`, `deduped_items`, `ranked_items`, `abort_reason`.

No existe `selected_items` ni claves posteriores.

### 9.8 Abort en summary

Gate F. Código: `SUMMARY_ALL_ITEMS_FAILED`.

Nodo: `summarize_reduce`. → `Contrato_Sistema_v2` §10

Existen: `query`, `time_window`, `top_k`, `input_raw`, `input_validated`, `source_units`, `merged_source_units`, `normalized_items`, `filtered_items`, `deduped_items`, `ranked_items`, `selected_items`, `summary_items`, `summary_stats`, `abort_reason`.

No existe `output`.

### 9.9 Restricciones de valor en abort

Además de la existencia de claves, los siguientes aborts imponen restricciones de valor:

| Abort | Restricción |
|---|---|
| `NO_ITEMS_IN_TIME_WINDOW` | `filtered_items` = `[]` |
| `NO_ITEMS_AFTER_DEDUPE` | `deduped_items` = `[]` |
| `SUMMARY_ALL_ITEMS_FAILED` | `summary_stats.ok == 0` |

---

## 10. Invariantes globales v2

- Determinismo estructural: → `Contrato_Sistema_v2` §12
- Dedupe exclusivamente estructural.
- Ranking puramente textual.
- No dependencia del orden de finalización en concurrencia.
- `output` y `abort_reason` son mutuamente excluyentes.
- No existen claves huérfanas.
