from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

import pytest

import graph.v2.graph as gmod


RUNS = 20
TOP_K = 3
ARTIFACT_PATH = Path("tests/artifacts/gate3_real_llm_report.json")
FIXED_INPUT = {
    "query": "agentic ai reliability",
    "time_window": "last_7_days",
    "top_k": TOP_K,
}


def _fixed_fetch_arxiv(_state: Dict[str, Any]) -> Dict[str, Any]:
    # Fixed deterministic corpus; future timestamp avoids time-window drift.
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
                            "abstract": "agentic ai retrieval planning",
                            "published_at": "2099-01-01T00:00:00Z",
                            "link": "https://arxiv.org/abs/2602.00001",
                        },
                    },
                    {
                        "source": "arxiv",
                        "source_seq": 1,
                        "payload": {
                            "title": "Reliability in LLM Ops",
                            "abstract": "llm operations reliability guardrails",
                            "published_at": "2099-01-01T00:00:00Z",
                            "link": "https://arxiv.org/abs/2602.00002",
                        },
                    },
                    {
                        "source": "arxiv",
                        "source_seq": 2,
                        "payload": {
                            "title": "Robust Summary Pipelines",
                            "abstract": "summary pipeline robustness deterministic tests",
                            "published_at": "2099-01-01T00:00:00Z",
                            "link": "https://arxiv.org/abs/2602.00003",
                        },
                    },
                ],
            }
        }
    }


