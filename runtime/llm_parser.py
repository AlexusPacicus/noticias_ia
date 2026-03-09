import json

from runtime.types import LLMOutput


class ParseError(Exception):
    pass


def parse_llm_output(raw: str) -> LLMOutput:
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ParseError("Invalid JSON from LLM") from exc

    if not isinstance(data, dict):
        raise ParseError("LLM output must be a JSON object")

    if set(data.keys()) != {"summary"}:
        raise ParseError("Unexpected keys in LLM output")

    summary = data["summary"]

    if not isinstance(summary, str) or not summary.strip():
        raise ParseError("Invalid summary field")

    return LLMOutput(summary=summary.strip())
