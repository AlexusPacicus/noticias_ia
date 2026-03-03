Tests_Summarize_v2.1
1. Scope
Este documento define los tests contractuales de la fase SummarizePhase v2.1.
Valida:
Correcta aplicación de aborts.
Preservación de invariantes estructurales.
Compatibilidad con HITL.
No contaminación de state.
Equivalencia con ejecución completa.
No valida:
Calidad del texto generado por LLM.
Latencia.
Métricas externas.
2. Tipos de test
2.1 Unit (por nodo)
summarize_map
summarize_reduce
Valida semántica local:
Conteo correcto de ok/failed.
No modificación de rank_position.
Orden impuesto correctamente en reduce.
No creación indebida de claves.
2.2 Integration (fase completa)
Valida:
Flujo completo de SummarizePhase.
Correcta selección de effective_selected_items.
Emisión correcta de aborts.
No ejecución de LLM cuando input vacío.
2.3 Equivalencia estructural
Valida:
system_full.invoke(..., execute_until="summary")
==
summarize_graph.invoke(...)
Con mismo state inicial.
3. Tests contractuales obligatorios
Test 1 — Happy Path
Input:
effective_selected_items con N > 0
LLM mockeado devuelve éxito
Expect:
summary_items len == N
summary_stats.ok == N
summary_stats.failed == 0
output existe
abort_reason no existe
returned_k == N
Test 2 — Fallos parciales
Input:
N items
LLM falla en algunos
Expect:
summary_stats.ok + summary_stats.failed == N
summary_stats.ok > 0
output existe
abort_reason no existe
Test 3 — Fallo total LLM
Input:
N > 0
LLM falla en todos
Expect:
summary_stats.ok == 0
abort_reason == SUMMARY_ALL_ITEMS_FAILED
output no existe
Test 4 — SUMMARY_EMPTY_INPUT
Input:
selected_items = []
hitl_selected_items no existe
Expect:
abort_reason == SUMMARY_EMPTY_INPUT
summarize_map NO ejecutado
LLM NO invocado
summary_items no existe
summary_stats no existe
output no existe
Test 5 — HITL domina selected_items
Input:
selected_items = 3
hitl_selected_items = 1
Expect:
Se procesa solo 1 item
summary_stats.ok + failed == 1
Test 6 — Preservación de rank_position
Input:
effective_selected_items con rank_position no consecutivos
Expect:
output.results ordenado por rank_position ascendente
rank_position no alterado
No reindexación
4. Invariantes estructurales que deben validarse
Cada test debe validar:
No se crean claves fuera de:
summary_items
summary_stats
output
abort_reason
No se modifican claves previas.
No se recalcula ranking.
No existe coexistencia output + abort_reason.
5. Prohibiciones a testear
Se debe verificar explícitamente:
SummarizePhase NO lee ranked_items.
SummarizePhase NO modifica selected_items.
SummarizePhase NO reintroduce claves eliminadas por hitl_remove_keys.
6. Cobertura mínima exigida
Cobertura de ambos aborts.
Cobertura de flujo con y sin HITL.
Cobertura de fallo parcial.