@pytest.mark.integration
def test_gate3_real_llm_stress(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep fetch deterministic while using the real LLM summarize path.
    monkeypatch.setattr(gmod, "fetch_arxiv", _fixed_fetch_arxiv)

    graph = gmod.build_graph(sources=("arxiv",))

    abort_reason_occurrences = 0
    missing_output_occurrences = 0
    empty_summary_occurrences = 0
    exception_occurrences = 0
    zero_ok_occurrences = 0
    summary_stats_coherence_violations: List[str] = []
    returned_k_violations: List[str] = []
    returned_k_ge_2_runs = 0

    latencies: List[float] = []
    per_run: List[Dict[str, Any]] = []

    for run_number in range(1, RUNS + 1):
        started = perf_counter()
        result: Dict[str, Any] = {}
        escaped_exc: Exception | None = None

        try:
            result = graph.invoke(FIXED_INPUT)
        except Exception as exc:  # defensive aggregation, asserted at end
            escaped_exc = exc

        latency_seconds = perf_counter() - started
        latencies.append(latency_seconds)

        run_report: Dict[str, Any] = {
            "run": run_number,
            "latency_seconds": latency_seconds,
        }
        run_violations: List[str] = []

        if escaped_exc is not None:
            exception_occurrences += 1
            run_report["exception_type"] = type(escaped_exc).__name__
            run_report["exception_message"] = str(escaped_exc)
            run_violations.append(
                f"escaped exception: {type(escaped_exc).__name__}: {escaped_exc}"
            )
            run_report["violations"] = run_violations
            per_run.append(run_report)
            continue

        abort_reason = result.get("abort_reason")
        if abort_reason is not None:
            abort_reason_occurrences += 1
            run_report["abort_reason"] = abort_reason
            run_violations.append(f"abort_reason present: {abort_reason}")

        output = result.get("output")
        if not isinstance(output, dict):
            missing_output_occurrences += 1
            run_report["output_missing"] = True
            run_violations.append("missing output object")
            output = {}

        summary_stats = result.get("summary_stats") or {}
        ok_raw = summary_stats.get("ok", 0)
        failed_raw = summary_stats.get("failed", 0)
        ok = ok_raw if isinstance(ok_raw, int) else 0
        failed = failed_raw if isinstance(failed_raw, int) else 0

        if not isinstance(ok_raw, int) or not isinstance(failed_raw, int):
            msg = (
                f"run {run_number}: summary_stats values must be ints "
                f"(ok={ok_raw!r}, failed={failed_raw!r})"
            )
            summary_stats_coherence_violations.append(msg)
            run_violations.append(msg)
        elif ok + failed != TOP_K:
            msg = (
                f"run {run_number}: summary_stats coherence failed "
                f"(ok={ok}, failed={failed}, top_k={TOP_K})"
            )
            summary_stats_coherence_violations.append(msg)
            run_violations.append(msg)

        if ok == 0:
            zero_ok_occurrences += 1
            run_report["summary_ok_violation"] = "summary_stats.ok == 0"
            run_violations.append("summary_stats.ok == 0")

        output_results = output.get("results") or []
        returned_k = output.get("returned_k")
        if not isinstance(returned_k, int):
            msg = (
                f"run {run_number}: returned_k missing/invalid type "
                f"(returned_k={returned_k!r})"
            )
            returned_k_violations.append(msg)
            run_violations.append(msg)
        elif not (1 <= returned_k <= TOP_K):
            msg = (
                f"run {run_number}: returned_k out of range "
                f"(returned_k={returned_k}, expected 1..{TOP_K})"
            )
            returned_k_violations.append(msg)
            run_violations.append(msg)
        elif returned_k >= 2:
            returned_k_ge_2_runs += 1

        empty_in_run = 0
        for item in output_results:
            text = item.get("summary") if isinstance(item, dict) else None
            if not isinstance(text, str) or not text.strip():
                empty_in_run += 1

        empty_summary_occurrences += empty_in_run

        run_report.update(
            {
                "summary_stats": {"ok": ok, "failed": failed},
                "returned_k": returned_k,
                "empty_summaries": empty_in_run,
            }
        )
        run_report["violations"] = run_violations
        per_run.append(run_report)

    min_latency = min(latencies)
    max_latency = max(latencies)
    sorted_latencies = sorted(latencies)
    median_latency = sorted_latencies[len(sorted_latencies) // 2]
    latency_ratio = (
        max_latency / median_latency if median_latency > 0 else float("inf")
    )
    returned_k_ge_2_ratio = returned_k_ge_2_runs / RUNS

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "runs": RUNS,
        "input": FIXED_INPUT,
        "metrics": {
            "abort_reason_occurrences": abort_reason_occurrences,
            "missing_output_occurrences": missing_output_occurrences,
            "empty_summary_occurrences": empty_summary_occurrences,
            "exception_occurrences": exception_occurrences,
            "zero_ok_occurrences": zero_ok_occurrences,
            "summary_stats_coherence_violations": len(summary_stats_coherence_violations),
            "returned_k_violations": len(returned_k_violations),
            "min_latency_seconds": min_latency,
            "median_latency_seconds": median_latency,
            "max_latency_seconds": max_latency,
            "latency_ratio_max_over_median": latency_ratio,
            "returned_k_ge_2_runs": returned_k_ge_2_runs,
            "returned_k_ge_2_ratio": returned_k_ge_2_ratio,
        },
        "per_run": per_run,
    }
    ARTIFACT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    assert abort_reason_occurrences == 0, (
        f"abort_reason detected in {abort_reason_occurrences} run(s); expected 0"
    )
    assert missing_output_occurrences == 0, (
        f"missing output detected in {missing_output_occurrences} run(s); expected 0"
    )
    assert empty_summary_occurrences == 0, (
        f"empty summary detected {empty_summary_occurrences} time(s); expected 0"
    )
    assert exception_occurrences == 0, (
        f"escaped exception detected in {exception_occurrences} run(s); expected 0"
    )
    assert zero_ok_occurrences == 0, (
        f"summary_stats.ok == 0 detected in {zero_ok_occurrences} run(s); expected 0"
    )
    assert not summary_stats_coherence_violations, (
        "summary_stats coherence violations found: "
        + "; ".join(summary_stats_coherence_violations)
    )
    assert not returned_k_violations, (
        "returned_k validation violations found: " + "; ".join(returned_k_violations)
    )
    assert max_latency < 15, (
        f"absolute latency guard failed: max latency {max_latency:.6f}s is >= 15s"
    )
    assert returned_k_ge_2_ratio >= 0.9, (
        "operational degradation guard failed: "
        f"returned_k >= 2 only in {returned_k_ge_2_runs}/{RUNS} runs "
        f"({returned_k_ge_2_ratio:.2%}), expected at least 90%"
    )
    assert latency_ratio < 8, (
        "latency stability guard failed: "
        f"max/median ratio {latency_ratio:.6f} is >= 8 "
        f"(max={max_latency:.6f}s, median={median_latency:.6f}s)"
    )
