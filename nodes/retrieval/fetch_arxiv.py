from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

# Nodo fetch_arxiv - Responsabilidad: obtener SourceUnits de arXiv (stub/live).

ARXIV_API_URL = "https://export.arxiv.org/api/query"
HTTP_TIMEOUT_SECONDS = 15
MAX_RESULTS = 25
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

def _format_utc(dt: datetime) -> str:
    """Devuelve un ISO8601 UTC con sufijo Z (sin microsegundos)."""
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_items(now_dt: datetime) -> List[Dict[str, Any]]:
    fetched_at = _format_utc(now_dt)
    published_at = _format_utc(now_dt - timedelta(days=1))

    return [
        {
            "source": "arxiv",
            "source_seq": 0,
            "fetched_at": fetched_at,
            "payload": {
                "title": "Paper A",
                "abstract": "Abstract A",
                "published_at": published_at,
                "link": "https://arxiv.org/abs/1234.0001",
            },
        },
        {
            "source": "arxiv",
            "source_seq": 1,
            "fetched_at": fetched_at,
            "payload": {
                "title": "Paper B",
                "abstract": "Abstract B",
                "published_at": published_at,
                "link": "https://arxiv.org/abs/1234.0002",
            },
        },
    ]


def _collapse_ws(text: str) -> str:
    return " ".join((text or "").split())


def _extract_link(entry: ET.Element) -> str:
    for link in entry.findall("atom:link", ATOM_NS):
        rel = link.attrib.get("rel", "")
        href = link.attrib.get("href", "")
        if rel == "alternate" and href:
            return href
    id_el = entry.find("atom:id", ATOM_NS)
    return (id_el.text or "").strip() if id_el is not None else ""


def _fetch_live_items(query: str, now_dt: datetime) -> List[Dict[str, Any]]:
    params = urlencode(
        {
            "search_query": f"all:{query}",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": MAX_RESULTS,
        }
    )
    url = f"{ARXIV_API_URL}?{params}"
    req = Request(url, headers={"User-Agent": "noticias-v2/1.0"})

    with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
        xml_text = resp.read().decode("utf-8", errors="replace")

    root = ET.fromstring(xml_text)
    fetched_at = _format_utc(now_dt)
    items: List[Dict[str, Any]] = []

    for idx, entry in enumerate(root.findall("atom:entry", ATOM_NS)):
        title_el = entry.find("atom:title", ATOM_NS)
        summary_el = entry.find("atom:summary", ATOM_NS)
        published_el = entry.find("atom:published", ATOM_NS)

        title = _collapse_ws(title_el.text if title_el is not None else "")
        abstract = _collapse_ws(summary_el.text if summary_el is not None else "")
        published_at = _collapse_ws(published_el.text if published_el is not None else "")
        link = _extract_link(entry)

        if not all([title, abstract, published_at, link]):
            continue

        items.append(
            {
                "source": "arxiv",
                "source_seq": idx,
                "fetched_at": fetched_at,
                "payload": {
                    "title": title,
                    "abstract": abstract,
                    "published_at": published_at,
                    "link": link,
                },
            }
        )

    return items


def fetch_arxiv_with_mode(state: Dict[str, Any], *, mode: str) -> Dict[str, Any]:
    """
    Implementación parametrizada por modo.
    - mode="stub": comportamiento determinista congelado.
    - mode="live": fechas relativas a now UTC.
    """
    if mode == "live":
        now_dt = datetime.now(timezone.utc)
        query = ((state.get("input_validated") or {}).get("query") or "").strip()
        if not query:
            return {
                "source_units": {
                    "arxiv": {
                        "status": "failed",
                        "error": {"code": "ARXIV_INVALID_QUERY", "message": "Missing query"},
                        "items": [],
                    }
                }
            }

        try:
            items = _fetch_live_items(query, now_dt)
            return {
                "source_units": {
                    "arxiv": {
                        "status": "ok",
                        "error": None,
                        "items": items,
                    }
                }
            }
        except Exception as exc:
            return {
                "source_units": {
                    "arxiv": {
                        "status": "failed",
                        "error": {"code": "ARXIV_FETCH_ERROR", "message": str(exc)},
                        "items": [],
                    }
                }
            }
    else:
        # Modo stub: exactamente la fecha fija original.
        now_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)

    items = _build_items(now_dt)

    return {
        "source_units": {
            "arxiv": {
                "status": "ok",
                "error": None,
                "items": items,
            }
        }
    }


def fetch_arxiv(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo simulado y determinista (modo stub por defecto).
    No usa endpoint real.
    """
    return fetch_arxiv_with_mode(state, mode="stub")
