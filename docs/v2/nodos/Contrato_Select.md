# Contrato_Nodo_select_v2

## 1. Estado
- Version: v2
- Estado: DRAFT
- Pertenece a: Contrato_Sistema_v2
- Gobernado por: Contrato_State_v2

## 2. Rol
Seleccionar los primeros elementos de `ranked_items` según `top_k` validado y producir `selected_items`.

## 3. Reads (lista cerrada)
- ranked_items
- input_validated.top_k

## 4. Writes (creador único)
- selected_items

Reglas:
- MUST calcular `effective_k = min(top_k, len(ranked_items))`.
- MUST producir `selected_items = ranked_items[:effective_k]`.
- MUST preservar el orden original.
- MUST retornar únicamente el delta.
- MUST NOT modificar `ranked_items`.

## 5. Abort (exclusivos)
- SELECT_MISSING_RANKED_ITEMS
- SELECT_TOPK_INVALID

Reglas:
- Si `ranked_items` no existe o es inválido → emitir `SELECT_MISSING_RANKED_ITEMS`.
- Si `top_k` es inválido en runtime → emitir `SELECT_TOPK_INVALID`.
- Si retorna `abort_reason` → no crea claves posteriores.
- No lanza excepciones para abort contractual.

## 6. Invariantes locales
- `selected_items` es prefijo de `ranked_items`.
- `len(selected_items) <= top_k`.

## 7. Prohibiciones
- MUST NOT reordenar elementos.
- MUST NOT recalcular ranking.
- MUST NOT crear claves fuera de `selected_items`.
- MUST NOT emitir abort distinto a los declarados.
