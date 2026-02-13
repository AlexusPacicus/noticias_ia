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

## Setup

```bash
pip install -r requirements.txt
```

Requiere [Ollama](https://ollama.com/) con el modelo `gemma3:4b` disponible para el nodo `summarize`.

## Runtime

```bash
python run_real_pipeline.py
```

Ejecuta el pipeline completo con datos reales. Captura aborts vía `ValueError` y escribe `abort_reason` en el State.

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
