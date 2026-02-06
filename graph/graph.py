from langgraph.graph import StateGraph, END

from graph.nodes.collect_input import collect_input
from graph.nodes.validate_input import validate_input
from graph.nodes.fetch import fetch
from graph.nodes.normalize import normalize
from graph.nodes.rank import rank
from graph.nodes.select import select
from graph.nodes.summarize import summarize


def build_graph():
    g = StateGraph(dict)

    g.add_node("collect_input", collect_input)
    g.add_node("validate_input", validate_input)
    g.add_node("fetch", fetch)
    g.add_node("normalize", normalize)
    g.add_node("rank", rank)
    g.add_node("select", select)
    g.add_node("summarize", summarize)

    g.set_entry_point("collect_input")

    g.add_edge("collect_input", "validate_input")
    g.add_edge("validate_input", "fetch")
    g.add_edge("fetch", "normalize")
    g.add_edge("normalize", "rank")
    g.add_edge("rank", "select")
    g.add_edge("select", "summarize")
    g.add_edge("summarize", END)

    return g.compile()
