from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from graph.state import PipelineState

_TIME_WINDOW_DAYS = {
    "last_24h": 1,
    "last_3_days": 3,
    "last_7_days": 7,
}

_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _entry_to_dict(entry: ET.Element) -> dict:
    """Convierte un entry XML de arXiv a dict serializable.

    Extrae los campos tal cual sin interpretar ni transformar contenido.
    """
    def _text(tag: str) -> str | None:
        el = entry.find(tag, _NS)
        if el is not None and el.text is not None:
            return el.text
        return None

    return {
        "title": _text("atom:title"),
        "id": _text("atom:id"),
        "summary": _text("atom:summary"),
        "published": _text("atom:published"),
    }


def fetch(state: PipelineState) -> dict:
    """Obtiene items de arXiv cs.AI parametrizado por query y time_window.

    Retorna external_units (lista de dicts serializables) o abort_reason.
    """
    validated = state["input_validated"]
    query = validated["query"]
    time_window = validated["time_window"]

    params = urllib.parse.urlencode({
        "search_query": f"cat:cs.AI AND all:{query}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 50,
    })
    url = f"http://export.arxiv.org/api/query?{params}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_xml = resp.read().decode("utf-8")
    except Exception:
        return {"abort_reason": "FETCH_SOURCE_ERROR"}

    try:
        root = ET.fromstring(raw_xml)
        entries = root.findall("atom:entry", _NS)
    except Exception:
        return {"abort_reason": "FETCH_NOT_ITERABLE"}

    # Filtro temporal determinista (UTC, bordes inclusivos)
    days = _TIME_WINDOW_DAYS[time_window]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    external_units: list[dict] = []
    for entry in entries:
        published_el = entry.find("atom:published", _NS)
        if published_el is None or published_el.text is None:
            continue
        try:
            pub_date = datetime.fromisoformat(
                published_el.text.replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            continue
        if pub_date >= cutoff:
            external_units.append(_entry_to_dict(entry))

    return {"external_units": external_units}
