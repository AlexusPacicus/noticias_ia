# Contrato de Runtime - v1.1

## 1. Estado

- Version: v1.1
- Estado: ACTIVE

## 2. Runtime oficial unico

El runtime oficial de v1.1 es el grafo compilado de LangGraph exportado como `graph` en:

- `graph/graph.py:graph`

Toda ejecucion del pipeline v1.1 debe ocurrir via:

- `graph.invoke(input)`

`run_pipeline.py` es solo un entrypoint de conveniencia y delega al runtime oficial (`graph.invoke`).

Este contrato complementa `docs/v1.1/Contrato_Sistema_v1.1.md`.

## 3. Semantica de abort contractual

- Los nodos no usan excepciones para abort contractual.
- Un nodo aborta retornando `{"abort_reason": "CODIGO"}`.
- El router condicional del grafo detecta `abort_reason` y redirige a `END`.
- En abort no se emiten resultados parciales.

## 4. Contrato I/O publico

- Input publico: `InputState` (definido en `graph/state.py`).
- Output publico: `OutputState` (definido en `graph/state.py`).
- Los campos internos del pipeline no forman parte del output publico.

## 5. Compatibilidad con v1

El contrato v1 permanece FROZEN e intacto como registro historico.

v1.1 sustituye unicamente la capa de runtime y formaliza LangGraph como ejecucion oficial.
