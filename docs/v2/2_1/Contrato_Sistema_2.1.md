1. Identificación
Sistema: AI Papers Engine
Versión: v2.1
Estado: FROZEN
Tipo: Contrato de Sistema
Este documento define la interfaz pública y la semántica global del sistema.
Incluye:
pipeline del sistema
interfaz de entrada
interfaz de salida
política global de abort
semántica de ejecución parcial
equivalencias estructurales
Este contrato NO define:
dominio del state
writers/readers
contratos internos de nodos
reglas internas de fase
Estos elementos están definidos en contratos específicos.

2. Principios arquitectónicos
El sistema sigue un enfoque contract-first.
Principios obligatorios:
Interfaces explícitas
Toda interacción entre fases se realiza mediante el state.
Separación de responsabilidades
El sistema se divide en tres fases:
Retrieval
HITL
Summarize
Nodos como funciones puras
Cada nodo devuelve actualizaciones parciales del state.
Abort dominante
Si aparece abort_reason:
la ejecución se detiene inmediatamente
no se ejecutan nodos posteriores
State gobernado
El dominio del state está definido externamente en Contrato_State_v2.1.

3. Pipeline del sistema
El pipeline v2.1 es determinista y fijo.
Orden obligatorio:
collect_input
→ validate_input
→ fetch_router
→ fetch_arxiv
→ fetch_huggingface
→ merge_source_units
→ normalize
→ filter_by_time_window
→ dedupe
→ rank_bm25
→ select
→ hitl_review
→ summarize_map
→ summarize_reduce
Reglas:
- el orden NO DEBE cambiar
- no se permiten nodos adicionales
- no se permiten loops
- no se permiten ramas dinámicas

4. Fases del sistema
El pipeline se divide en tres fases contractuales.
4.1 Retrieval
Nodos:
collect_input
validate_input
fetch_router
fetch_arxiv
fetch_huggingface
merge_source_units
normalize
filter_by_time_window
dedupe
rank_bm25
select
Responsabilidad:
obtener papers
normalizar resultados
filtrar
ordenar
seleccionar candidatos
Salida principal:
selected_items
4.2 HITL
Nodo:
hitl_review
Responsabilidad:
revisión humana
eliminación opcional de items
Salidas:
hitl_action
hitl_remove_keys
4.3 Summarize
Nodos:
summarize_map
summarize_reduce
Responsabilidad:
generar resúmenes
consolidar el resultado final
Salida pública:
output
5. Entrada del sistema
El sistema acepta un único payload JSON:
{
  "query": "string",
  "time_window": "enum",
  "top_k": "integer"
}
Reglas:
query
MUST ser string no vacío
time_window
MUST pertenecer al enum permitido
top_k
MUST ser entero positivo
La validación concreta pertenece al nodo validate_input.
6. Salidas del sistema
6.1 Ejecución exitosa completa
El resultado MUST contener:
summary_items
summary_stats
output
output es el artefacto público final del sistema.
6.2 Ejecución parcial
La ejecución parcial depende del parámetro execute_until.
execute_until = select
Resultado mínimo:
ranked_items
selected_items
Las siguientes claves MUST NOT existir:
hitl_action
summary_items
summary_stats
output
execute_until = summary
Resultado equivalente a ejecución completa.
7. Abort global
El sistema utiliza un set cerrado de abort_reason.
EMPTY_INPUT_PAYLOAD
INVALID_QUERY
INVALID_TIME_WINDOW
INVALID_TOP_K
UNKNOWN_SOURCE_PRIORITY
FETCH_ALL_SOURCES_FAILED
NO_ITEMS_IN_TIME_WINDOW
NO_ITEMS_AFTER_DEDUPE
RANK_QUERY_EMPTY_AFTER_NORMALIZATION
SELECT_MISSING_RANKED_ITEMS
SELECT_TOPK_INVALID
SUMMARY_EMPTY_INPUT
SUMMARY_ALL_ITEMS_FAILED
USER_ABORT
No se permiten valores adicionales.
Reglas globales de abort
Si existe abort_reason:
el pipeline se detiene
no se ejecutan nodos posteriores
output MUST NOT existir
8. Ejecución parcial
El sistema admite ejecución parcial mediante un parámetro externo:
execute_until
Valores permitidos:
select
summary
Reglas:
select
ejecuta Retrieval completo
no ejecuta HITL
no ejecuta Summarize
summary
ejecuta el pipeline completo
9. Equivalencias estructurales
Estas equivalencias deben cumplirse siempre.
9.1 Equivalencia Retrieval
system.invoke(payload, execute_until="select")
debe producir un state idéntico a:
retrieval_graph.invoke(payload)
Dos states se consideran idénticos si:
contienen exactamente las mismas claves
los valores asociados a cada clave son iguales
las listas mantienen el mismo orden
las estructuras internas de los items son equivalentes
9.2 Equivalencia HITL
hitl_graph.invoke(state)
debe ser equivalente a la ejecución del sistema entre:
select → summarize_map
9.3 Equivalencia Summarize
summarize_graph.invoke(state)
debe ser equivalente a la ejecución del sistema entre:
summarize_map → summarize_reduce
10. No objetivos
Este contrato no cubre:
persistencia
observabilidad
métricas
paralelismo
streaming
expansión de fuentes
11. Garantías del sistema
El sistema garantiza:
pipeline determinista
contratos de fase independientes
state gobernado
abort consistente
equivalencia entre subgrafos y sistema completo