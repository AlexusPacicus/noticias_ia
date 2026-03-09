from __future__ import annotations

from typing import Any, Dict

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:8b"
OLLAMA_TEMPERATURE = 0
OLLAMA_TOP_P = 1

LLM_TIMEOUT_SECONDS = 90
LLM_MAX_RETRIES = 2


class LLMTimeout(Exception):
    """Raised when the LLM call times out after retries."""


class LLMError(Exception):
    """Raised for non-timeout LLM/client errors."""


class LLMEmptyResponse(Exception):
    """Raised when Ollama returns an empty response string."""


class LLMClient:
    def generate(self, *, title: str, abstract: str, query: str) -> str:
        prompt = (
            f"Query:\n{query}\n\n"
            f"Title:\n{title}\n\n"
            f"Abstract:\n{abstract}"
        )
        payload: Dict[str, Any] = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "top_p": OLLAMA_TOP_P,
            },
        }

        last_timeout_error: Timeout | None = None
        last_infra_error: RequestException | None = None

        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                response = requests.post(
                    OLLAMA_ENDPOINT,
                    json=payload,
                    timeout=LLM_TIMEOUT_SECONDS,
                )
            except Timeout as exc:
                last_timeout_error = exc
                if attempt < LLM_MAX_RETRIES:
                    continue
                raise LLMTimeout(
                    f"LLM request timed out after {LLM_MAX_RETRIES + 1} attempts"
                ) from exc
            except RequestException as exc:
                last_infra_error = exc
                if attempt < LLM_MAX_RETRIES:
                    continue
                raise LLMError(
                    f"LLM infrastructure failure after {LLM_MAX_RETRIES + 1} attempts: {exc}"
                ) from exc

            if response.status_code >= 500:
                if attempt < LLM_MAX_RETRIES:
                    continue
                raise LLMError(
                    f"LLM request failed with status {response.status_code}: "
                    f"{_safe_response_excerpt(response)}"
                )

            if response.status_code != 200:
                raise LLMError(
                    f"LLM request failed with status {response.status_code}: "
                    f"{_safe_response_excerpt(response)}"
                )

            body = _parse_json(response)
            if body.get("done") is False:
                raise LLMError("Incomplete Ollama response")

            generated_text = body.get("response")

            if not isinstance(generated_text, str):
                raise LLMError("Invalid Ollama response: missing string field 'response'")

            if not generated_text.strip():
                raise LLMEmptyResponse("Ollama returned an empty 'response' field")

            return generated_text

        if last_timeout_error is not None:
            raise LLMTimeout(
                f"LLM request timed out after {LLM_MAX_RETRIES + 1} attempts"
            ) from last_timeout_error

        if last_infra_error is not None:
            raise LLMError(
                f"LLM infrastructure failure after {LLM_MAX_RETRIES + 1} attempts: "
                f"{last_infra_error}"
            ) from last_infra_error

        raise LLMError("LLM request failed for an unknown reason")


def _parse_json(response: Response) -> Dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        raise LLMError("Invalid JSON from Ollama response") from exc

    if not isinstance(data, dict):
        raise LLMError("Invalid Ollama response payload type")
    return data


def _safe_response_excerpt(response: Response) -> str:
    text = response.text or ""
    text = text.strip().replace("\n", " ")
    return text[:200]


llm = LLMClient()
