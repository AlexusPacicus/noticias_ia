import json
import re
from typing import Dict, Any
from urllib.request import Request, urlopen
import logging

MODEL_NAME = "llama3:8b"
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
TIMEOUT_SECONDS = 60
MAX_TOKENS = 450
TEMPERATURE = 0
MAX_RETRIES = 1
RETRY_HARDENING_SUFFIX = (
    "\n\nThe previous output was invalid.\n"
    "Return ONLY raw JSON.\n"
    "No markdown.\n"
    "No explanation.\n"
)

logger = logging.getLogger(__name__)


def extract_json_safely(text: str) -> dict:
    """
    Attempt strict JSON parsing.
    If it fails, try extracting the first balanced JSON object found.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        raise RuntimeError("No JSON object found")

    try:
        candidate = _extract_first_balanced_object(text, start)
        return json.loads(candidate)
    except Exception:
        raise RuntimeError("Invalid JSON after extraction")


def _extract_first_balanced_object(text: str, start_idx: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    end_idx = None

    for idx in range(start_idx, len(text)):
        ch = text[idx]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_idx = idx
                break

    if end_idx is None:
        raise RuntimeError("No balanced JSON object found")

    return text[start_idx:end_idx + 1]


def build_prompt(title: str, abstract: str) -> str:
    with open("docs/v2/prompts/summarize_v2.txt", "r") as f:
        template = f.read()

    return (
        template
        .replace("{title}", title)
        .replace("{abstract}", abstract)
    )


def build_retry_prompt(base_prompt: str) -> str:
    return f"{base_prompt.rstrip()}{RETRY_HARDENING_SUFFIX}"


def _sanitize_fallback_summary(raw_output: str) -> str:
    cleaned = (raw_output or "").replace("`", "").strip()
    if not cleaned:
        return ""

    prefix_pattern = re.compile(
        r"^\s*(summary|resumen|technical summary|final summary|tl;dr)\s*[:\-]\s*",
        re.IGNORECASE,
    )
    while True:
        new_value = prefix_pattern.sub("", cleaned, count=1).strip()
        if new_value == cleaned:
            break
        cleaned = new_value

    return cleaned


def _looks_like_json_output(text: str) -> bool:
    t = (text or "").strip()
    return t.startswith("{") or '"summary"' in t


def _recover_summary_from_json_like(text: str) -> str:
    candidate = text or ""
    match = re.search(r'"summary"\s*:\s*"((?:\\.|[^"\\])*)"', candidate, flags=re.DOTALL)
    if not match:
        return ""

    encoded_summary = match.group(1)
    try:
        recovered = json.loads(f'"{encoded_summary}"')
    except Exception:
        recovered = encoded_summary
    return recovered.strip() if isinstance(recovered, str) else ""


def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "num_predict": MAX_TOKENS,
        },
    }

    req = Request(
        OLLAMA_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        body = resp.read().decode("utf-8", errors="replace")

    parsed = json.loads(body)
    response_text = parsed.get("response")
    if not isinstance(response_text, str):
        raise RuntimeError("Missing response field from Ollama")
    return response_text


def validate_summary_schema(payload: Dict[str, Any]) -> Dict[str, str]:
    if not isinstance(payload, dict):
        raise RuntimeError("Invalid summary payload type")

    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise RuntimeError("Invalid summary value")

    return {"summary": summary.strip()}


def generate_summary(item: Dict[str, str]) -> Dict[str, Any]:
    """
    Deterministic summary generation with:
    - temperature=0
    - max_tokens enforced in provider call
    - 1 retry
    - defensive JSON extraction
    """
    if set(item.keys()) != {"title", "abstract", "link", "source"}:
        return {"error": "INVALID_LLM_INPUT_SCHEMA"}

    title = item.get("title")
    abstract = item.get("abstract")
    link = item.get("link")
    source = item.get("source")

    if not all(isinstance(v, str) for v in [title, abstract, link, source]):
        return {"error": "INVALID_LLM_INPUT_VALUE"}

    base_prompt = build_prompt(title, abstract)
    prompt = base_prompt

    attempt = 0
    while attempt <= MAX_RETRIES:
        try:
            raw_output = call_ollama(prompt)
            try:
                parsed = extract_json_safely(raw_output)
                return validate_summary_schema(parsed)
            except Exception:
                text = (raw_output or "").strip()
                if not text:
                    raise RuntimeError("Empty LLM output after parse failure")

                if _looks_like_json_output(text):
                    recovered_summary = _recover_summary_from_json_like(text)
                    if recovered_summary:
                        return {"summary": recovered_summary, "mode": "fallback_json_recovery"}
                    raise RuntimeError("JSON-like output without recoverable summary")

                fallback_summary = _sanitize_fallback_summary(text)
                if fallback_summary:
                    return {"summary": fallback_summary, "mode": "fallback_text"}
                raise RuntimeError("Empty fallback text after parse failure")
        except Exception as exc:
            logger.warning(
                "LLM summary attempt failed (attempt=%s/%s): %s",
                attempt + 1,
                MAX_RETRIES + 1,
                exc,
                exc_info=True,
            )
            attempt += 1
            if attempt > MAX_RETRIES:
                return {"error": f"LLM_CALL_FAILED: {exc}"}
            prompt = build_retry_prompt(base_prompt)
