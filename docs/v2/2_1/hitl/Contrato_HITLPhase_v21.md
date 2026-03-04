1. Estado
Versión: v2.1
Estado: DRAFT
Tipo: Contrato de Fase
Fase: HITLPhase

2. Scope
HITLPhase define un subgrafo independiente cuya única responsabilidad es permitir la intervención humana para:
Aceptar resultados seleccionados.
Eliminar subconjunto de resultados.
Cancelar ejecución.
HITLPhase:
No modifica RetrievalPhase.
No modifica SummarizePhase.
No recalcula ranking.
No ejecuta lógica de negocio adicional.

3. Frontera
Incluye exclusivamente:
Nodo: hitl_review
Se ejecuta estrictamente:
Después de select
Antes de summarize_map
No contiene:
Loops
LLM
Fetch
Re-ranking
Llamadas externas
4. Inputs (read-only)
HITLPhase MUST leer únicamente:
selected_items
HITLPhase MUST NOT leer:
ranked_items
source_units
abort_reason
hitl_action
hitl_remove_keys
hitl_selected_items
Cualquier clave previa a select distinta de selected_items

5. Outputs (write-only)
HITLPhase MAY escribir:
hitl_action
hitl_remove_keys
abort_reason (solo en caso de cancel)
HITLPhase MUST NOT escribir:
Claves de Retrieval
Claves de Summarize
output
hitl_selected_items

6. Identidad
La identidad contractual de cada item es:
canonical_id
hitl_remove_keys es una lista de canonical_id.
No se permite ningún otro identificador.

7. Acciones válidas (enum cerrado)
"accept"
"subset"
"cancel"
No existen otras acciones.

8. Semántica

8.1 accept
MUST:
hitl_action = "accept"
hitl_remove_keys = []
MUST NOT existir:
abort_reason

8.2 subset
MUST:
hitl_action = "subset"
hitl_remove_keys ⊆ {canonical_id(selected_items)}
Reglas:
No duplicados.
No ids inexistentes.
No puede introducir nuevos ids.
Puede eliminar todos los elementos.
MUST NOT:
Crear nuevos items.
Reordenar.
Mutar contenido.

8.3 cancel
MUST:
hitl_action = "cancel"
abort_reason = "USER_ABORT"
MUST NOT existir:
hitl_remove_keys
En caso de cancel:
No deben crearse claves posteriores.
Se activa abort dominante.
La ejecución del sistema debe detenerse inmediatamente tras este nodo.

9. Invariantes
HITLPhase MUST:
No modificar selected_items.
No reordenar items.
No crear nuevos items.
No mutar contenido.
No cambiar top_k.
Determinismo condicionado:
Dado el mismo selected_items y la misma decisión humana,
el resultado de hitl_review MUST ser idéntico.
HITLPhase MUST NOT:
Re-rankear.
Re-fetch.
Ejecutar LLM.
Escribir claves fuera de su dominio.

10. Aplicación posterior (fuera de esta fase)
SummarizePhase calculará:
final_items = selected_items - hitl_remove_keys
HITLPhase:
No ejecuta esta operación.
No materializa hitl_selected_items.
Solo declara intención.

11. Abort Policy
HITLPhase puede emitir exclusivamente:
USER_ABORT
HITLPhase NO puede emitir:
Aborts de Retrieval
Aborts de Summarize

12. State retornado
Ejecución no abortada
El state MUST contener:
selected_items
hitl_action
hitl_remove_keys
No debe existir:
abort_reason
Ejecución con cancel
El state MUST contener:
selected_items
hitl_action
abort_reason
No debe existir:
hitl_remove_keys
No deben existir claves posteriores al nodo.

13. Independencia Ejecutable
HITLPhase MUST poder ejecutarse de forma aislada:
hitl_graph.invoke(state_con_selected_items, decision)
El resultado MUST ser equivalente a ejecutar el sistema completo desde select hasta antes de summarize_map.