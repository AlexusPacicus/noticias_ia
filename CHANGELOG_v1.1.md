# Changelog v1 -> v1.1

Cambios entre el baseline `v1.0.0` (FROZEN, legacy) y `v1.1` (activo).

## 1. Runtime

- `v1`: runtime manual en `run_real_pipeline.py` con loop secuencial.
- `v1.1`: runtime oficial en LangGraph (`graph/graph.py:graph`) via `graph.invoke(...)`.

## 2. Abort handling

- `v1`: los nodos abortaban via `raise ValueError(...)`; el runner escribia `abort_reason`.
- `v1.1`: los nodos retornan `{"abort_reason": "CODIGO"}` y el grafo corta via conditional edge a `END`.

## 3. State e I/O

- Se introduce `graph/state.py` con `InputState`, `OutputState` y `PipelineState`.
- El estado interno pasa a merge por deltas (sin mutacion in-place en nodos).
- `OutputState` limita la salida publica a `output` o `abort_reason`.

## 4. Serializacion

- `external_units` deja de transportar XML crudo y pasa a dicts serializables.
- Esto permite mejor compatibilidad con serving/checkpointing.

## 5. Runner local

- `run_pipeline.py` queda como entrypoint liviano para `graph.invoke(...)`.
- El runtime manual historico se conserva en `codex/legacy-v1` / `v1.0.0`.

## 6. Tests

- Los tests se alinean al runtime de grafo (`graph.invoke`).
- Las verificaciones de abort se hacen sobre `result["abort_reason"]`.
- Markers centralizados en `pytest.ini` de raiz.

## 7. Documentacion

- `v1` movido a `docs/legacy/v1/` (solo historico, FROZEN).
- `v1.1` activo en `docs/v1.1/`.
- `README.md` reescrito para reflejar una sola verdad operativa: LangGraph como runtime oficial.

## 8. Compatibilidad funcional

`v1.1` mantiene el pipeline y codigos de abort operativos, cambiando solo la capa de ejecucion y gobernanza del estado.
