"""Tests for the global delegate telemetry aggregator."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import aggregate_telemetry as agg  # noqa: E402


def _write(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for ev in events:
            fh.write(json.dumps(ev) + "\n")


def _inv(**kw) -> dict:
    base = {
        "event": "delegate_invocation",
        "status": "ok",
        "task_class": "review",
        "model_used": "pi-kimi-subagent:default",
        "delegate_input_tokens": 100,
        "delegate_output_tokens": 200,
        "estimated_tokens_saved": 500,
        "latency_ms": 1234.5,
        "timestamp": "2026-06-01T00:00:00+00:00",
    }
    base.update(kw)
    return base


def test_iter_event_files_discovers_repo_and_catchall(tmp_path: Path):
    _write(tmp_path / "repoA" / "artifacts" / "kimi-delegate" / "events.jsonl", [_inv()])
    _write(tmp_path / "artifacts" / "devin-delegate" / "events.jsonl", [_inv()])
    _write(tmp_path / "repoB" / "artifacts" / "devin-delegate" / "events.jsonl.1", [_inv()])
    found = agg.iter_event_files([tmp_path])
    delegates = sorted(d for _, d in found)
    assert delegates == ["devin-delegate", "devin-delegate", "kimi-delegate"]
    assert len(found) == 3  # includes the rotated .jsonl.1


def test_repo_attribution_precedence(tmp_path: Path):
    p = tmp_path / "repoX" / "artifacts" / "kimi-delegate" / "events.jsonl"
    # top-level repo wins
    assert agg.repo_for(p, {"repo": "explicit"}) == "explicit"
    # else meta.repo_root basename
    assert agg.repo_for(p, {"meta": {"repo_root": "/home/agents/workspace/frommeta"}}) == "frommeta"
    # else path-derived (component before "artifacts")
    assert agg.repo_for(p, {}) == "repoX"
    # non-git catch-all path -> _catchall
    cat = tmp_path / "artifacts" / "kimi-delegate" / "events.jsonl"
    assert agg.repo_for(Path("/home/agents/artifacts/kimi-delegate/events.jsonl"), {}) == agg.CATCHALL_REPO


def test_dedup_by_uuid_collapses(tmp_path: Path):
    ev = _inv(uuid="abc123")
    _write(tmp_path / "r1" / "artifacts" / "kimi-delegate" / "events.jsonl", [ev])
    # same uuid recorded in the catch-all (the split-write problem) must not double count
    _write(tmp_path / "artifacts" / "kimi-delegate" / "events.jsonl", [dict(ev)])
    events = agg.load_events(roots=[tmp_path])
    assert len(events) == 1


def test_composite_key_does_not_collapse_distinct_token_events(tmp_path: Path):
    # Two same-second, same-class events that differ ONLY in token counts.
    # The old lossy key excluded tokens and would collapse these; the fix keeps both.
    a = _inv(delegate_input_tokens=100, delegate_output_tokens=200)
    b = _inv(delegate_input_tokens=999, delegate_output_tokens=888)
    _write(tmp_path / "r1" / "artifacts" / "kimi-delegate" / "events.jsonl", [a, b])
    events = agg.load_events(roots=[tmp_path])
    assert len(events) == 2


def test_identical_historical_events_still_collapse(tmp_path: Path):
    a = _inv()
    _write(tmp_path / "r1" / "artifacts" / "kimi-delegate" / "events.jsonl", [a, dict(a)])
    events = agg.load_events(roots=[tmp_path])
    assert len(events) == 1


def test_compute_usd_for_kimi_without_recorded_cost(tmp_path: Path):
    pricing = agg.load_pricing()
    cost, savings = agg.compute_usd(_inv(), pricing)
    assert cost > 0  # kimi emits no USD; aggregator computes it
    assert savings > 0


def test_rate_prefix_and_default_matching():
    pricing = {
        "models": {"devin:devin-default": {"input_per_mtok": 5.0, "output_per_mtok": 15.0}},
        "prefixes": {"fallback:codex": {"input_per_mtok": 1.25, "output_per_mtok": 10.0}},
        "default": {"input_per_mtok": 2.0, "output_per_mtok": 10.0},
    }
    assert agg._rate(pricing, "devin:devin-default")["input_per_mtok"] == 5.0
    assert agg._rate(pricing, "fallback:codex:default")["input_per_mtok"] == 1.25
    assert agg._rate(pricing, "totally-unknown")["input_per_mtok"] == 2.0


def test_summary_attributes_per_repo_and_totals(tmp_path: Path):
    _write(tmp_path / "repoA" / "artifacts" / "kimi-delegate" / "events.jsonl",
           [_inv(uuid="a1"), _inv(uuid="a2", status="error", fallback_used=True, fallback_reason="auth_error")])
    _write(tmp_path / "repoB" / "artifacts" / "devin-delegate" / "events.jsonl",
           [_inv(uuid="b1", model_used="devin:devin-default")])
    events = agg.load_events(roots=[tmp_path])
    data = agg.summarize(events)
    assert data["delegate_calls"] == 3
    assert data["by_repo"]["repoA"] == 2
    assert data["by_repo"]["repoB"] == 1
    assert data["by_delegate"]["kimi-delegate"] == 2
    assert data["auth_errors"] == 1
    assert data["computed_cost_usd"] > 0
    assert set(data["computed_cost_usd_by_repo"]) == {"repoA", "repoB"}


def test_days_filter_excludes_old(tmp_path: Path):
    _write(tmp_path / "r1" / "artifacts" / "kimi-delegate" / "events.jsonl",
           [_inv(uuid="old", timestamp="2020-01-01T00:00:00+00:00"),
            _inv(uuid="recent", timestamp="2026-06-30T00:00:00+00:00")])
    both = agg.load_events(roots=[tmp_path], days=None)  # no window -> both
    assert len(both) == 2
    only_new = agg.load_events(roots=[tmp_path], days=30)
    assert all(e.get("uuid") != "old" for e in only_new)
