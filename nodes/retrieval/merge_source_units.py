from typing import Dict, Any, List

# Nodo merge_source_units - Responsabilidad: consolidar y ordenar SourceUnits, y evaluar gate global de fetch.

SOURCE_PRIORITY = ["arxiv", "huggingface"]


def merge_source_units(state: Dict[str, Any]) -> Dict[str, Any]:
    source_units = state.get("source_units", {})

    # 1️⃣ Gate — fuente desconocida
    unknown = set(source_units.keys()) - set(SOURCE_PRIORITY)
    if unknown:
        return {"abort_reason": "UNKNOWN_SOURCE_PRIORITY"}

    # 2️⃣ Gate B — fallo global real
    if not any(
        data.get("status") == "ok"
        for data in source_units.values()
    ):
        return {"abort_reason": "FETCH_ALL_SOURCES_FAILED"}

    # 3️⃣ Concatenación determinista
    merged: List[Dict[str, Any]] = []

    for source in SOURCE_PRIORITY:
        data = source_units.get(source)
        if not data:
            continue
        if data.get("status") != "ok":
            continue

        merged.extend(data.get("items", []))

    # 4️⃣ Orden contractual total
    merged.sort(
        key=lambda x: (
            SOURCE_PRIORITY.index(x["source"]),
            x["source_seq"],
        )
    )

    return {"merged_source_units": merged}
