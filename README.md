# noticias — v1

Sistema contractual de selección y resumen de papers de IA desde arXiv `cs.AI`.

## Estado

- **Versión:** v1.0.0
- **Contratos:** FROZEN (Sistema, State, 7 nodos)
- **Tests:** 29 unitarios passing

## Pipeline

```
collect_input → validate_input → fetch → normalize → rank → select → summarize
```

## Runtime oficial

```bash
python run_real_pipeline.py
```

Ejecuta el pipeline completo con datos reales. Captura aborts vía `ValueError` y escribe `abort_reason` en el State.

`graph.py` / `run.py` (LangGraph) son artefactos legacy. No implementan el mecanismo de abort contractual.

## Tests

```bash
# Tests unitarios (sin red ni LLM)
python -m pytest --ignore=tests/test_e2e.py --ignore=tests/test_summarize.py

# Tests con mock de LLM
python -m pytest tests/test_summarize.py

# Tests e2e (requieren arXiv + Ollama)
python -m pytest -m e2e
```

## Pendiente para v1.1

- Migración a LangGraph con State tipado, conditional edges y abort handling nativo.
