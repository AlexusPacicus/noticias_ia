# CHANGELOG `2.1`

## Structural refactor
- separación de builders canónicos, nodos puros y utilidades runtime

## Builder ownership normalization
- `graph/v2_1/*/graph_21.py` concentra la lógica real de construcción

## Runtime wrapper conversion
- `graph/v2_1/runtime.py` queda como wrapper puro de compatibilidad

## Known limitations
- `graph/v2/nodes/summarize_map.py` sigue legacy por monkeypatching de tests
- `graph/v2/nodes/filter_by_time_window.py` sigue legacy por monkeypatching de tests
