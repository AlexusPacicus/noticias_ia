# noticias v2 (FROZEN)

Pipeline multi-fuente para descubrimiento y resumen tecnico de papers, con contratos de sistema/state/nodos y comportamiento determinista hasta ranking.

## Que hace

1. Valida input (`query`, `time_window`, `top_k`).
2. Hace fetch desde arXiv y HuggingFace Papers.
3. Normaliza, filtra por ventana temporal, deduplica y rankea con BM25.
4. Selecciona `top_k`.
5. Resume cada item con LLM local (Ollama) bajo schema estricto JSON.

## Pipeline v2

```text
collect_input -> validate_input -> fetch_router -> fetch_* -> merge_source_units
-> normalize -> filter_by_time_window -> dedupe -> rank_bm25 -> select
-> summarize_map -> summarize_reduce
```

## Input publico

- `query`: string no vacio
- `time_window`: `last_24h | last_3_days | last_7_days`
- `top_k`: int opcional en `[1..5]` (default `3`)

## Output publico (exito)

```json
{
  "topic": "agentic ai",
  "time_window": "last_7_days",
  "requested_k": 2,
  "returned_k": 2,
  "failed_summaries": 0,
  "results": [
    {
      "rank_position": 1,
      "title": "Paper title",
      "link": "https://...",
      "source": "arxiv",
      "summary": "Technical summary..."
    }
  ]
}
```

En ejecucion abortada, la salida contiene:

```json
{"abort_reason":"..."}
```

## Ejecutar

Requisitos:

- Python 3.11+
- Ollama local
- modelo `llama3:8b` descargado

Instalacion:

```bash
pip install -r requirements.txt
```

Runner principal:

```bash
python run_pipeline_v2.py
```

Flags utiles:

```bash
# modo determinista de pruebas (sin fetch real)
python run_pipeline_v2.py --stub --debug

# modo live real (default)
python run_pipeline_v2.py --live --query "agentic ai" --time-window last_7_days --top-k 2

# aislar fuente
python run_pipeline_v2.py --source arxiv
python run_pipeline_v2.py --source huggingface
python run_pipeline_v2.py --source both
```

## Tests

```bash
pytest -q
```

Suite actual: `79 passed`.

## Documentacion contractual

- [Contrato de Sistema v2](docs/v2/Contrato_Sistema_v2.md)
- [Contrato de State v2](docs/v2/Contrato_State_v2.md)
- [Diseno v2](docs/v2/Diseno_v2.md)
- [Contratos de nodos v2](docs/v2/nodos/)

## Notas para demos

- El determinismo estructural aplica hasta ranking.
- `summarize_map` tolera fallos parciales por item.
- Solo aborta en summary cuando todos los items fallan (`SUMMARY_ALL_ITEMS_FAILED`).
