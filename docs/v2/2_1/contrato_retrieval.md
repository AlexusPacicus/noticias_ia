📄 Contrato_Retrieval_v2.1
1. Estado
Versión: v2.1
Estado: DRAFT
Tipo: Contrato de Fase
Fase: RetrievalPhase


Dependencias:
Contrato_Sistema_v2.1
Contrato_State_v2.1
Este documento delimita la frontera de la fase Retrieval y no redefine reglas globales del sistema.


2. Contexto
RetrievalPhase es una unidad estructural reutilizable del motor AI Papers Engine.
Su responsabilidad es:
Transformar parámetros de búsqueda en un conjunto ordenado y seleccionado de papers, sin intervención de modelos LLM.
RetrievalPhase DEBE poder ejecutarse de forma independiente.
3. Alcance (Scope)
RetrievalPhase comprende exclusivamente los siguientes nodos:
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
La fase termina estrictamente tras la ejecución de select.

RetrievalPhase NO DEBE incluir nodos de HITL ni nodos de SummarizePhase.
RetrievalPhase MUST NOT crear:
hitl_action
hitl_remove_keys
hitl_selected_items

4. Entradas
RetrievalPhase acepta exclusivamente el siguiente objeto de entrada:
{
  "query": "string",
  "time_window": "enum permitido",
  "top_k": "int positivo"
}
Las validaciones de estos campos se rigen por lo definido en Contrato_Sistema_v2.
5. Salidas
En ejecución exitosa, RetrievalPhase DEBE producir:
ranked_items
selected_items
RetrievalPhase NO DEBE producir:
summary_items
summary_stats
output
Estas claves pertenecen exclusivamente a fases posteriores.
6. Semántica de Gates
RetrievalPhase PUEDE emitir exclusivamente los aborts correspondientes a:
Gate A — Error de validación de entrada
Gate B — Error en fetch
Gate C — Sin elementos tras filtrado estructural
Gate D — Sin elementos tras ranking
Gate E — Sin elementos tras select
RetrievalPhase NO PUEDE emitir:
SUMMARY_ALL_ITEMS_FAILED
En caso de abort:
El state DEBE contener abort_reason
NO DEBEN crearse claves posteriores al punto de fallo
ranked_items y selected_items NO DEBEN existir si el abort ocurre antes de su generación
RetrievalPhase puede emitir exclusivamente:

EMPTY_INPUT_PAYLOAD
INVALID_QUERY
INVALID_TIME_WINDOW
INVALID_TOP_K
FETCH_ALL_SOURCES_FAILED
UNKNOWN_SOURCE_PRIORITY
NO_ITEMS_IN_TIME_WINDOW
NO_ITEMS_AFTER_DEDUPE
RANK_QUERY_EMPTY_AFTER_NORMALIZATION
SELECT_MISSING_RANKED_ITEMS
SELECT_TOPK_INVALID

Reglas específicas por Gate:

Gate A:
No debe existir input_validated ni claves posteriores.

Gate B:
No debe existir merged_source_units ni claves posteriores.

Gate C (filter):
No debe existir deduped_items ni claves posteriores.

Gate C (dedupe):
No debe existir ranked_items ni claves posteriores.

Gate D:
ranked_items MUST NOT existir.

Gate E:
ranked_items MUST existir.
selected_items MUST NOT existir.

7. Invariantes
RetrievalPhase DEBE cumplir las siguientes condiciones:

Determinismo estructural total:
RetrievalPhase MUST produce identical ranked_items and selected_items
given:
- mismo input
- mismas respuestas de las fuentes externas (contenido y orden idénticos)
- mismo SOURCE_PRIORITY
- mismos parámetros BM25

No uso de modelos LLM.
La deduplicación DEBE realizarse exclusivamente por canonical_id.
El ranking DEBE realizarse exclusivamente mediante la estrategia BM25 activa.
No dependencia de fases posteriores.
No modificación de claves ajenas a esta fase.

8. Prohibiciones
RetrievalPhase NO DEBE:
Invocar modelos LLM.
Crear claves posteriores a select.
Alterar el ranking una vez generado.
Introducir decisiones basadas en métricas.
Modificar el modelo de ejecución global del sistema.
9. No-Objetivos
Este contrato NO define:
Persistencia
Reanudación
Multi-LLM
Observabilidad
HITL
Cambios en el contrato global del sistema
10. Independencia de Ejecución
RetrievalPhase DEBE poder compilarse y ejecutarse de forma independiente:
retrieval_graph.invoke(...)
El resultado DEBE ser idéntico al del sistema completo hasta el nodo select.
11. Referencias
Contrato_Sistema_v2.1
Contrato_State_v2.1
Contrato_LLM_v2.1
Diseno_v2

12. Equivalencia estructural con el sistema completo
RetrievalPhase es un subgrafo estructural interno del pipeline v2.1.
RetrievalPhase MUST ser semánticamente equivalente a ejecutar el sistema completo hasta el nodo select, bajo las siguientes condiciones:
Sin ejecución de HITL.
Sin ejecución de SummarizePhase.
Sin creación de summary_items, summary_stats ni output.
Equivalente a ejecutar el pipeline completo con execute_until="select".
Cualquier divergencia entre:
system_full.invoke(..., execute_until="select")
retrieval_graph.invoke(...)
constituye una violación contractual.
13. State retornado
RetrievalPhase MUST devolver el state completo acumulado hasta el nodo select.
En ejecución exitosa, el state MUST contener:
query
time_window
top_k
input_raw
input_validated
source_units
merged_source_units
normalized_items
filtered_items
deduped_items
ranked_items
selected_items
RetrievalPhase MUST NOT crear:
summary_items
summary_stats
output
RetrievalPhase MUST NOT crear abort_reason en ejecución exitosa.
En caso de abort, aplican las reglas de existencia definidas en Contrato_State_v2.1.
14. Orden total congelado
RetrievalPhase MUST respetar el orden total determinista definido en el sistema v2:
(-bm25_score, title ASC, link ASC)
No se permite:
Reranking posterior.
Estrategias alternativas activas.
Dependencia de métricas externas.
La estrategia activa en v2.1 es exclusivamente BM25.