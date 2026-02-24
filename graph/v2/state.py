from typing import TypedDict, Dict, Any, List, Optional, Annotated
from langgraph.channels import BinaryOperatorAggregate


def merge_dicts(old, new):
    old = old or {}
    new = new or {}
    merged = dict(old)
    merged.update(new)
    return merged


class V2State(TypedDict, total=False):
    query: str
    time_window: str
    top_k: int

    input_raw: Dict[str, Any]
    input_validated: Dict[str, Any]

    source_units: Annotated[
        Dict[str, Any],
        BinaryOperatorAggregate({}, merge_dicts)  # 👈 aquí está el fix
    ]

    merged_source_units: List[Dict[str, Any]]

    normalized_items: List[Dict[str, Any]]
    filtered_items: List[Dict[str, Any]]
    deduped_items: List[Dict[str, Any]]
    ranked_items: List[Dict[str, Any]]
    selected_items: List[Dict[str, Any]]

    summary_items: List[Dict[str, Any]]
    summary_stats: Dict[str, int]
    output: Dict[str, Any]

    abort_reason: Optional[str]