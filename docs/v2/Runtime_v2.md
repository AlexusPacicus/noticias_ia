# Runtime v2

## 1. Scope

Este documento describe cómo ejecutar v2 y cuál es el perfil operativo validado.
No define reglas contractuales (ver Contrato_Sistema_v2, Contrato_State_v2 y Contrato_LLM_v2).

---

## 2. Ejecución

### Entry-point

```python
from graph.v2.graph import build_graph

graph = build_graph()
result = graph.invoke({
    "query": "agentic ai",
    "time_window": "last_7_days",
    "top_k": 2
})

graph.invoke() devuelve el state completo del pipeline.
El output público contractual se encuentra en la clave output.


3. Configuración LLM (FROZEN)
Ver: Contrato_LLM_v2.md
Configuración congelada por Gate 4 (v2):
Provider: Ollama local
Endpoint: http://127.0.0.1:11434/api/generate
Modelo: llama3:8b
Temperatura: 0
max_tokens = 450
TIMEOUT_SECONDS = 60
MAX_RETRIES = 1
Ejecución secuencial vía summarize_map
Cualquier modificación requiere nueva formalización contractual.
## 4. Perfil operativo validado (entorno CPU local)

En el entorno validado (Ollama CPU local):

- Latencia observada dentro del umbral aceptado (<= 120s)
- Sin aborts en escenario nominal
- Estructura final completa
- Determinismo estructural preservado hasta rank_bm25

Este umbral no constituye SLA ni garantía universal.
Es el criterio aprobado para el freeze v2 en el entorno validado.

## 5. Restricciones de ejecución (v2)

El runtime v2 opera bajo las siguientes restricciones en el perfil validado:

- Concurrencia permitida contractualmente en `fetch_*`, pero no garantizada por el entorno.
- `summarize_map` ejecuta de forma secuencial determinista.
- No existe caching.
- No existe persistencia.
- No existe soporte GPU.
- No se define SLA.

## 6. Artefactos esperados

### Ejecución nominal (sin abort)

Salida estructural válida:

- output
- summary_stats
- selected_items

El output público contractual tiene la siguiente estructura:

{
  "topic": "agentic ai",
  "time_window": "last_7_days",
  "requested_k": 2,
  "returned_k": 2,
  "failed_summaries": 0,
  "results": [
    {
      "title": "Paper A",
      "summary": "...",
      "link": "https://...",
      "source": "arxiv",
      "rank_position": 1
    }
  ]
}

### Ejecución con abort

- abort_reason

En caso de abort, no deben existir:
- abort_reason
- output
- claves posteriores al nodo que abortan


### Ejemplo de abort

{
  "query": "",
  "time_window": "last_7_days",
  "top_k": 2,
  "abort_reason": "INVALID_QUERY"
}