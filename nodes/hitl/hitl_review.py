from __future__ import annotations

from typing import Any


VALID_HITL_ACTIONS = {"accept", "subset", "cancel"}


def hitl_review(state: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    if "selected_items" not in state:
        raise KeyError("selected_items missing in state")

    selected_items = state["selected_items"]
    action = decision["action"]

    if action not in VALID_HITL_ACTIONS:
        raise ValueError(f"Invalid HITL action: {action!r}")

    if action == "accept":
        return {
            "hitl_action": "accept",
            "hitl_remove_keys": [],
        }

    if action == "cancel":
        return {
            "hitl_action": "cancel",
            "abort_reason": "USER_ABORT",
        }

    remove_keys = decision.get("remove_keys", [])
    if not isinstance(remove_keys, list):
        raise ValueError("remove_keys must be a list")
    if len(remove_keys) != len(set(remove_keys)):
        raise ValueError("remove_keys must not contain duplicates")

    selected_ids = {item.get("canonical_id") for item in selected_items}
    invalid = [key for key in remove_keys if key not in selected_ids]
    if invalid:
        raise ValueError(f"remove_keys contains unknown canonical_id values: {invalid}")

    return {
        "hitl_action": "subset",
        "hitl_remove_keys": remove_keys,
    }
