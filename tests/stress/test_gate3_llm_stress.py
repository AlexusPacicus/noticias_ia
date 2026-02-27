from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

import pytest

import graph.v2.graph as gmod


RUNS = 30
TOP_K = 3
ARTIFACT_PATH = Path("tests/artifacts/gate3_llm_stress_report.json")


def _fake_fetch_arxiv(_state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_units": {
            "arxiv": {
                "status": "ok",
                "error": None,
                "items": [
                    {
                        "source": "arxiv",
                        "source_seq": 0,
                        "payload": {
                            "title": "Agentic Systems for Retrieval",
                            "content": "agentic ai retrieval planning",
                            "published_at": "2026-02-20T00:00:00Z",
                            "link": "https://arxiv.org/abs/2602.00001",
                        },
                    },
                    {
                        "source": "arxiv",
                        "source_seq": 1,
                        "payload": {
                            "title": "Reliability in LLM Ops",
                            "content": "llm operations reliability guardrails",
                            "published_at": "2026-02-20T00:00:00Z",
                            "link": "https://arxiv.org/abs/2602.00002",
                        },
                    },
                    {
                        "source": "arxiv",
                        "source_seq": 2,
                        "payload": {
                            "title": "Robust Summary Pipelines",
                            "content": "summary pipeline robustness deterministic tests",
                            "published_at": "2026-02-20T00:00:00Z",
                            "link": "https://arxiv.org/abs/2602.00003",
                        },
                    },
                ],
            }
        }
    }


def _passthrough_filter(state: Dict[str, Any]) -> Dict[str, Any]:
    return {"filtered_items": state.get("normalized_items", [])}


