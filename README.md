# AI Papers Engine — v2 / v2.1

Motor determinista multi-fuente para descubrimiento y resumen de papers técnicos, construido con LangGraph.

> **Estado:**
> - `v2` FROZEN
> - `v2.1` funcional y cerrada para publicación, con limitaciones conocidas en `live`

---

## ¿Qué hace?

Dado una `query`, una `time_window` y un `top_k`, el pipeline ejecuta los siguientes pasos en orden:

1. **Fetch** — obtiene papers desde múltiples fuentes (arXiv, HuggingFace)
2. **Merge** — combina resultados de forma determinista
3. **Normalize** — convierte todo a un esquema común
4. **Filter** — aplica filtro temporal uniforme según `time_window`
5. **Dedupe** — elimina duplicados por `canonical_id`
6. **Rank** — ordena por relevancia usando BM25 propio
7. **Select** — toma los `top_k` resultados
8. **Summarize** — genera resúmenes secuenciales con Llama 3 8B vía Ollama
9. **Output** — devuelve resultado estructurado y trazable

---

## Parámetros de entrada

| Parámetro | Valores posibles |
|---|---|
| `query` | texto libre |
| `time_window` | `last_24h`, `last_3_days`, `last_7_days` |
| `top_k` | entero entre 1 y 5 |

---

## Versiones

### `v2`

- Pipeline base congelado
- Entry point: `run_pipeline_v2.py`
- Runtime principal: `graph.v2`

### `v2.1`

- Extiende `v2` con separación estructural de `RetrievalPhase`, `HITLPhase` y `SummarizePhase`
- Entry point: `run_pipeline_v2_1.py`
- Runtime principal: `graph.v2_1`
- Soporta ejecución parcial con `--execute-until select|summary`
- Tolera fallos parciales de summarize por item

## Propiedades del sistema

- **Determinismo estructural** hasta `rank_bm25` — el resultado es reproducible
- **Ranking puramente textual** — sin embeddings ni similitud semántica
- **Dedupe exclusivamente estructural** — basado en `canonical_id`
- **Abort dominante** en `retrieval`
- **Tolerancia a fallos parciales** en `v2.1/summarize`
- **Sin mutación in-place** del estado del grafo
- **Concurrencia** limitada a la fase de fetch

---

## Stack

- Python + LangGraph
- BM25 (implementación propia)
- Ollama con `llama3:8b`
- Pytest

**Configuración del LLM (congelada):**

```
model:       llama3:8b
temperature: 0
max_tokens:  450
timeout:     90s
modo:        ejecución secuencial
```

---

## Quick Start

```bash
pip install -r requirements.txt
ollama pull llama3:8b
pytest
```

```python
from graph.v2.graph import build_graph

graph = build_graph()
result = graph.invoke({
    "query": "agentic ai",
    "time_window": "last_7_days",
    "top_k": 3
})

print(result["output"])
```

### CLI `v2.1`

```bash
python run_pipeline_v2_1.py \
  --live \
  --execute-until summary \
  --query "agentic ai" \
  --time-window last_7_days \
  --top-k 2
```

```bash
python run_pipeline_v2_1.py \
  --stub \
  --execute-until select \
  --query "agentic ai" \
  --time-window last_7_days \
  --top-k 2
```

## Estructura del repositorio

Carpetas que deben entrar al subir el proyecto:

- `graph/` — runtimes `v2` y `v2.1`
- `nodes/` — implementación de nodos compartidos
- `runtime/` — cliente y parser LLM
- `tests/` — tests unitarios, integración y contratos `v2.1`
- `docs/` — contratos, alcance y guías operativas
- `run_pipeline_v2.py`
- `run_pipeline_v2_1.py`
- `requirements.txt`
- `pytest.ini`
- `LICENSE`
- `README.md`

Carpetas o archivos que no deben entrar en una subida limpia:

- `.venv/`
- `.pytest_cache/`
- `__pycache__/`
- `artifacts/` si contiene resultados locales temporales
- cualquier output generado manualmente durante pruebas locales

## Estructura mínima recomendada para publicar

```text
docs/
graph/
nodes/
runtime/
tests/
run_pipeline_v2.py
run_pipeline_v2_1.py
requirements.txt
pytest.ini
README.md
LICENSE
```

---

## Limitaciones conocidas

- Sin caching ni persistencia entre ejecuciones
- Summarize no paralelizado
- Dependencia de endpoints externos (arXiv, HuggingFace, Ollama)
- No es un servicio desplegado
- En `v2.1 live`, algunos items pueden fallar por timeout de Ollama en hardware local lento
- En `v2.1`, si el LLM no devuelve JSON válido, se usa texto libre como fallback
- El modo `stub` puede no ser representativo si las fechas fijas quedan fuera de la ventana temporal actual

---

## Decisiones deliberadas

Estas features fueron descartadas intencionalmente para mantener el sistema simple y determinista:

- ~~Embeddings o similitud semántica~~
- ~~Reranking con LLM~~
- ~~Señales sociales (citas, likes, etc.)~~
