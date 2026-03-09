# 📄 Contrato_State_v2.1

## 1. Estado

Versión: v2.1  
Estado: FROZEN  
Tipo: Contrato de Estado  

Este documento define:

- dominio completo del state del sistema
- writers autorizados por clave
- readers autorizados
- invariantes globales
- reglas de coexistencia
- matriz contractual (resumen derivado)

---

## 2. Dominio del state

El state del sistema contiene exclusivamente las siguientes claves:

- `query`
- `time_window`
- `top_k`
- `input_raw`
- `input_validated`
- `source_units`
- `merged_source_units`
- `normalized_items`
- `filtered_items`
- `deduped_items`
- `ranked_items`
- `selected_items`
- `hitl_action`
- `hitl_remove_keys`
- `summary_items`
- `summary_stats`
- `output`
- `abort_reason`

No se permiten claves adicionales.

---

## 3. Writers

Cada clave tiene **un único writer contractual** (salvo `abort_reason`, ver regla global).

| Clave | Writer |
|------|------|
| query | collect_input |
| time_window | collect_input |
| top_k | collect_input |
| input_raw | collect_input |
| input_validated | validate_input |
| source_units | fetch_* |
| merged_source_units | merge_source_units |
| normalized_items | normalize |
| filtered_items | filter_by_time_window |
| deduped_items | dedupe |
| ranked_items | rank_bm25 |
| selected_items | select |
| hitl_action | hitl_review |
| hitl_remove_keys | hitl_review |
| summary_items | summarize_map |
| summary_stats | summarize_reduce |
| output | summarize_reduce |

`abort_reason`:
- Writer: el nodo que emite el abort (según contratos de fase y sistema)
- Restricción: write-once (ver §5)

---

## 4. Readers

Los readers contractuales se resumen en la matriz (§9).  
Regla mínima explícita v2.1:

- `hitl_remove_keys` es leído por `summarize_map` para calcular `effective_selected_items`.

---

## 5. Invariantes globales

Las siguientes condiciones deben cumplirse siempre que el state exista.

### 5.1 Writer único

Cada clave tiene un único writer contractual, excepto `abort_reason`, que se rige por write-once.

### 5.2 Abort write-once

`abort_reason` es write-once.

Una vez definida:

- no puede modificarse
- no puede sobrescribirse

### 5.3 Abort dominante

Si existe `abort_reason`, entonces:

- el flujo del pipeline debe detenerse
- no deben crearse claves posteriores al punto de abort

### 5.4 Inmutabilidad por fases

Una fase MUST NOT modificar claves creadas por fases anteriores.  
Solo puede leerlas.

### 5.5 Integridad de HITL

Si `hitl_action = "cancel"`, entonces:

- `abort_reason = "USER_ABORT"`
- MUST NOT existir: `hitl_remove_keys`
- MUST NOT existir: `summary_items`, `summary_stats`, `output`

### 5.6 Integridad subset

Si `hitl_action = "subset"`, entonces:

- `hitl_remove_keys` MUST existir
- `hitl_remove_keys ⊆ canonical_id(selected_items)`
- `hitl_remove_keys` no puede contener duplicados

### 5.7 Acción accept

Si `hitl_action = "accept"`, entonces:

- `hitl_remove_keys = []`

---

## 6. Reglas de existencia de claves

### 6.1 Ejecución exitosa por frontera

En ejecución exitosa:

- tras `rank_bm25` → `ranked_items` MUST existir
- tras `select` → `selected_items` MUST existir
- tras `hitl_review` (no cancel) → `hitl_action` y `hitl_remove_keys` MUST existir
- tras `summarize_reduce` → `summary_items`, `summary_stats` y `output` MUST existir

### 6.2 Abort

En caso de abort:

- `abort_reason` MUST existir
- no deben existir claves posteriores al punto de abort
- `output` MUST NOT existir

(El detalle por Gate se define en los contratos de fase.)

---

## 7. Integridad del pipeline

El state evoluciona únicamente en el orden del pipeline definido por el sistema:

Retrieval → HITL → Summarize

Ninguna fase puede modificar claves pertenecientes a fases anteriores.

---

## 8. Compatibilidad con v2

Contrato_State_v2.1 extiende v2 añadiendo exclusivamente:

- `hitl_action`
- `hitl_remove_keys`
- abort code: `USER_ABORT`

No se eliminan claves existentes.

---

## 9. Matriz contractual del state (resumen derivado)

La siguiente matriz resume las relaciones contractuales entre claves, writers, readers y fases.
Esta matriz es derivada de las reglas anteriores y no introduce nueva semántica.

| Clave               | Writer                   | Readers                     | Fase      |
| ------------------- | ------------------------ | --------------------------- | --------- |
| query               | collect_input            | validate_input              | Retrieval |
| time_window         | collect_input            | validate_input              | Retrieval |
| top_k               | collect_input            | select, summarize_map       | Retrieval |
| input_raw           | collect_input            | validate_input              | Retrieval |
| input_validated     | validate_input           | fetch_router, summarize_map | Retrieval |
| source_units        | fetch_*                  | merge_source_units          | Retrieval |
| merged_source_units | merge_source_units       | normalize                   | Retrieval |
| normalized_items    | normalize                | filter_by_time_window       | Retrieval |
| filtered_items      | filter_by_time_window    | dedupe                      | Retrieval |
| deduped_items       | dedupe                   | rank_bm25                   | Retrieval |
| ranked_items        | rank_bm25                | select                      | Retrieval |
| selected_items      | select                   | hitl_review, summarize_map  | Retrieval |
| hitl_action         | hitl_review              | ninguno                     | HITL      |
| hitl_remove_keys    | hitl_review              | summarize_map               | HITL      |
| summary_items       | summarize_map            | summarize_reduce            | Summarize |
| summary_stats       | summarize_reduce         | output                      | Summarize |
| output              | summarize_reduce         | sistema externo             | Summarize |
| abort_reason        | nodo que aborta (write-once) | sistema completo        | Global    |