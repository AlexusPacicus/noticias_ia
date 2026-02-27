1. Estado
Version: v2
Estado: FROZEN
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2

2. Rol
Procesar secuencialmente selected_items para generar resúmenes individuales y materializar summary_stats.

2.b Dependencia externa
Este nodo depende contractualmente de:
`Contrato_LLM_v2`

3. Reads (lista cerrada)
`selected_items`
Reglas:
- MUST invocar la capa generativa definida en Contrato_LLM_v2.
- MUST respetar estrictamente la configuración técnica congelada allí.
- MUST validar el output según el schema definido en Contrato_LLM_v2.
- MUST contabilizar como failed cualquier violación del schema o error tras aplicar la política de reintentos.
- MUST NOT alterar la configuración del modelo desde este nodo.
- La topología del grafo NO depende del modelo específico.

4. Writes (creador único)
summary_stats
summary_items

Reglas:
- MUST ejecutar el proceso de resumen de forma secuencial y determinista respecto al orden de selected_items.
- MUST intentar generar un resumen para cada elemento.
summary_stats MUST contener:
    - ok: número de resúmenes válidos.
    - failed: número de resúmenes fallidos.
- MUST NOT abortar por fallo individual.
- MUST retornar únicamente el delta.
- MUST NOT modificar selected_items.
- La generación del resumen MUST realizarse exclusivamente a través de la capa definida en Contrato_LLM_v2.

5. Abort (exclusivos)
(none)
Reglas:
- MUST NOT emitir abort_reason.

6. Invariantes locales
summary_stats.ok + summary_stats.failed == len(selected_items).
len(summary_items) == summary_stats.ok
summary_items es subconjunto posicional de selected_items

7. Prohibiciones
MUST NOT emitir abort_reason
MUST NOT crear output
MUST NOT modificar selected_items