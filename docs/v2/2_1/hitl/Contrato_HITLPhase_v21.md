1. Scope
HITLPhase v2.1 define un subgrafo independiente cuya única responsabilidad es permitir la intervención humana para:
Aceptar resultados seleccionados.
Eliminar subconjunto de resultados.
Cancelar ejecución.
No modifica RetrievalPhase.
No modifica SummarizePhase.
2. Frontera
Incluye exclusivamente:
Nodo: hitl_review
Se ejecuta estrictamente después de select y antes de summarize_map.
No contiene loops.
No contiene LLM.
No contiene llamadas externas.
3. Inputs (read-only)
HITLPhase MUST leer únicamente:
selected_items
HITLPhase MUST NOT leer:
ranked_items
source_units
abort_reason
cualquier clave previa a select
4. Outputs (write-only)
HITLPhase MAY escribir:
hitl_action
hitl_remove_keys
abort_reason (solo en cancel)
HITLPhase MUST NOT escribir:
claves de Retrieval
claves de Summarize
output
5. Identidad
La identidad contractual de cada item es:
canonical_id
hitl_remove_keys es una lista de canonical_id.
No se permite ningún otro identificador.
6. Acciones válidas (enum cerrado)
"accept"
"subset"
"cancel"
No existen otras acciones.
7. Semántica
7.1 accept
MUST:
hitl_action = "accept"
hitl_remove_keys = []
No debe existir abort_reason.
7.2 subset
MUST:
hitl_action = "subset"
hitl_remove_keys ⊆ {canonical_id(selected_items)}
Reglas:
No duplicados.
No ids inexistentes.
No puede ser vacío (si vacío → debe ser "accept").
No puede introducir nuevos ids.
7.3 cancel
MUST:
hitl_action = "cancel"
abort_reason = "USER_ABORT"
MUST NOT existir:
hitl_remove_keys
Abort dominante limpio.
8. Invariantes
HITLPhase MUST:
No modificar selected_items.
No reordenar items.
No crear nuevos items.
No mutar contenido.
No cambiar top_k.
Ser determinista dado input humano.
HITLPhase MUST NOT:
Re-rankear.
Re-fetch.
Ejecutar LLM.
Escribir claves fuera de su dominio.
9. Aplicación posterior (fuera de esta fase)
SummarizePhase calculará:
final_items = selected_items - hitl_remove_keys
HITLPhase no ejecuta esta operación.
Solo declara intención.
10. Abort Policy
HITLPhase solo puede emitir:
USER_ABORT
No puede emitir aborts de Retrieval ni de Summarize.
11. Independencia Ejecutable
HITLPhase MUST poder ejecutarse de forma aislada:
hitl_graph.invoke(state_con_selected_items, decision)
El resultado debe ser equivalente a ejecutar el sistema completo desde select hasta antes de summarize_map.