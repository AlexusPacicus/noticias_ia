from typing import Any, Dict, List

from graph.v2.state import V2State


class V21State(V2State, total=False):
    hitl_action: str
    hitl_remove_keys: List[str]
    hitl_selected_items: List[Dict[str, Any]]
