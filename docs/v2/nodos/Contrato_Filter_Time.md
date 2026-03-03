1. Estado
Version: v2
Estado: FROZEN
Pertenece a: Contrato_Sistema_v2
Gobernado por: Contrato_State_v2

2. Rol
Aplicar la ventana temporal validada sobre normalized_items y materializar filtered_items como subconjunto que preserva el orden original, activando el gate correspondiente si el resultado es vacío.

3. Reads (lista cerrada)
normalized_items
input_validated.time_window

4. Writes (creador único)
filtered_items
Reglas:
MUST preservar el orden heredado de normalized_items.
MUST evaluar la ventana temporal respecto a published_at ya normalizado.
MUST calcular now_utc una única vez al inicio del nodo.
MUST definir cutoff = now_utc - delta(time_window).
La comparación MUST ser inclusiva: published_at >= cutoff.
MUST descartar elementos con published_at inválido.
MUST retornar únicamente el delta.
MUST NOT modificar normalized_items.

5. Abort (exclusivos)
NO_ITEMS_IN_TIME_WINDOW
Reglas:
Si len(filtered_items) == 0 → emitir abort_reason.
Si retorna abort_reason → no crea claves posteriores.
No lanza excepciones para abort contractual.

6. Invariantes locales
filtered_items es subconjunto de normalized_items y preserva su orden relativo.

7. Prohibiciones
MUST NOT leer query
MUST NOT leer ranked_items
MUST NOT crear claves fuera de filtered_items
MUST NOT emitir abort distinto al declarado
