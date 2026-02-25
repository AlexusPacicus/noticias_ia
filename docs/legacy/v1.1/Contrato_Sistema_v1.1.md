# Contrato de Sistema - v1.1

## 1. Estado

- Version: v1.1
- Estado: ACTIVE

## 2. Runtime oficial

El runtime oficial del sistema es el grafo compilado exportado como `graph` en:

- `graph/graph.py:graph`

La ejecucion contractual ocurre via `graph.invoke(input)`.

## 3. Pipeline contractual

Orden fijo e inmutable:

`collect_input -> validate_input -> fetch -> normalize -> rank -> select -> summarize`

Ningun nodo puede alterar el orden o reejecutar nodos previos.

## 4. Contrato I/O

Input (`InputState`):

- `query: str`
- `time_window: "last_24h" | "last_3_days" | "last_7_days"`
- `top_k: int` opcional (default `5`, rango `[1..10]`)

Output (`OutputState`):

- `output` (ejecucion exitosa)
- `abort_reason` (ejecucion abortada)

Schema de `output`:

```json
{
  "topic": "string",
  "time_window": "string",
  "results": [
    {
      "title": "string",
      "idea_clave": "string (<= 80 palabras)",
      "relacion_con_query": "string (<= 30 palabras)",
      "link": "string"
    }
  ]
}
```

## 5. Semantica de abort

- Los nodos abortan retornando `{"abort_reason": "CODIGO"}`.
- El router condicional redirige a `END` cuando detecta `abort_reason`.
- No hay resultados parciales.

## 6. Invariantes

- Determinismo estructural: mismo input + mismo snapshot de fuente => mismo conjunto/orden.
- El LLM solo transforma texto en `summarize`; no decide ranking/seleccion.
- El estado interno se construye por deltas, sin mutacion in-place.
- `output` y `abort_reason` no coexisten en una ejecucion abortada.

## 7. Codigos de abort operativos

- `EMPTY_INPUT_PAYLOAD`
- `INVALID_QUERY`
- `INVALID_TIME_WINDOW`
- `INVALID_TOP_K`
- `FETCH_SOURCE_ERROR`
- `FETCH_NOT_ITERABLE`
- `NORMALIZE_MISSING_TITLE`
- `NORMALIZE_MISSING_LINK`
- `NORMALIZE_MISSING_CONTENT`
- `RANK_QUERY_EMPTY_AFTER_NORMALIZATION`
- `SELECT_MISSING_RANKED_ITEMS`
- `SELECT_TOPK_INVALID`
- `SUMMARY_LLM_RUNTIME_ERROR`
- `SUMMARY_SCHEMA_VIOLATION`

## 8. Relacion con v1

`v1` permanece FROZEN como legacy historico en `docs/legacy/v1/`.

La ejecutabilidad de v1 se conserva en:

- `tag v1.0.0`
- `branch codex/legacy-v1`
