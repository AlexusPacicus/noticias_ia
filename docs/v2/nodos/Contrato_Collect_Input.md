# Contrato_Nodo_collect_input_v2

## 1. Estado
- Version: v2
- Estado: DRAFT
- Pertenece a: Contrato_Sistema_v2
- Gobernado por: Contrato_State_v2

## 2. Rol
Recoger el input dado por el usuario y almacenarlo en `input_raw` sin modificarlo.

## 3. Reads
- query
- time_window
- top_k (puede estar ausente)

## 4. Writes
- input_raw

Regla:
- Debe crear `input_raw` con exactamente las claves leídas en Reads.

## 5. Abort
- EMPTY_INPUT_PAYLOAD

## 6. Prohibiciones
- MUST NOT aplicar validación ni defaults.
- MUST NOT modificar valores del input.
- MUST NOT crear claves fuera de `input_raw`.
