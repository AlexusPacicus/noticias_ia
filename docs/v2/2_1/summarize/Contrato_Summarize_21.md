1. Estado
Versión: v2.1
Estado: DRAFT
Tipo: Contrato de Fase
Fase: SummarizePhase
Dependencias:
Contrato_Sistema_v2 
Contrato_Sistema_v2
Contrato_State_v2 
Contrato_State_v2
Contrato_LLM_v2
Este documento delimita la frontera de la fase Summarize y no redefine reglas globales del sistema.
2. Contexto
SummarizePhase es una unidad estructural reutilizable del motor AI Papers Engine.
Su responsabilidad es:
Transformar una lista previamente seleccionada (selected_items o hitl_selected_items) en:
summary_items
summary_stats
output (si éxito)
SummarizePhase NO realiza ranking ni selección.
SummarizePhase DEBE ser tolerante a fallos parciales por item.
SummarizePhase DEBE poder ejecutarse de forma independiente una vez RetrievalPhase haya finalizado correctamente.
3. Alcance (Scope)
SummarizePhase comprende exclusivamente los siguientes nodos:
summarize_map
→ summarize_reduce
La fase termina estrictamente tras la ejecución de summarize_reduce.
SummarizePhase NO DEBE incluir:
RetrievalPhase
HITL
Ranking
Fetch
Normalize
Dedupe
4. Entradas
SummarizePhase acepta exclusivamente como entrada efectiva:
effective_selected_items
Definición:
Si existe hitl_selected_items → usar esa lista.
En caso contrario → usar selected_items.
Además puede leer:
input_validated.query
input_validated.time_window
input_validated.top_k
SummarizePhase NO DEBE leer:
ranked_items
merged_source_units
normalized_items
deduped_items
5. Salidas
En ejecución exitosa, SummarizePhase DEBE producir:
summary_items
summary_stats
output
SummarizePhase NO DEBE producir:
ranked_items
selected_items
hitl_selected_items
Claves de fases anteriores
6. Semántica de Gates
SummarizePhase PUEDE emitir exclusivamente aborts de Gate F:
SUMMARY_EMPTY_INPUT
SUMMARY_ALL_ITEMS_FAILED
6.1 SUMMARY_EMPTY_INPUT
Condición:
len(effective_selected_items) == 0
Reglas:
El state DEBE contener abort_reason = SUMMARY_EMPTY_INPUT
SummarizePhase MUST NOT ejecutar summarize_map
SummarizePhase MUST NOT invocar LLM
SummarizePhase MUST NOT crear:
summary_items
summary_stats
output
6.2 SUMMARY_ALL_ITEMS_FAILED
Condición:
SummarizePhase ejecuta summarize_map sobre effective_selected_items con longitud >= 1
Tras ejecutar summarize_reduce:
summary_stats.ok == 0
Reglas:
El state DEBE contener abort_reason = SUMMARY_ALL_ITEMS_FAILED
output NO DEBE existir
summary_stats DEBE existir
summary_items PUEDE existir (típicamente vacío)
En cualquier abort:
El state DEBE contener abort_reason
output NO DEBE existir
NO se crean claves posteriores
SummarizePhase NO PUEDE emitir:
Gates A–E definidos en Contrato_Sistema_v2 
Contrato_Sistema_v2
7. Invariantes
SummarizePhase DEBE cumplir:
Ejecución secuencial determinista de summarize_map (sin paralelismo).
Tolerancia a fallos parciales por item: un fallo individual NO aborta.
Preservación de trazabilidad: rank_position MUST preservarse.
Reordenación final: summarize_reduce MUST reordenar únicamente por rank_position.
Coherencia estadística:
summary_stats.ok + summary_stats.failed
== len(effective_selected_items)
Coherencia con output público:
returned_k == summary_stats.ok
failed_summaries == summary_stats.failed
8. Prohibiciones
SummarizePhase NO DEBE:
Reordenar resultados antes de summarize_reduce.
Recalcular ranking.
Recalcular top_k.
Invocar fetch.
Invocar ranking.
Introducir decisiones basadas en métricas.
Reintroducir claves eliminadas por HITL (hitl_remove_keys).
Crear claves fuera de:
summary_items
summary_stats
output
abort_reason
9. No-Objetivos
Este contrato NO define:
Persistencia
Reanudación
Multi-LLM dinámico
Reranking por LLM
Observabilidad
Cambios en el contrato global del sistema
10. Independencia de Ejecución
SummarizePhase DEBE poder compilarse y ejecutarse de forma independiente:
summarize_graph.invoke(...)
Dado un state válido que contenga:
selected_items (o hitl_selected_items)
input_validated
El resultado DEBE ser idéntico al del sistema completo desde summarize_map hasta summarize_reduce.
11. Referencias
Contrato_Sistema_v2 
Contrato_Sistema_v2
Contrato_State_v2 
Contrato_State_v2
Contrato_LLM_v2
Diseno_v2 
Diseno_v2
AI Papers Engine — v2.1 Scope 
alcance_21
12. Equivalencia estructural con el sistema completo
SummarizePhase es un subgrafo estructural interno del pipeline v2.1.
SummarizePhase MUST ser semánticamente equivalente a ejecutar el sistema completo desde summarize_map hasta summarize_reduce, bajo las siguientes condiciones:
Sin ejecución de nodos de RetrievalPhase (ya completada)
Sin modificación de effective_selected_items
Sin creación de claves ajenas a SummarizePhase
Cualquier divergencia entre:
system_full.invoke(..., execute_until="summary")
summarize_graph.invoke(...)
constituye una violación contractual.
13. State retornado
SummarizePhase MUST devolver el state completo acumulado hasta el final de summarize_reduce.
En ejecución exitosa, el state MUST contener:
summary_items
summary_stats
output
SummarizePhase MUST NOT crear:
ranked_items
selected_items
hitl_selected_items
En caso de abort, aplican las reglas de existencia definidas en Contrato_State_v2 
Contrato_State_v2
.
14. Orden total congelado
SummarizePhase MUST:
Preservar rank_position de los items de entrada
Reordenar únicamente en summarize_reduce por rank_position ascendente
MUST NOT recalcular ranking tras summarize
MUST NOT introducir estrategias alternativas