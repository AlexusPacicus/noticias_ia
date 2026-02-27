from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

HF_DAILY_PAPERS_API_URL = "https://huggingface.co/api/daily_papers"
HTTP_TIMEOUT_SECONDS = 15
MAX_RESULTS = 25


def _format_utc(dt: datetime) -> str:
    """Devuelve un ISO8601 UTC con sufijo Z (sin microsegundos)."""
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_items(now_dt: datetime) -> List[Dict[str, Any]]:
    fetched_at = _format_utc(now_dt)
    published_at = _format_utc(now_dt - timedelta(days=1))

    return [
        {
            "source": "huggingface",
            "source_seq": 0,
            "fetched_at": fetched_at,
            "payload": {
                "title": "HF Paper A",
                "abstract": "HF Abstract A",
                "published_at": published_at,
                "link": "https://huggingface.co/paper/0001",
            },
        },
        {
            "source": "huggingface",
            "source_seq": 1,
            "fetched_at": fetched_at,
            "payload": {
                "title": "HF Paper B",
                "abstract": "HF Abstract B",
                "published_at": published_at,
                "link": "https://huggingface.co/paper/0002",
            },
        },
    ]


def _coerce_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalize_published_at(raw: str, now_dt: datetime) -> str:
    if not raw:
        return _format_utc(now_dt)

    ts = raw.strip()
    if len(ts) == 10 and ts.count("-") == 2:
        ts = f"{ts}T00:00:00+00:00"
    elif ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return _format_utc(dt)
    except ValueError:
        return _format_utc(now_dt)


def _extract_items_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if isinstance(payload, dict):
        for key in ["papers", "items", "results", "data"]:
            data = payload.get(key)
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
    return []


def _extract_link(record: Dict[str, Any]) -> str:
    link = _coerce_str(record.get("link") or record.get("url"))
    if link:
        return link

    slug = _coerce_str(record.get("id") or record.get("slug"))
    if slug:
        if slug.startswith("http://") or slug.startswith("https://"):
            return slug
        return f"https://huggingface.co/papers/{slug}"
    return ""


def _extract_live_paper(item: Dict[str, Any]) -> Dict[str, Any]:
    # Some payloads nest the paper under "paper".
    nested = item.get("paper")
    return nested if isinstance(nested, dict) else item


def _fetch_live_items(query: str, now_dt: datetime) -> List[Dict[str, Any]]:
    params = urlencode({"q": query, "limit": MAX_RESULTS})
    url = f"{HF_DAILY_PAPERS_API_URL}?{params}"
    req = Request(url, headers={"User-Agent": "noticias-v2/1.0"})

    with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="replace"))

    raw_items = _extract_items_list(payload)
    fetched_at = _format_utc(now_dt)
    items: List[Dict[str, Any]] = []

    for idx, raw in enumerate(raw_items):
        paper = _extract_live_paper(raw)
        title = _coerce_str(paper.get("title"))
        abstract = _coerce_str(
            paper.get("summary") or paper.get("abstract") or paper.get("content")
        )
        published_at = _normalize_published_at(
            _coerce_str(
                paper.get("publishedAt")
                or paper.get("published_at")
                or paper.get("date")
                or paper.get("createdAt")
            ),
            now_dt,
        )
        link = _extract_link(paper)

        if not all([title, abstract, link]):
            continue

        items.append(
            {
                "source": "huggingface",
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


def fetch_huggingface_with_mode(state: Dict[str, Any], *, mode: str) -> Dict[str, Any]:
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
                    "huggingface": {
                        "status": "failed",
                        "error": {"code": "HF_INVALID_QUERY", "message": "Missing query"},
                        "items": [],
                    }
                }
            }

        try:
            items = _fetch_live_items(query, now_dt)
            return {
                "source_units": {
                    "huggingface": {
                        "status": "ok",
                        "error": None,
                        "items": items,
                    }
                }
            }
        except Exception as exc:
            return {
                "source_units": {
                    "huggingface": {
                        "status": "failed",
                        "error": {"code": "HF_FETCH_ERROR", "message": str(exc)},
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
            "huggingface": {
                "status": "ok",
                "error": None,
                "items": items,
            }
        }
    }


def fetch_huggingface(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo simulado y determinista (modo stub por defecto).
    No usa endpoint real.
    """
    return fetch_huggingface_with_mode(state, mode="stub")
