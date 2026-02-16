# noticias - v1.1

Sistema de seleccion y resumen de items recientes de IA con runtime oficial en LangGraph.

## Estado actual

- Version activa: `v1.1`
- Runtime oficial: `graph/graph.py:graph`
- Entry point local: `run_pipeline.py` (delegado a `graph.invoke`)
- Legacy ejecutable v1: `tag v1.0.0` y `branch codex/legacy-v1`

## Runtime oficial (v1.1)

El pipeline se ejecuta unicamente via `graph.invoke(input)` sobre el grafo compilado:

- `graph/graph.py`
- `langgraph.json` -> `./graph/graph.py:graph`

Semantica de abort contractual en v1.1:

- Cada nodo aborta retornando `{"abort_reason": "CODIGO"}`.
- El router condicional del grafo redirige a `END` cuando detecta `abort_reason`.
- No se devuelven resultados parciales.

## Pipeline

Orden fijo:

`collect_input -> validate_input -> fetch -> normalize -> rank -> select -> summarize`

## Contrato I/O publico

Input (`InputState`):

- `query: str`
- `time_window: "last_24h" | "last_3_days" | "last_7_days"`
- `top_k: int` (opcional, default `5`, rango `[1..10]`)

Output (`OutputState`):

- `output` o `abort_reason`

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

## Ejecucion local

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar pipeline:

```bash
python run_pipeline.py
```

## Tests

```bash
# Unitarios (sin red ni e2e)
pytest -q -m "not integration and not e2e"

# Integracion (arXiv)
pytest -q -m integration

# E2E (arXiv + Ollama)
pytest -q -m e2e
```

## Documentacion

Activa (`v1.1`):

- `docs/v1.1/Contrato_Sistema_v1.1.md`
- `docs/v1.1/Contrato_Runtime_v1.1.md`
- `docs/v1.1/Contrato_State_v1.1.md`

Legacy (`v1`, solo historico):

- `docs/legacy/v1/Contrato_Sistema_v1.md`
- `docs/legacy/v1/Contrato_State_v1.md`
- `docs/legacy/v1/nodos/`

## Ejecutar legacy v1

Si necesitas ejecutar el runtime manual historico (`run_real_pipeline.py`):

```bash
git switch codex/legacy-v1
python run_real_pipeline.py
```

Volver a v1.1:

```bash
git switch v1.1
```
