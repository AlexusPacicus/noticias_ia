import json

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


_llm = ChatOllama(
    model="gemma3:4b",
    temperature=0.1,
    top_p=0.9,
    num_predict=300,
    repeat_penalty=1.05,
    format="json",
)

_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres un asistente que genera resúmenes breves, descriptivos y "
        "estrictamente factuales de ítems del ámbito de la IA.\n\n"
        "Para el ítem proporcionado genera exactamente dos campos:\n"
        '- "idea_clave": máximo 60 palabras. Describe de forma factual qué es '
        "el ítem.\n"
        '- "por_que_importa": máximo 40 palabras. Contexto factual breve.\n\n'
        "Reglas:\n"
        "- Sin opiniones, predicciones, hype ni comparativas.\n"
        "- Usa SOLO la información proporcionada (title, source).\n"
        "- No inventes datos que no estén en el ítem.\n"
        '- Responde ÚNICAMENTE con JSON válido: '
        '{{\"idea_clave\": \"...\", \"por_que_importa\": \"...\"}}\n'
        "- Sin texto adicional fuera del JSON.",
    ),
    (
        "human",
        "Tipo: {kind}\nTítulo: {title}\nFuente: {source}",
    ),
])

_chain = _PROMPT | _llm


def _validate_summary(parsed: dict) -> None:
    idea = parsed.get("idea_clave")
    porque = parsed.get("por_que_importa")

    if not isinstance(idea, str) or not idea.strip():
        raise ValueError("SUMMARY_SCHEMA_VIOLATION")
    if not isinstance(porque, str) or not porque.strip():
        raise ValueError("SUMMARY_SCHEMA_VIOLATION")
    if len(idea.split()) > 60:
        raise ValueError("SUMMARY_SCHEMA_VIOLATION")
    if len(porque.split()) > 40:
        raise ValueError("SUMMARY_SCHEMA_VIOLATION")


def summarize(state: dict) -> dict:
    results = []

    for item in state["selected_items"]:
        response = _chain.invoke({
            "kind": item.get("kind", ""),
            "title": item.get("title", ""),
            "source": item.get("source") or "",
        })

        try:
            parsed = json.loads(response.content)
        except Exception:
            raise ValueError("SUMMARY_SCHEMA_VIOLATION")

        _validate_summary(parsed)

        results.append({
            **item,
            "idea_clave": parsed["idea_clave"],
            "por_que_importa": parsed["por_que_importa"],
        })

    state["results"] = results
    return state
