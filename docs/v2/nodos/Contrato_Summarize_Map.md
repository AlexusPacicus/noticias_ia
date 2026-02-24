1. Estado
Version: v2
Estado: DRAFT
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2

2. Rol
Procesar secuencialmente selected_items para generar resúmenes individuales y materializar summary_stats.

3. Reads (lista cerrada)
selected_items

4. Writes (creador único)
summary_stats
summary_items

Reglas:
MUST ejecutar el proceso de resumen de forma secuencial y determinista respecto al orden de selected_items.
MUST intentar generar un resumen para cada elemento.
summary_stats MUST contener:
ok: número de resúmenes válidos.
failed: número de resúmenes fallidos.
MUST NOT abortar por fallo individual.
MUST retornar únicamente el delta.
MUST NOT modificar selected_items.

5. Abort (exclusivos)
(none)
Reglas:
Este nodo MUST NOT emitir abort_reason.

6. Invariantes locales
summary_stats.ok + summary_stats.failed == len(selected_items).
len(summary_items) == summary_stats.ok
summary_items es subconjunto posicional de selected_items

7. Prohibiciones
MUST NOT emitir abort_reason
MUST NOT crear output
MUST NOT modificar selected_items