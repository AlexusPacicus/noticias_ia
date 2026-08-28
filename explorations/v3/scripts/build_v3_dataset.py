from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("explorations/data/raw/data_v0.csv")
DEFAULT_OUTPUT = Path("explorations/data/interim/data_v1_structured.csv")
USER_AGENT = "noticias-build-v3-dataset/0.1"
ARXIV_API = "https://export.arxiv.org/api/query?id_list={paper_id}"
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:8b"
OUTPUT_COLUMNS = [
    "paper_id",
    "title",
    "year",
    "source_url",
    "abstract",
    "problem",
    "method",
    "result",
    "method_family_seed",
    "method_family_lexical",
    "method_family_llm",
    "method_family_final",
    "confidence",
    "notes",
]
ALLOWED_FAMILIES = [
    "gan",
    "autoregressive",
    "diffusion",
    "diffusion_transformer_or_hybrid",
    "other",
    "unknown",
]


class MetaDescriptionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return

        attr_map = {key.lower(): (value or "") for key, value in attrs}
        content = attr_map.get("content", "").strip()
        if not content:
            return

        for key in ("name", "property"):
            meta_name = attr_map.get(key, "").strip().lower()
            if meta_name:
                self.meta[meta_name] = content


def _http_get(url: str, *, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _http_post_json(url: str, payload: dict[str, Any], *, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("Invalid JSON payload from Ollama")
    return parsed


def _extract_arxiv_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if "arxiv.org" not in parsed.netloc.lower():
        return None

    path = parsed.path.strip("/")
    if path.startswith("abs/"):
        return path.removeprefix("abs/").strip()
    if path.startswith("pdf/"):
        return path.removeprefix("pdf/").removesuffix(".pdf").strip()
    return None


def _clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip()


def _clean_abstract(text: str) -> str:
    text = _clean_text(text)
    text = re.sub(r"^(abstract|summary)\s*[:\-]\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _fetch_arxiv_abstract(paper_id: str, *, timeout: float) -> str | None:
    feed = _http_get(ARXIV_API.format(paper_id=urllib.parse.quote(paper_id)), timeout=timeout)
    root = ET.fromstring(feed)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    summary = root.findtext(".//atom:entry/atom:summary", default="", namespaces=namespace)
    return _clean_abstract(summary)


def _extract_meta_abstract(html_text: str) -> str | None:
    parser = MetaDescriptionParser()
    parser.feed(html_text)
    candidates = [
        parser.meta.get("citation_abstract"),
        parser.meta.get("description"),
        parser.meta.get("og:description"),
        parser.meta.get("twitter:description"),
    ]
    for candidate in candidates:
        cleaned = _clean_abstract(candidate or "")
        if cleaned:
            return cleaned
    return None


def _fetch_abstract(source_url: str, *, timeout: float) -> str | None:
    arxiv_id = _extract_arxiv_id(source_url)
    if arxiv_id:
        return _fetch_arxiv_abstract(arxiv_id, timeout=timeout)
    page = _http_get(source_url, timeout=timeout)
    return _extract_meta_abstract(page)


def _extract_json_object(raw: str) -> dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Empty LLM response")

    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    candidate = match.group(0) if match else raw
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    return parsed


def _call_ollama(prompt: str, *, timeout: float) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "top_p": 1},
    }
    response = _http_post_json(OLLAMA_ENDPOINT, payload, timeout=timeout)
    text = response.get("response")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Ollama returned an empty response")
    return text


def _extract_problem_method_result(*, title: str, abstract: str, timeout: float) -> dict[str, str]:
    prompt = f"""
Return valid JSON only with keys "problem", "method", "result".

Rules:
- Use only the information present in title and abstract.
- Keep each value concise, specific, and in English.
- "problem" = task or research problem addressed by the paper.
- "method" = main methodological approach, model family, or technical core.
- "result" = main claimed outcome, capability, or empirical finding.
- If a field is missing, return an empty string for that field.

Title:
{title}

Abstract:
{abstract}
""".strip()
    raw = _call_ollama(prompt, timeout=timeout)
    parsed = _extract_json_object(raw)
    return {
        "problem": _clean_text(str(parsed.get("problem", ""))),
        "method": _clean_text(str(parsed.get("method", ""))),
        "result": _clean_text(str(parsed.get("result", ""))),
    }


def _classify_method_family_lexical(method: str) -> str:
    text = (method or "").lower()
    if not text:
        return "unknown"

    hybrid_patterns = [
        "diffusion transformer",
        "mm-dit",
        "mmdit",
        "dit",
        "rectified flow",
        "flow matching",
        "sd3",
        "stable diffusion 3",
        "flux",
    ]
    diffusion_patterns = [
        "diffusion",
        "denoising",
        "ddpm",
        "score-based",
        "latent diffusion",
        "classifier-free guidance",
        "ldm",
        "glide",
    ]
    autoregressive_patterns = [
        "autoregressive",
        "token",
        "discrete",
        "vq-vae",
        "vqvae",
        "dall-e",
        "parti",
        "sequential transformer",
    ]
    gan_patterns = [
        "gan",
        "cgan",
        "adversarial",
        "stackgan",
        "attngan",
    ]

    if any(pattern in text for pattern in hybrid_patterns):
        return "diffusion_transformer_or_hybrid"
    if any(pattern in text for pattern in diffusion_patterns):
        return "diffusion"
    if any(pattern in text for pattern in autoregressive_patterns):
        return "autoregressive"
    if any(pattern in text for pattern in gan_patterns):
        return "gan"
    return "other"


def _classify_method_family_llm(method: str, *, timeout: float) -> str:
    if not method.strip():
        return "unknown"

    prompt = f"""
Classify the following method description into exactly one label.
Return JSON only with key "method_family".

Allowed labels:
{", ".join(ALLOWED_FAMILIES)}

Label definitions:
- gan: adversarial text-to-image approaches
- autoregressive: token-based or sequential generative modeling
- diffusion: denoising or diffusion-based generation
- diffusion_transformer_or_hybrid: diffusion combined centrally with transformer, DiT, flow-matching, SD3, Flux, or close hybrid variants
- other: method is in-scope but does not fit the active families
- unknown: insufficient evidence

Method:
{method}
""".strip()
    raw = _call_ollama(prompt, timeout=timeout)
    parsed = _extract_json_object(raw)
    label = _clean_text(str(parsed.get("method_family", ""))).lower()
    if label not in ALLOWED_FAMILIES:
        return "unknown"
    return label


def _resolve_final_family(seed: str, lexical: str, llm_label: str) -> tuple[str, str]:
    candidates = [seed, lexical, llm_label]
    known = [label for label in candidates if label and label != "unknown"]
    if lexical == llm_label and lexical != "unknown":
        return lexical, "high"
    if seed and seed == lexical and seed != "unknown":
        return seed, "medium"
    if seed and seed == llm_label and seed != "unknown":
        return seed, "medium"
    if lexical != "unknown":
        return lexical, "low"
    if llm_label != "unknown":
        return llm_label, "low"
    if known:
        return known[0], "low"
    return "unknown", "low"


def _normalize_row(row: dict[str, str]) -> dict[str, str]:
    normalized = {column: _clean_text(row.get(column, "")) for column in OUTPUT_COLUMNS}
    for key in row:
        if key not in normalized:
            normalized[key] = _clean_text(row.get(key, ""))
    return normalized


def build_dataset(
    input_path: Path,
    output_path: Path,
    *,
    timeout: float,
    delay_seconds: float,
) -> tuple[int, int]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        rows = [_normalize_row(row) for row in reader]

    if not rows:
        raise ValueError(f"{input_path} does not contain data rows")

    processed = 0
    failures = 0
    output_rows: list[dict[str, str]] = []

    for row in rows:
        row_out = {column: row.get(column, "") for column in OUTPUT_COLUMNS}

        if not row_out["abstract"]:
            source_url = row.get("source_url", "")
            if source_url:
                try:
                    row_out["abstract"] = _fetch_abstract(source_url, timeout=timeout) or ""
                except (urllib.error.URLError, urllib.error.HTTPError, ET.ParseError, ValueError) as exc:
                    row_out["notes"] = _merge_notes(row_out["notes"], f"abstract_fetch_error={exc}")

        abstract = row_out["abstract"].strip()
        if abstract:
            try:
                extracted = _extract_problem_method_result(
                    title=row_out["title"],
                    abstract=abstract,
                    timeout=timeout,
                )
                row_out["problem"] = extracted["problem"]
                row_out["method"] = extracted["method"]
                row_out["result"] = extracted["result"]
            except (urllib.error.URLError, urllib.error.HTTPError, ValueError, json.JSONDecodeError) as exc:
                failures += 1
                row_out["notes"] = _merge_notes(row_out["notes"], f"pmr_extraction_error={exc}")
        else:
            failures += 1
            row_out["notes"] = _merge_notes(row_out["notes"], "missing_abstract")

        row_out["method_family_seed"] = _classify_method_family_lexical(row_out["method"])
        row_out["method_family_lexical"] = row_out["method_family_seed"]

        try:
            row_out["method_family_llm"] = _classify_method_family_llm(
                row_out["method"],
                timeout=timeout,
            )
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, json.JSONDecodeError) as exc:
            row_out["method_family_llm"] = "unknown"
            row_out["notes"] = _merge_notes(row_out["notes"], f"method_family_llm_error={exc}")

        final_family, confidence = _resolve_final_family(
            row_out["method_family_seed"],
            row_out["method_family_lexical"],
            row_out["method_family_llm"],
        )
        row_out["method_family_final"] = final_family
        row_out["confidence"] = confidence

        output_rows.append(row_out)
        processed += 1

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    return processed, failures


def _merge_notes(current: str, new_note: str) -> str:
    current = current.strip()
    new_note = new_note.strip()
    if not current:
        return new_note
    if not new_note:
        return current
    return f"{current} | {new_note}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the structured v3 dataset from the raw paper CSV.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    processed, failures = build_dataset(
        args.input,
        args.output,
        timeout=args.timeout,
        delay_seconds=args.delay,
    )
    print(f"Wrote {args.output} | processed={processed} failures={failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
