# Guia Operativa `2.1`

## Builders canónicos
- Full graph: `graph/v2_1/graph_21.py::build_graph_21`
- Retrieval subgraph: `graph/v2_1/retrieval/graph_21.py::build_retrieval_graph`
- Summarize subgraph: `graph/v2_1/summarize/graph_21.py::build_summarize_graph`
- HITL subgraph: `graph/v2_1/hitl/graph_21.py::build_hitl_graph`

## Ruta real de summarize en `2.1`
- `graph/v2_1/summarize/summarize_map.py`
- `nodes/summarize/summarize_reduce.py`
- `runtime/llm_client.py`
- `runtime/parse_llm_output.py`
- `runtime/llm_parser.py`

## Qué observar en pruebas reales
- `summary_stats.ok`
- `summary_stats.failed`
- `abort_reason`
- `output.returned_k`
- `output.failed_summaries`
- orden de `output.results[*].rank_position`

## Qué no mezclar
Para pruebas reales de `2.1`, no usar la ruta legacy:
- `graph/v2/graph.py::build_graph`
- `graph/v2/nodes/summarize_map.py`

## Smoke tests mínimos
1. Happy path:
   `query="agentic ai"`, `time_window="last_7_days"`, `top_k=2`
2. Fallo parcial:
   al menos un item falla y la fase no aborta si queda un item válido
3. Parser robustness:
   salida inválida del LLM se trata como item failure
4. Rank preservation:
   `rank_position` se preserva en `summary_items` y `output.results` queda ordenado
