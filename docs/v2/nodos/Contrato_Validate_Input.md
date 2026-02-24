# Contrato_Nodo_validate_input_v2

## 1. Estado
- Version: v2
- Estado: DRAFT
- Pertenece a: Contrato_Sistema_v2
- Gobernado por: Contrato_State_v2

## 2. Rol
Aplicar las reglas contractuales de entrada y producir `input_validated`.

## 3. Reads
- input_raw

## 4. Writes
- input_validated

Reglas:
- query MUST ser tipo str y tener longitud > 0.
- time_window MUST ser exactamente uno de:
  - last_24h
  - last_3_days
  - last_7_days
- top_k:
  - Si ausente → asignar 3.
  - Si presente → MUST ser int en rango [1..5].

## 5. Abort
- INVALID_QUERY
- INVALID_TIME_WINDOW
- INVALID_TOP_K
