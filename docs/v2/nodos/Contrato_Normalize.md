# Contrato_Nodo_normalize_v2

## 1. Estado
- Version: v2
- Estado: FROZEN
- Pertenece a: Contrato_Sistema_v2
- Gobernado por: Contrato_State_v2

## 2. Rol
Transformar `merged_source_units` en `normalized_items` con el schema común definido en Diseño v2.

## 3. Reads (lista cerrada)
- merged_source_units

## 4. Writes (creador único)
- normalized_items

Reglas:
- MUST preservar el orden heredado de `merged_source_units`.
- MUST generar `canonical_id` no vacío y determinista.
- MUST descartar cualquier item cuyo canonical_id resulte vacío o None.
- MUST descartar items sin published_at parseable.
- MUST descartar items sin title no vacío.

## 5. Abort
(none)

Reglas:
- Este nodo MUST NOT emitir `abort_reason`.

## 6. Prohibiciones
- MUST NOT realizar ranking.
- MUST NOT realizar deduplicación.
- MUST NOT reordenar elementos.
- MUST NOT crear claves fuera de `normalized_items`.