@pytest.mark.integration
def test_gate3_llm_stress_report(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gmod, "fetch_arxiv", _fake_fetch_arxiv)
    monkeypatch.setattr(gmod, "filter_by_time_window", _passthrough_filter)

    llm_counters = {
        "timeout_occurrences": 0,
        "invalid_json_occurrences": 0,
        "fallback_occurrences": 0,
    }
    llm_call_index = {"value": 0}

    def deterministic_generate_summary(_item: Dict[str, str]) -> Dict[str, Any]:
        idx = llm_call_index["value"]
        llm_call_index["value"] += 1

        run_idx = idx // TOP_K
        pos_in_run = idx % TOP_K

        if pos_in_run == 1:
            mode = run_idx % 3
            if mode == 0:
                llm_counters["timeout_occurrences"] += 1
                raise TimeoutError("simulated timeout")
            if mode == 1:
                llm_counters["invalid_json_occurrences"] += 1
                raise ValueError("simulated invalid json")

            llm_counters["fallback_occurrences"] += 1
            return {
                "summary": f"fallback summary run-{run_idx + 1}",
                "mode": "fallback_text",
            }

        return {"summary": f"summary run-{run_idx + 1} item-{pos_in_run + 1}"}

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        deterministic_generate_summary,
    )

    graph = gmod.build_graph(sources=("arxiv",))

    summary_success_total = 0
    summary_failed_total = 0
    abort_reason_occurrences = 0
    empty_summary_occurrences = 0
    silent_exception_occurrences = 0
    summary_stats_coherence_violations: List[str] = []
    missing_output_violations: List[str] = []
    invalid_returned_k_violations: List[str] = []
    latencies: List[float] = []

    per_run: List[Dict[str, Any]] = []

    for run_number in range(1, RUNS + 1):
        start = perf_counter()
        caught_exc: Exception | None = None
        result: Dict[str, Any] = {}

        try:
            result = graph.invoke(
                {
                    "query": "agentic ai reliability",
                    "time_window": "last_7_days",
                    "top_k": TOP_K,
                }
            )
        except Exception as exc:  # defensive: should remain zero
            caught_exc = exc

        latency = perf_counter() - start
        latencies.append(latency)

        run_record: Dict[str, Any] = {
            "run": run_number,
            "latency_seconds": latency,
        }

        if caught_exc is not None:
            silent_exception_occurrences += 1
            run_record["exception_type"] = type(caught_exc).__name__
            run_record["exception_message"] = str(caught_exc)
            per_run.append(run_record)
            continue

        if result.get("abort_reason") is not None:
            abort_reason_occurrences += 1
            run_record["abort_reason"] = result.get("abort_reason")

        summary_stats = result.get("summary_stats") or {}
        ok = int(summary_stats.get("ok", 0))
        failed = int(summary_stats.get("failed", 0))
        summary_success_total += ok
        summary_failed_total += failed
        if ok + failed != TOP_K:
            msg = (
                f"run {run_number}: summary_stats incoherent "
                f"(ok={ok}, failed={failed}, top_k={TOP_K})"
            )
            summary_stats_coherence_violations.append(msg)
            run_record["summary_stats_violation"] = msg

        has_output = isinstance(result.get("output"), dict)
        if not has_output:
            msg = f"run {run_number}: missing output object"
            missing_output_violations.append(msg)
            run_record["output_violation"] = msg

        output = result.get("output") if has_output else {}
        output_results = output.get("results") or []
        returned_k = output.get("returned_k")
        if not isinstance(returned_k, int) or not (1 <= returned_k <= TOP_K):
            msg = (
                f"run {run_number}: invalid returned_k={returned_k!r} "
                f"(expected int in [1, {TOP_K}])"
            )
            invalid_returned_k_violations.append(msg)
            run_record["returned_k_violation"] = msg

        empty_in_run = 0
        for item in output_results:
            summary_text = item.get("summary") if isinstance(item, dict) else ""
            if not isinstance(summary_text, str) or not summary_text.strip():
                empty_in_run += 1

        empty_summary_occurrences += empty_in_run

        run_record.update(
            {
                "summary_stats": {"ok": ok, "failed": failed},
                "returned_k": returned_k,
                "failed_summaries": output.get("failed_summaries"),
                "empty_summaries": empty_in_run,
            }
        )
        per_run.append(run_record)

    min_latency = min(latencies)
    max_latency = max(latencies)
    latency_ratio = max_latency / min_latency if min_latency > 0 else float("inf")

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "runs": RUNS,
        "metrics": {
            "successful_summaries": summary_success_total,
            "failed_summaries": summary_failed_total,
            "timeout_occurrences": llm_counters["timeout_occurrences"],
            "invalid_json_occurrences": llm_counters["invalid_json_occurrences"],
            "fallback_occurrences": llm_counters["fallback_occurrences"],
            "abort_reason_occurrences": abort_reason_occurrences,
            "empty_summary_occurrences": empty_summary_occurrences,
            "silent_exception_occurrences": silent_exception_occurrences,
            "summary_stats_coherence_violations": len(summary_stats_coherence_violations),
            "missing_output_violations": len(missing_output_violations),
            "invalid_returned_k_violations": len(invalid_returned_k_violations),
            "min_latency_seconds": min_latency,
            "max_latency_seconds": max_latency,
            "latency_ratio_max_over_min": latency_ratio,
        },
        "per_run": per_run,
    }
    ARTIFACT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    assert not summary_stats_coherence_violations, (
        "Summary stats coherence violations found: "
        + "; ".join(summary_stats_coherence_violations)
    )
    assert not missing_output_violations, (
        "Missing output violations found: " + "; ".join(missing_output_violations)
    )
    assert not invalid_returned_k_violations, (
        "Invalid returned_k violations found: "
        + "; ".join(invalid_returned_k_violations)
    )
    assert max_latency < 5, (
        f"Latency spike guard failed: max latency {max_latency:.6f}s is >= 5s"
    )
    assert latency_ratio < 10, (
        "Latency stability guard failed: "
        f"max/min ratio {latency_ratio:.6f} is >= 10 "
        f"(max={max_latency:.6f}s, min={min_latency:.6f}s)"
    )
    assert abort_reason_occurrences == 0
    assert empty_summary_occurrences == 0
    assert silent_exception_occurrences == 0
