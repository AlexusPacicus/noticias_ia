AI Papers Engine — v2
Motor determinista multi-fuente para descubrimiento y resumen de papers técnicos, construido con LangGraph.
v2 está congelada (FROZEN) tras validación estructural y stress con LLM real.
Qué hace
Consulta múltiples fuentes técnicas (arxiv, huggingface)
Normaliza payloads heterogéneos a un esquema común
Elimina duplicados cross-source mediante canonical_id
Rankea usando BM25 implementado manualmente
Resume con patrón map-reduce secuencial
Devuelve un output estructurado y trazable
Enfoque de ingeniería
Este proyecto no es un RAG con embeddings.
Se diseñó para explorar:
Determinismo estructural bajo concurrencia en fetch
Separación estricta de responsabilidades por nodo
Gobernanza explícita del state (sin mutación in-place)
Gates de abort dominantes y controlados
Tolerancia a fallos individuales en summarize
Validación con ejecuciones reales de LLM (stress tests)
El objetivo fue priorizar control, trazabilidad y previsibilidad, no “magia” heurística.
Arquitectura
Pipeline fijo:
collect_input
→ validate_input
→ fetch (multi-source)
→ merge determinista
→ normalize
→ filter_by_time_window
→ dedupe
→ rank_bm25
→ select
→ summarize_map
→ summarize_reduce
Propiedades clave:
Orden total determinista hasta rank_bm25
Ranking puramente textual ((-bm25_score, title ASC, link ASC))
Dedupe exclusivamente estructural
Abort dominante: no hay outputs parciales inconsistentes
No se recalcula ranking tras summarize
Stack técnico
Python
LangGraph (StateGraph)
BM25 propio (sin librerías externas)
Ollama local (llama3:8b)
Pytest (unit, integration, stress tests)
Ejecución
from graph.v2.graph import build_graph

graph = build_graph()

result = graph.invoke({
    "query": "agentic ai",
    "time_window": "last_7_days",
    "top_k": 3
})

print(result["output"])
Ejemplo de output
{
  "topic": "agentic ai",
  "requested_k": 3,
  "returned_k": 2,
  "failed_summaries": 1,
  "results": [
    {
      "title": "...",
      "summary": "...",
      "link": "...",
      "source": "arxiv",
      "rank_position": 1
    }
  ]
}
Lo que NO es (decisiones deliberadas)
No usa embeddings
No usa similitud semántica
No hace reranking con LLM
No usa señales sociales
No paraleliza summarize
No es un servicio desplegado
El foco de v2 es la robustez estructural del motor, no la sofisticación algorítmica.