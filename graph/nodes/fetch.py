import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

_TIME_WINDOW_DAYS = {
    "last_24h": 1,
    "last_3_days": 3,
    "last_7_days": 7,
}

_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch(state: dict) -> dict:
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
        raise ValueError("FETCH_SOURCE_ERROR")

    try:
        root = ET.fromstring(raw_xml)
        entries = root.findall("atom:entry", _NS)
    except Exception:
        raise ValueError("FETCH_NOT_ITERABLE")

    # Filtro temporal determinista (UTC, bordes inclusivos)
    days = _TIME_WINDOW_DAYS[time_window]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    external_units = []
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
            external_units.append(entry)

    state["external_units"] = external_units
    return state
