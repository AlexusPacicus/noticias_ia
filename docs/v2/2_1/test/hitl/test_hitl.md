1. Scope
Este documento define los tests contractuales que validan HITLPhase v2.1 como subgrafo independiente.
No valida:
RetrievalPhase
SummarizePhase
Aplicación de eliminación
Valida únicamente:
Semántica declarativa
Gobernanza de claves
Invariantes estructurales
2. Tipos de test
2.1 Unit — Nodo hitl_review
Valida contrato interno del nodo.
2.2 Subgraph isolation
Valida que HITLPhase puede ejecutarse con state mínimo válido sin depender de otras fases.
3. Matriz mínima de casos
3.1 Accept
Caso:
selected_items con N elementos
decision.action = "accept"
Expect:
hitl_action == "accept"
hitl_remove_keys == []
abort_reason no existe
3.2 Subset
3.2.1 Eliminación simple
remove_keys con 1 canonical_id válido
resultado correcto
sin abort
3.2.2 Eliminación múltiple
remove_keys con varios ids válidos
resultado correcto
sin abort
3.2.3 Subset total
remove_keys contiene todos los ids
permitido
sin abort en HITL
Nota:
Si esto produce lista vacía, el posible abort pertenece a SummarizePhase, no a HITLPhase.
3.3 Cancel
Caso:
decision.action = "cancel"
Expect:
hitl_action == "cancel"
abort_reason == "USER_ABORT"
hitl_remove_keys no existe
no coexistencia con claves posteriores
4. Invariantes estructurales
4.1 No mutación
selected_items debe permanecer estructuralmente idéntico antes y después de la ejecución.
4.2 Dominio de claves
El state resultante solo puede contener:
claves originales
hitl_action
hitl_remove_keys (si aplica)
abort_reason (si cancel)
No se permiten claves adicionales.
4.3 Determinismo
Dado:
mismo selected_items
misma decision
El resultado debe ser estructuralmente idéntico.
5. Exclusiones explícitas
No se testea:
Aplicación de eliminación
Cardinalidad final
Lógica de Summarize
Runtime completo del sistema
6. Criterio de cierre
HITLPhase v2.1 se considera validado cuando:
Todos los casos anteriores pasan
No se muta input
No se escriben claves fuera del dominio
Cancel produce abort dominante limpio
Estado
Documento:
Minimalista
Enfocado
No sobreingenierizado
Coherente con modelo declarativo
Compatible con Retrieval FROZEN