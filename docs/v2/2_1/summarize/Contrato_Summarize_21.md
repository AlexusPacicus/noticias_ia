# 📄 Contrato_SummarizePhase_v2.1

## 1. Estado

Versión: v2.1  
Estado: DRAFT  
Tipo: Contrato de Fase  
Fase: SummarizePhase  

Dependencias:
- Contrato_Sistema_v2.1
- Contrato_State_v2.1
- Contrato_LLM_v2.1

Este documento delimita la frontera de la fase **SummarizePhase** y no redefine reglas globales del sistema.

---

# 2. Contexto

SummarizePhase es una unidad estructural reutilizable del motor **AI Papers Engine**.

Su responsabilidad es transformar una lista previamente seleccionada en:

- `summary_items`
- `summary_stats`
- `output` (si la ejecución es exitosa)

SummarizePhase:

- NO realiza ranking
- NO realiza selección
- NO modifica resultados estructurales de Retrieval
- DEBE ser tolerante a fallos parciales por item
- DEBE poder ejecutarse de forma independiente una vez RetrievalPhase haya finalizado correctamente

---

# 3. Alcance (Scope)

SummarizePhase comprende exclusivamente los siguientes nodos:
`summarize_map` → `summarize_reduce`


La fase termina estrictamente tras la ejecución de `summarize_reduce`.

SummarizePhase **NO DEBE incluir**:

- RetrievalPhase
- HITLPhase
- Ranking
- Fetch
- Normalize
- Dedupe

---

# 4. Entradas

SummarizePhase lee:

selected_items
hitl_remove_keys (opcional)

El conjunto de items procesados se calcula internamente como:

effective_selected_items = selected_items - hitl_remove_keys)


En ausencia de `hitl_remove_keys`, se utiliza directamente `selected_items`.

SummarizePhase puede leer además:

- `input_validated.query`
- `input_validated.time_window`
- `input_validated.top_k`

SummarizePhase **NO DEBE leer**:

- `ranked_items`
- `merged_source_units`
- `normalized_items`
- `deduped_items`
- `hitl_action`
- `hitl_selected_items`

---

# 5. Salidas

En ejecución exitosa, SummarizePhase **DEBE producir**:

- `summary_items`
- `summary_stats`
- `output`

SummarizePhase **NO DEBE producir**:

- `ranked_items`
- `selected_items`
- `hitl_selected_items`
- claves de fases anteriores

---

# 6. Semántica de Gates

SummarizePhase **PUEDE emitir exclusivamente aborts de Gate F**:

- `SUMMARY_EMPTY_INPUT`
- `SUMMARY_ALL_ITEMS_FAILED`

SummarizePhase **NO PUEDE emitir** aborts de Gates A–E definidos en el sistema.

---

## 6.1 SUMMARY_EMPTY_INPUT

Condición:

len(`effective_selected_items`) == 0


Reglas:

El state **DEBE contener**
`abort_reason`= `SUMMARY_EMPTY_INPUT`


SummarizePhase **MUST NOT**:

- ejecutar `summarize_map`
- invocar LLM
- crear `summary_items`
- crear `summary_stats`
- crear `output`

---

## 6.2 SUMMARY_ALL_ITEMS_FAILED

Condición:

SummarizePhase ejecuta `summarize_map` sobre `effective_selected_items` con longitud ≥ 1.

Tras ejecutar `summarize_reduce`:
summary_stats.ok == 0

Reglas:

El state **DEBE contener**
`abort_reason` = `SUMMARY_ALL_ITEMS_FAILED`


Reglas adicionales:

- `output` **NO DEBE existir**
- `summary_stats` **DEBE existir**
- `summary_items` **PUEDE existir** (típicamente vacío)

---

## 6.3 Reglas generales de abort

En cualquier abort:

- El state **DEBE contener** `abort_reason`
- `output` **NO DEBE existir**
- **NO deben crearse claves posteriores**
- La ejecución debe detenerse tras `summarize_reduce` si el abort ocurre en esta fase

---

# 7. Invariantes

SummarizePhase **DEBE cumplir**:

### Determinismo condicionado

Dado:

- el mismo `effective_selected_items`
- el mismo modelo LLM
- la misma configuración del prompt

Entonces:
`summary_items` y `summary_stats` MUST ser idénticos


### Ejecución

- `summarize_map` DEBE ejecutarse secuencialmente
- no se permite paralelismo implícito

### Tolerancia a fallos

Un fallo individual de item **NO DEBE abortar la fase completa**.

### Trazabilidad

`rank_position` **MUST preservarse**.

### Reordenación final

`summarize_reduce` **MUST reordenar únicamente por**
`rank_position` ASC


### Coherencia estadística
summary_stats.ok + summary_stats.failed
== len(effective_selected_items)

### Coherencia con output público
returned_k == summary_stats.ok
failed_summaries == summary_stats.failed


---

# 8. Prohibiciones

SummarizePhase **NO DEBE**:

- Reordenar resultados antes de `summarize_reduce`
- Recalcular ranking
- Recalcular `top_k`
- Invocar `fetch`
- Invocar ranking
- Introducir decisiones basadas en métricas
- Reintroducir claves eliminadas por HITL (`hitl_remove_keys`)
- Crear claves fuera de:
`summary_items`
`summary_stats`
`output`
`abort_reason`


---

# 9. No-Objetivos

Este contrato **NO define**:

- Persistencia
- Reanudación
- Multi-LLM dinámico
- Reranking por LLM
- Observabilidad
- Cambios en el contrato global del sistema

---

# 10. Independencia de Ejecución

SummarizePhase **DEBE poder ejecutarse de forma independiente**:
summarize_graph.invoke(...)


Dado un state válido que contenga:

- `selected_items`
- `hitl_remove_keys` (opcional)
- `input_validated`

El resultado **DEBE ser idéntico** al del sistema completo desde:
summarize_map → summarize_reduce


---

# 11. Referencias

- Contrato_Sistema_v2.1
- Contrato_State_v2.1
- Contrato_LLM_v2.1
- Diseno_v2.1

---

# 12. Equivalencia estructural con el sistema completo

SummarizePhase es un **subgrafo estructural interno del pipeline v2.1**.

SummarizePhase **MUST ser semánticamente equivalente** a ejecutar el sistema completo desde `summarize_map` hasta `summarize_reduce`, bajo las siguientes condiciones:

- RetrievalPhase ya completada
- HITLPhase ya completada
- `effective_selected_items` no modificado
- Sin creación de claves ajenas a SummarizePhase

Cualquier divergencia entre:
system_full.invoke(..., execute_until="summary")
summarize_graph.invoke(...)


constituye una **violación contractual**.

---

# 13. State retornado

SummarizePhase **MUST devolver el state completo acumulado** hasta el final de `summarize_reduce`.

### Ejecución exitosa

El state **MUST contener**:

- `summary_items`
- `summary_stats`
- `output`

### En caso de abort

El state **MUST contener**:
`abort_reason`


Las reglas de existencia de claves siguen lo definido en `Contrato_State_v2`.

SummarizePhase **MUST NOT crear**:

- `ranked_items`
- `selected_items`
- `hitl_selected_items`

---

# 14. Orden total congelado

SummarizePhase **MUST**:

- preservar `rank_position` de los items de entrada
- reordenar únicamente en `summarize_reduce` por
rank_position ASC

SummarizePhase **MUST NOT**:

- recalcular ranking
- modificar `rank_position`
- introducir estrategias alternativas