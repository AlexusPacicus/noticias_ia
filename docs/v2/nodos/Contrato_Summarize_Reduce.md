1. Estado
Version: v2
Estado: DRAFT
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2

2. Rol
Construir output a partir de selected_items y summary_stats, preservando el rank_position original y activando el gate correspondiente si no existen resúmenes válidos.

3. Reads (lista cerrada)
summary_items
summary_stats
input_validated.query
input_validated.time_window
input_validated.top_k

4. Writes (creador único)
output
Reglas:
MUST construir resultados exclusivamente a partir de summary_items.
MUST preservar el rank_position asignado en rank_bm25.
MUST reordenar resultados por rank_position ascendente.
MUST establecer en output:
topic = input_validated.query
time_window = input_validated.time_window
requested_k = input_validated.top_k
returned_k = número de resultados válidos
failed_summaries = summary_stats.failed
MUST retornar únicamente el delta.

5. Abort (exclusivos)
SUMMARY_ALL_ITEMS_FAILED
Reglas:
Si summary_stats.ok == 0 → emitir abort_reason.
Si retorna abort_reason → MUST NOT crear output.
No lanza excepciones para abort contractual.

6. Invariantes locales
returned_k <= requested_k.
output y abort_reason son mutuamente excluyentes.
len(summary_items) == summary_stats.ok

7. Prohibiciones
MUST NOT recalcular ranking.
MUST NOT modificar claves previas.
MUST NOT crear claves fuera de output.

