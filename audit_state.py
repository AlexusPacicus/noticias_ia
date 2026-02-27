#!/usr/bin/env python3
import argparse
import json
import sys
from typing import Any, Dict, List, Sequence, Tuple


ALLOWED_KEYS = {
    "query",
    "time_window",
    "top_k",
    "input_raw",
    "input_validated",
    "source_units",
    "merged_source_units",
    "normalized_items",
    "filtered_items",
    "deduped_items",
    "ranked_items",
    "selected_items",
    "summary_items",
    "summary_stats",
    "output",
    "abort_reason",
}

VALID_TIME_WINDOWS = {"last_24h", "last_3_days", "last_7_days"}
SOURCE_PRIORITY = ["arxiv", "huggingface"]
ABORT_CODES = {
    "EMPTY_INPUT_PAYLOAD",
    "INVALID_QUERY",
    "INVALID_TIME_WINDOW",
    "INVALID_TOP_K",
    "FETCH_ALL_SOURCES_FAILED",
    "UNKNOWN_SOURCE_PRIORITY",
    "NO_ITEMS_IN_TIME_WINDOW",
    "NO_ITEMS_AFTER_DEDUPE",
    "RANK_QUERY_EMPTY_AFTER_NORMALIZATION",
    "SELECT_MISSING_RANKED_ITEMS",
    "SELECT_TOPK_INVALID",
    "SUMMARY_ALL_ITEMS_FAILED",
}

