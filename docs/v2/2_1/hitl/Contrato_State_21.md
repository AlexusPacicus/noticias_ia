1. Nuevas claves añadidas
Se amplía la lista cerrada de claves con:
hitl_action: str
hitl_remove_keys: list[str]
Y se amplía el conjunto cerrado de abort codes con:
USER_ABORT
Nada más.
2. Writers
hitl_action
Writer único: hitl_review
hitl_remove_keys
Writer único: hitl_review
abort_reason
Writers permitidos:
nodos previos (ya definidos en v2)
hitl_review (solo si action = cancel)
3. Readers
hitl_action
summarize_map
summarize_reduce
hitl_remove_keys
summarize_map
4. Reglas de coexistencia
Regla 1 — Abort dominante
Si existe:
abort_reason = "USER_ABORT"
Entonces:
hitl_remove_keys MUST NOT existir
No deben existir claves de Summarize
No debe existir output
Regla 2 — Acción vs abort
Si:
hitl_action = "cancel"
Debe existir abort_reason = "USER_ABORT"
Si action ≠ cancel → abort_reason MUST NOT existir.
Regla 3 — Integridad
Si:
hitl_action = "subset"
Entonces:
hitl_remove_keys MUST existir
Debe ser lista no vacía
Si:
hitl_action = "accept"
Entonces:
hitl_remove_keys MUST existir
Debe ser lista vacía