1. Estado
Version: v2
Estado: FROZEN
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2
2. Rol
Eliminar duplicados por igualdad exacta de canonical_id en filtered_items y producir deduped_items, preservando el orden determinista heredado.
3. Reads (lista cerrada)
filtered_items
4. Writes (creador único)
deduped_items
Reglas:
MUST identificar duplicados únicamente por igualdad exacta de canonical_id.
MUST conservar la primera aparición según el orden heredado.
MUST descartar apariciones posteriores con el mismo canonical_id.
MUST preservar el orden relativo de los elementos retenidos.
MUST retornar únicamente el delta.
MUST NOT modificar filtered_items.
5. Abort (exclusivos)
NO_ITEMS_AFTER_DEDUPE
Reglas:
Si len(deduped_items) == 0 → emitir abort_reason.
Si retorna abort_reason → no crea claves posteriores.
No lanza excepciones para abort contractual.
6. Invariantes locales
deduped_items es subconjunto de filtered_items.
Cada canonical_id aparece como máximo una vez.
7. Prohibiciones
MUST NOT reordenar elementos.
MUST NOT crear claves fuera de deduped_items.
MUST NOT emitir abort distinto al declarado.