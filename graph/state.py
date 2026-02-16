"""
State schemas para el pipeline v1.1.

Define los TypedDict que gobiernan el State del grafo LangGraph:
- InputState:    lo que el usuario pasa a graph.invoke().
- OutputState:   lo que graph.invoke() devuelve.
- PipelineState: state interno completo (superset).
"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict


class InputState(TypedDict):
    """Schema de entrada del grafo. Campos que el usuario proporciona."""

    query: str
    time_window: str
    top_k: NotRequired[int]


class OutputState(TypedDict, total=False):
    """Schema de salida del grafo. Solo lo que el usuario recibe."""

    output: dict
    abort_reason: str


class PipelineState(TypedDict, total=False):
    """State interno completo del pipeline.

    Incluye los campos de entrada del usuario (presentes en la invocacion)
    y los campos contractuales del State v1.1.
    """

    # --- Campos de entrada (presentes al invocar el grafo) ---
    query: str
    time_window: str
    top_k: int

    # --- State contractual v1.1 ---
    input_raw: dict
    input_validated: dict
    external_units: list
    normalized_items: list
    ranked_items: list
    selected_items: list
    output: dict
    abort_reason: str
