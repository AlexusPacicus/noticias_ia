HITLPhase v2.1 — Scope Final (FROZEN)
1. Propósito
Permitir únicamente que el usuario elimine elementos del top_k o cancele.
No reconstruye listas.
No transforma datos.
No reordena.
No reevalúa.
2. Inputs (read-only)
selected_items (desde Retrieval, FROZEN)
Prohibido leer cualquier otra clave.
3. Outputs (write-only)
hitl_action: "accept" | "subset" | "cancel"
hitl_remove_keys: list[str] (solo si action = subset)
abort_reason = "USER_ABORT" (solo si cancel)
Nada más.
4. Semántica Mecánica
accept
hitl_action = "accept"
hitl_remove_keys = []
subset
hitl_action = "subset"
hitl_remove_keys ⊂ ids(selected_items)
Reglas:
Debe ser subconjunto válido.
No puede contener ids inexistentes.
No puede introducir ids nuevos.
cancel
hitl_action = "cancel"
abort_reason = "USER_ABORT"
Y:
hitl_remove_keys MUST NOT existir.
No deben coexistir resultados posteriores.
5. Regla de Aplicación (fuera de HITL)
SummarizePhase calculará:
final_items = selected_items - hitl_remove_keys
HITL no ejecuta esta operación.
Solo declara intención.
6. Identidad (decisión pendiente crítica)
Necesitas cerrar qué es una “key”:
Recomendación fuerte:
canonical_id
No uses solo rank_position. Es frágil ante cambios futuros.
7. Invariantes
HITL MUST:
No modificar contenido.
No reordenar.
No duplicar estructuras.
No crear nuevas entidades.
Ser determinista dado input humano.
HITL MUST NOT:
Re-rankear.
Re-fetch.
Cambiar top_k.
Escribir claves de Retrieval o Summarize.