INVARIANT_CATALOG: Sequence[Tuple[str, str]] = (
    ("INV-01", "Lista cerrada de claves: no existen claves fuera del conjunto contractual."),
    ("INV-02", "Mutua exclusión terminal: output y abort_reason no coexisten."),
    ("INV-03", "abort_reason, si existe, pertenece al conjunto cerrado de códigos."),
    ("INV-04", "input_validated respeta shape/tipos y dominio (query, time_window, top_k)."),
    ("INV-05", "Dependencias mínimas entre fases (no hay claves de fases posteriores sin previas)."),
    ("INV-06", "source_units respeta shape por fuente: status/error/items y consistencia status."),
    ("INV-07", "merged_source_units está ordenado por (SOURCE_PRIORITY, source_seq)."),
    ("INV-08", "deduped_items no contiene canonical_id duplicados."),
    ("INV-09", "ranked_items respeta orden total y rank_position secuencial."),
    ("INV-10", "selected_items es prefijo de ranked_items."),
    ("INV-11", "summary_stats y summary_items cumplen invariantes de conteo y schema."),
    ("INV-12", "output cumple schema mínimo y consistencia de conteos."),
    ("INV-13", "Restricciones de valor en aborts específicos."),
)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class Auditor:
    def __init__(self, state: Dict[str, Any]) -> None:
        self.state = state
        self.findings: List[Dict[str, str]] = []

    def add(self, inv_id: str, message: str) -> None:
        self.findings.append({"invariant": inv_id, "message": message})

    def run(self) -> List[Dict[str, str]]:
        self.check_keys()
        self.check_terminal_mutual_exclusion()
        self.check_abort_reason()
        self.check_input_validated()
        self.check_phase_dependencies()
        self.check_source_units()
        self.check_merged_source_units_order()
        self.check_dedupe_unique_canonical_id()
        self.check_ranked_items()
        self.check_selected_prefix()
        self.check_summary_contract()
        self.check_output_contract()
        self.check_abort_value_constraints()
        return self.findings

    def check_keys(self) -> None:
        unknown = sorted(set(self.state.keys()) - ALLOWED_KEYS)
        if unknown:
            self.add("INV-01", f"Claves no permitidas: {unknown}")

    def check_terminal_mutual_exclusion(self) -> None:
        if "output" in self.state and "abort_reason" in self.state:
            self.add("INV-02", "output y abort_reason coexisten.")

    def check_abort_reason(self) -> None:
        if "abort_reason" not in self.state:
            return
        reason = self.state.get("abort_reason")
        if not isinstance(reason, str):
            self.add("INV-03", "abort_reason no es string.")
            return
        if reason not in ABORT_CODES:
            self.add("INV-03", f"abort_reason fuera de catálogo: {reason}")

    def check_input_validated(self) -> None:
        if "input_validated" not in self.state:
            return
        iv = self.state.get("input_validated")
        if not isinstance(iv, dict):
            self.add("INV-04", "input_validated no es objeto.")
            return
        required = {"query", "time_window", "top_k"}
        missing = sorted(required - set(iv.keys()))
        if missing:
            self.add("INV-04", f"input_validated sin claves requeridas: {missing}")
            return
        if not isinstance(iv.get("query"), str) or not iv.get("query", "").strip():
            self.add("INV-04", "input_validated.query inválido.")
        if iv.get("time_window") not in VALID_TIME_WINDOWS:
            self.add("INV-04", "input_validated.time_window inválido.")
        top_k = iv.get("top_k")
        if not _is_int(top_k) or not (1 <= top_k <= 5):
            self.add("INV-04", "input_validated.top_k inválido (debe ser int en [1..5]).")

    def check_phase_dependencies(self) -> None:
        deps = {
            "input_validated": ["input_raw"],
            "source_units": ["input_validated"],
            "merged_source_units": ["source_units"],
            "normalized_items": ["merged_source_units"],
            "filtered_items": ["normalized_items"],
            "deduped_items": ["filtered_items"],
            "ranked_items": ["deduped_items"],
            "selected_items": ["ranked_items"],
            "summary_items": ["selected_items"],
            "summary_stats": ["selected_items"],
            "output": ["summary_items", "summary_stats", "input_validated"],
        }
        for key, required in deps.items():
            if key not in self.state:
                continue
            missing = [k for k in required if k not in self.state]
            if missing:
                self.add("INV-05", f"{key} existe sin dependencias previas: faltan {missing}")

        if "abort_reason" in self.state:
            forbidden_after_abort = [
                "merged_source_units",
                "normalized_items",
                "filtered_items",
                "deduped_items",
                "ranked_items",
                "selected_items",
                "summary_items",
                "summary_stats",
                "output",
            ]
            for clave in forbidden_after_abort:
                if clave in self.state:
                    self.add("INV-05", f"abort_reason presente pero existe clave de fase posterior: {clave}")

    def check_source_units(self) -> None:
        if "source_units" not in self.state:
            return
        su = self.state.get("source_units")
        if not isinstance(su, dict):
            self.add("INV-06", "source_units no es objeto.")
            return
        for source, data in su.items():
            if source not in SOURCE_PRIORITY:
                self.add("INV-06", f"source_units contiene fuente desconocida: {source}")
                continue
            if not isinstance(data, dict):
                self.add("INV-06", f"source_units[{source}] no es objeto.")
                continue
            status = data.get("status")
            error = data.get("error")
            items = data.get("items")
            if status not in {"ok", "failed"}:
                self.add("INV-06", f"source_units[{source}].status inválido: {status}")
            if not isinstance(items, list):
                self.add("INV-06", f"source_units[{source}].items no es lista.")
                continue
            if status == "ok" and error is not None:
                self.add("INV-06", f"source_units[{source}] inconsistente: status=ok con error!=null.")
            if status == "failed":
                if items != []:
                    self.add("INV-06", f"source_units[{source}] inconsistente: status=failed con items no vacíos.")
                if error is None:
                    self.add("INV-06", f"source_units[{source}] inconsistente: status=failed sin error.")

    def check_merged_source_units_order(self) -> None:
        if "merged_source_units" not in self.state:
            return
        msu = self.state.get("merged_source_units")
        if not isinstance(msu, list):
            self.add("INV-07", "merged_source_units no es lista.")
            return

        observed_keys = []
        for i, item in enumerate(msu):
            if not isinstance(item, dict):
                self.add("INV-07", f"merged_source_units[{i}] no es objeto.")
                return
            source = item.get("source")
            source_seq = item.get("source_seq")
            if source not in SOURCE_PRIORITY:
                self.add("INV-07", f"merged_source_units[{i}].source inválido: {source}")
                return
            if not _is_int(source_seq) or source_seq < 0:
                self.add("INV-07", f"merged_source_units[{i}].source_seq inválido: {source_seq}")
                return
            observed_keys.append((SOURCE_PRIORITY.index(source), source_seq))

        if observed_keys != sorted(observed_keys):
            self.add("INV-07", "merged_source_units no respeta orden contractual por prioridad/source_seq.")

    def check_dedupe_unique_canonical_id(self) -> None:
        if "deduped_items" not in self.state:
            return
        items = self.state.get("deduped_items")
        if not isinstance(items, list):
            self.add("INV-08", "deduped_items no es lista.")
            return
        seen = set()
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                self.add("INV-08", f"deduped_items[{i}] no es objeto.")
                continue
            cid = item.get("canonical_id")
            if not isinstance(cid, str) or not cid:
                self.add("INV-08", f"deduped_items[{i}] sin canonical_id válido.")
                continue
            if cid in seen:
                self.add("INV-08", f"canonical_id duplicado en deduped_items: {cid}")
            seen.add(cid)

    def check_ranked_items(self) -> None:
        if "ranked_items" not in self.state:
            return
        ranked = self.state.get("ranked_items")
        if not isinstance(ranked, list):
            self.add("INV-09", "ranked_items no es lista.")
            return

        tuples: List[Tuple[Any, Any, Any]] = []
        for i, item in enumerate(ranked):
            if not isinstance(item, dict):
                self.add("INV-09", f"ranked_items[{i}] no es objeto.")
                return
            score = item.get("bm25_score")
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                self.add("INV-09", f"ranked_items[{i}].bm25_score inválido.")
                return
            rp = item.get("rank_position")
            if not _is_int(rp) or rp != i + 1:
                self.add("INV-09", f"ranked_items[{i}].rank_position inválido (esperado {i + 1}).")
            title = item.get("title")
            link = item.get("link")
            if not isinstance(title, str) or not isinstance(link, str):
                self.add("INV-09", f"ranked_items[{i}] sin title/link string.")
                return
            tuples.append((-float(score), title, link))

        if tuples != sorted(tuples):
            self.add("INV-09", "ranked_items no respeta orden total (-bm25_score, title ASC, link ASC).")

    def check_selected_prefix(self) -> None:
        if "selected_items" not in self.state:
            return
        selected = self.state.get("selected_items")
        ranked = self.state.get("ranked_items")
        if not isinstance(selected, list):
            self.add("INV-10", "selected_items no es lista.")
            return
        if not isinstance(ranked, list):
            self.add("INV-10", "selected_items existe sin ranked_items lista.")
            return
        if selected != ranked[: len(selected)]:
            self.add("INV-10", "selected_items no coincide con prefijo de ranked_items.")

    def check_summary_contract(self) -> None:
        if "summary_stats" in self.state:
            stats = self.state.get("summary_stats")
            if not isinstance(stats, dict):
                self.add("INV-11", "summary_stats no es objeto.")
            else:
                keys = set(stats.keys())
                if keys != {"ok", "failed"}:
                    self.add("INV-11", f"summary_stats keys inválidas: {sorted(keys)}")
                else:
                    for k in ("ok", "failed"):
                        if not _is_int(stats[k]) or stats[k] < 0:
                            self.add("INV-11", f"summary_stats.{k} inválido (int >= 0 requerido).")

        if "summary_items" in self.state:
            items = self.state.get("summary_items")
            if not isinstance(items, list):
                self.add("INV-11", "summary_items no es lista.")
                return
            required = {"rank_position", "title", "summary", "link", "source"}
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    self.add("INV-11", f"summary_items[{i}] no es objeto.")
                    continue
                keys = set(item.keys())
                if keys != required:
                    self.add("INV-11", f"summary_items[{i}] keys inválidas: {sorted(keys)}")
                if not _is_int(item.get("rank_position")):
                    self.add("INV-11", f"summary_items[{i}].rank_position inválido.")
                for f in ("title", "summary", "link", "source"):
                    if not isinstance(item.get(f), str) or not item.get(f, "").strip():
                        self.add("INV-11", f"summary_items[{i}].{f} inválido.")

        if "summary_items" in self.state and "summary_stats" in self.state:
            items = self.state.get("summary_items")
            stats = self.state.get("summary_stats")
            if isinstance(items, list) and isinstance(stats, dict):
                ok = stats.get("ok")
                if _is_int(ok) and len(items) != ok:
                    self.add("INV-11", "len(summary_items) != summary_stats.ok")

        if "selected_items" in self.state and "summary_stats" in self.state:
            selected = self.state.get("selected_items")
            stats = self.state.get("summary_stats")
            if isinstance(selected, list) and isinstance(stats, dict):
                ok = stats.get("ok")
                failed = stats.get("failed")
                if _is_int(ok) and _is_int(failed) and ok + failed != len(selected):
                    self.add("INV-11", "summary_stats.ok + failed != len(selected_items)")

    def check_output_contract(self) -> None:
        if "output" not in self.state:
            return
        output = self.state.get("output")
        if not isinstance(output, dict):
            self.add("INV-12", "output no es objeto.")
            return
        expected_keys = {
            "topic",
            "time_window",
            "requested_k",
            "returned_k",
            "failed_summaries",
            "results",
        }
        keys = set(output.keys())
        if keys != expected_keys:
            self.add("INV-12", f"output keys inválidas: {sorted(keys)}")
            return

        if not isinstance(output["topic"], str) or not output["topic"].strip():
            self.add("INV-12", "output.topic inválido.")
        if output["time_window"] not in VALID_TIME_WINDOWS:
            self.add("INV-12", "output.time_window inválido.")
        if not _is_int(output["requested_k"]) or not (1 <= output["requested_k"] <= 5):
            self.add("INV-12", "output.requested_k inválido.")
        if not _is_int(output["returned_k"]) or output["returned_k"] < 0:
            self.add("INV-12", "output.returned_k inválido.")
        if not _is_int(output["failed_summaries"]) or output["failed_summaries"] < 0:
            self.add("INV-12", "output.failed_summaries inválido.")

        results = output["results"]
        if not isinstance(results, list):
            self.add("INV-12", "output.results no es lista.")
            return

        if _is_int(output["returned_k"]) and output["returned_k"] != len(results):
            self.add("INV-12", "output.returned_k no coincide con len(output.results).")
        if _is_int(output["requested_k"]) and _is_int(output["returned_k"]):
            if output["returned_k"] > output["requested_k"]:
                self.add("INV-12", "output.returned_k > output.requested_k.")

        required_result_keys = {"title", "summary", "link", "source", "rank_position"}
        for i, item in enumerate(results):
            if not isinstance(item, dict):
                self.add("INV-12", f"output.results[{i}] no es objeto.")
                continue
            keys = set(item.keys())
            if keys != required_result_keys:
                self.add("INV-12", f"output.results[{i}] keys inválidas: {sorted(keys)}")
            for f in ("title", "summary", "link", "source"):
                if not isinstance(item.get(f), str) or not item.get(f, "").strip():
                    self.add("INV-12", f"output.results[{i}].{f} inválido.")
            if not _is_int(item.get("rank_position")):
                self.add("INV-12", f"output.results[{i}].rank_position inválido.")

    def check_abort_value_constraints(self) -> None:
        reason = self.state.get("abort_reason")
        if reason == "NO_ITEMS_IN_TIME_WINDOW":
            if self.state.get("filtered_items", None) != []:
                self.add("INV-13", "Abort NO_ITEMS_IN_TIME_WINDOW requiere filtered_items == [].")
        elif reason == "NO_ITEMS_AFTER_DEDUPE":
            if self.state.get("deduped_items", None) != []:
                self.add("INV-13", "Abort NO_ITEMS_AFTER_DEDUPE requiere deduped_items == [].")
        elif reason == "SUMMARY_ALL_ITEMS_FAILED":
            stats = self.state.get("summary_stats")
            ok = stats.get("ok") if isinstance(stats, dict) else None
            if ok != 0:
                self.add("INV-13", "Abort SUMMARY_ALL_ITEMS_FAILED requiere summary_stats.ok == 0.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita un dump JSON de state v2 contra invariantes contractuales mínimas."
    )
    parser.add_argument("state_json_path", nargs="?", help="Ruta al JSON con el state a auditar.")
    parser.add_argument(
        "--list-invariants",
        action="store_true",
        help="Imprime la lista explícita de invariantes y termina.",
    )
    args = parser.parse_args()

    if args.list_invariants:
        print("INVARIANTES_MINIMAS:")
        for inv_id, text in INVARIANT_CATALOG:
            print(f"- {inv_id}: {text}")
        return 0

    if not args.state_json_path:
        print("ERROR: falta state_json_path.")
        return 1

    try:
        with open(args.state_json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: archivo no encontrado: {args.state_json_path}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: JSON inválido: {exc}")
        return 1

    if not isinstance(payload, dict):
        print("ERROR: el dump JSON debe ser un objeto (state dict).")
        return 1

    findings = Auditor(payload).run()

    if not findings:
        print("SIN_HALLAZGOS")
        return 0

    print("VIOLACIONES:")
    for i, finding in enumerate(findings, start=1):
        print(f"{i}. [{finding['invariant']}] {finding['message']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
