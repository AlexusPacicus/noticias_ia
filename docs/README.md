AI Papers Engine — v2
Motor determinista multi-fuente para descubrimiento y resumen de papers técnicos construido con LangGraph.
v2 está formalmente congelada (FROZEN) tras validación estructural y stress con LLM real.
Qué hace
Consulta múltiples fuentes técnicas (arxiv, huggingface)
Normaliza resultados a un esquema común
Elimina duplicados cross-source por canonical_id
Rankea usando BM25 implementado manualmente
Resume usando LLM en patrón map-reduce secuencial
Devuelve un output estructurado y trazable
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
Propiedades:
Determinismo estructural hasta el ranking
Separación estricta de responsabilidades por nodo
Concurrencia controlada en fetch
Abort dominante explícito
No mutación in-place del state
Stack técnico
Python
LangGraph (StateGraph)
BM25 propio (sin librerías externas)
Ollama local (llama3:8b)
Pytest (unit, integration, stress tests)
Arquitectura contractual por capas (System / State / LLM)
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
Decisiones de diseño
Dedupe exclusivamente estructural
Ranking puramente textual (sin embeddings)
Orden total determinista: (-bm25_score, title ASC, link ASC)
Fallos individuales en summarize no abortan el sistema
Abort solo ante fallo total en fases críticas
Lo que NO es
No es un RAG con embeddings
No usa similitud semántica
No hace reranking con LLM
No usa señales sociales
No es un servicio desplegado (solo motor)
Estado del proyecto
v2: FROZEN
Validado con stress LLM real (20+ ejecuciones)
Determinismo estructural comprobado
