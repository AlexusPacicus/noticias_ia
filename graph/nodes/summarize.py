from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from graph.state import PipelineState

_llm = ChatOllama(
    model="gemma3:4b",
    temperature=0.1,
    top_p=0.9,
    num_predict=200,
    repeat_penalty=1.05,
    format="json",
)

_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Genera un resumen factual breve de un ítem de IA.\n\n"
        "Responde SOLO con JSON válido con exactamente dos campos:\n"
        '- "idea_clave": máximo 80 palabras. Qué es el ítem. Solo hechos.\n'
        '- "relacion_con_query": máximo 30 palabras. Términos del ítem '
        "relacionados con la query.\n\n"
        "IMPORTANTE: Sé conciso. No superes los límites de palabras.\n"
        "Sin opiniones, predicciones ni comparativas.\n"
        "Usa SOLO información del título y contenido proporcionados.\n"
        'Formato: {{\"idea_clave\": \"...\", \"relacion_con_query\": \"...\"}}',
    ),
    (
        "human",
        "Título: {title}\nContenido: {content}\nQuery: {query}",
    ),
])

_chain = _PROMPT | _llm

_ALLOWED_KEYS = {"idea_clave", "relacion_con_query"}


def _validate_structure(parsed: dict) -> str | None:
    """Valida schema del LLM. Retorna codigo de abort o None si es valido."""
    if set(parsed.keys()) != _ALLOWED_KEYS:
        return "SUMMARY_SCHEMA_VIOLATION"

    idea = parsed["idea_clave"]
    relacion = parsed["relacion_con_query"]

    if not isinstance(idea, str) or not idea.strip():
        return "SUMMARY_SCHEMA_VIOLATION"
    if not isinstance(relacion, str) or not relacion.strip():
        return "SUMMARY_SCHEMA_VIOLATION"
    if len(idea.split()) > 80:
        return "SUMMARY_SCHEMA_VIOLATION"
    if len(relacion.split()) > 30:
        return "SUMMARY_SCHEMA_VIOLATION"

    return None


def summarize(state: PipelineState) -> dict:
    """Genera resumenes descriptivos mediante LLM para cada selected_item.

    Retorna output o abort_reason.
    """
    selected = state["selected_items"]
    validated = state["input_validated"]

    output = {
        "topic": validated["query"],
        "time_window": validated["time_window"],
        "results": [],
    }

    if not selected:
        return {"output": output}

    results = []
    for item in selected:
        try:
            response = _chain.invoke({
                "title": item["title"],
                "content": item["content"],
                "query": validated["query"],
            })
        except Exception:
            return {"abort_reason": "SUMMARY_LLM_RUNTIME_ERROR"}

        try:
            parsed = json.loads(response.content)
        except Exception:
            return {"abort_reason": "SUMMARY_SCHEMA_VIOLATION"}

        violation = _validate_structure(parsed)
        if violation:
            return {"abort_reason": violation}

        results.append({
            "title": item["title"],
            "idea_clave": parsed["idea_clave"],
            "relacion_con_query": parsed["relacion_con_query"],
            "link": item["link"],
        })

    output["results"] = results
    return {"output": output}
