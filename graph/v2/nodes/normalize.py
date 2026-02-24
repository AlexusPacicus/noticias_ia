# graph/v2/nodes/normalize.py

from __future__ import annotations

import re
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from graph.v2.state import V2State


_ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)


def _generate_canonical_id(link: str) -> str:
    """
    Contract (Diseño v2 §6):
    - If an arXiv ID is present (YYYY.NNNNN with optional vN), return: arxiv:<base_id>
    - Else normalize URL:
        * lowercase
        * remove trailing slash
        * remove only utm_* query params
      and return: url:<normalized_url>
    """
    if not isinstance(link, str) or not link.strip():
        # normalize() will discard invalid items; this is just defensive.
        return "url:"

    link_lc = link.strip().lower()

    # Rule 1/2: arXiv ID anywhere in link
    m = _ARXIV_ID_RE.search(link_lc)
    if m:
        base_id = m.group(1)
        return f"arxiv:{base_id}"

    # Rule 3: URL fallback normalization
    p = urlparse(link_lc)

    # Filter query params: drop only utm_*
    qsl = parse_qsl(p.query, keep_blank_values=True)
    filtered = [(k, v) for (k, v) in qsl if not k.startswith("utm_")]
    new_query = urlencode(filtered, doseq=True)

    normalized = urlunparse(
        (
            p.scheme,
            p.netloc,
            p.path,
            p.params,
            new_query,
            p.fragment,
        )
    )

    # Remove trailing slash (but don't turn "https://x.com/" into "https://x.com")
    if normalized.endswith("/") and urlparse(normalized).path != "/":
        normalized = normalized.rstrip("/")

    return f"url:{normalized}"


def normalize(state: V2State) -> Dict[str, Any]:
    """
    Contract:
    - Reads: merged_source_units
    - Writes: normalized_items
    - MUST preserve order
    - MUST NOT emit abort_reason
    - MUST return delta only
    """
    merged_units = state.get("merged_source_units", []) or []
    normalized_items: List[Dict[str, Any]] = []

    for unit in merged_units:
        item = _normalize_one(unit)
        if item is not None:
            normalized_items.append(item)

    return {"normalized_items": normalized_items}


def _normalize_one(unit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Minimal, based on your real payload shape
    try:
        source = unit.get("source")
        payload = unit.get("payload") or {}

        title = payload.get("title")
        # Prefer "abstract" (contrato base) pero aceptar "content" como alias
        content = payload.get("abstract") or payload.get("content")
        published_at = payload.get("published_at")
        link = payload.get("link")

        # Required fields
        if not all(isinstance(x, str) and x.strip() for x in [title, content, published_at, link, source]):
            return None

        canonical_id = _generate_canonical_id(link)

        return {
            "title": title.strip(),
            "content": content.strip(),
            "published_at": published_at.strip(),
            "link": link.strip(),
            "source": source.strip(),
            "canonical_id": canonical_id,
        }
    except Exception:
        return None