# AI Papers Engine — v2

Motor determinista multi-fuente para descubrimiento y resumen de papers técnicos, construido con LangGraph.

> **Estado:** v2 FROZEN

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
8. **Summarize** — genera resúmenes secuenciales con Llama 3 8B
9. **Output** — devuelve resultado estructurado y trazable

---

## Parámetros de entrada

| Parámetro | Valores posibles |
|---|---|
| `query` | texto libre |
| `time_window` | `last_24h`, `last_3_days`, `last_7_days` |
| `top_k` | entero entre 1 y 5 |

---

## Propiedades del sistema

- **Determinismo estructural** hasta `rank_bm25` — el resultado es reproducible
- **Ranking puramente textual** — sin embeddings ni similitud semántica
- **Dedupe exclusivamente estructural** — basado en `canonical_id`
- **Abort dominante** — sin outputs parciales ante fallos
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
timeout:     60s
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

---

## Limitaciones conocidas

- Sin caching ni persistencia entre ejecuciones
- Summarize no paralelizado
- Dependencia de endpoints externos (arXiv, HuggingFace, Ollama)
- No es un servicio desplegado

---

## Decisiones deliberadas

Estas features fueron descartadas intencionalmente para mantener el sistema simple y determinista:

- ~~Embeddings o similitud semántica~~
- ~~Reranking con LLM~~
- ~~Señales sociales (citas, likes, etc.)~~
