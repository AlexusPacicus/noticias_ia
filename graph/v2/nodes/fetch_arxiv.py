from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta


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


def fetch_arxiv_with_mode(state: Dict[str, Any], *, mode: str) -> Dict[str, Any]:
    """
    Implementación parametrizada por modo.
    - mode="stub": comportamiento determinista congelado.
    - mode="live": fechas relativas a now UTC.
    """
    if mode == "live":
        now_dt = datetime.now(timezone.utc)
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