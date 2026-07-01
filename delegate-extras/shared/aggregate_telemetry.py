#!/usr/bin/env python3
"""Global delegate telemetry aggregator.

Telemetry is written per-repo to `<repo>/artifacts/<delegate>/events.jsonl` by each
delegate wrapper, plus a `/home/agents/artifacts/<delegate>/` catch-all that collects
events written when a delegate ran from a non-git CWD. This aggregator:

  * discovers every events.jsonl (and rotated .jsonl.1..N) under the search roots,
  * preserves per-repo attribution (top-level `repo`, else meta.repo_root, else the
    path component before `/artifacts/`),
  * dedupes losslessly on the per-event `uuid` when present, falling back to a
    composite key that INCLUDES the token fields (the old per-delegate key excluded
    them and truncated whole-second timestamps, collapsing distinct same-second
    events and corrupting tokens_saved),
  * computes USD cost/savings centrally from token counts + a tunable pricing.json,
    so delegates that emit no USD (kimi) are comparable with those that do (devin).

Read-only: it never writes to the source events files.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

DELEGATES = ("devin-delegate", "kimi-delegate", "grok-delegate")
DEFAULT_ROOTS = (Path("/home/agents/workspace"), Path("/home/agents"))
PRICING_PATH = Path(__file__).resolve().parent / "pricing.json"
CATCHALL_REPO = "_catchall"


def load_pricing(path: Path = PRICING_PATH) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def iter_event_files(roots: Iterable[Path]) -> list[tuple[Path, str]]:
    """Return unique (events_file, delegate) pairs under the given roots."""
    seen: set[Path] = set()
    found: list[tuple[Path, str]] = []
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for delegate in DELEGATES:
            # <root>/<repo>/artifacts/<delegate>/events.jsonl* and
            # <root>/artifacts/<delegate>/events.jsonl* (catch-all)
            for pattern in (
                f"*/artifacts/{delegate}/events.jsonl*",
                f"artifacts/{delegate}/events.jsonl*",
            ):
                for path in root.glob(pattern):
                    if not path.is_file():
                        continue
                    resolved = path.resolve()
                    if resolved in seen:
                        continue
                    seen.add(resolved)
                    found.append((path, delegate))
    return found


def repo_for(path: Path, event: dict[str, Any]) -> str:
    """Best-effort per-repo attribution for one event."""
    repo = event.get("repo")
    if isinstance(repo, str) and repo:
        return repo
    meta = event.get("meta") or {}
    if isinstance(meta, dict):
        rr = meta.get("repo_root")
        if isinstance(rr, str) and rr:
            return Path(rr).name
    # Derive from the file path: the component just before "artifacts".
    parts = path.parts
    if "artifacts" in parts:
        i = parts.index("artifacts")
        if i > 0:
            parent = parts[i - 1]
            # <root>/artifacts/... (no repo dir) is the non-git catch-all.
            if parent in ("agents", "home"):
                return CATCHALL_REPO
            return parent
    return CATCHALL_REPO


def dedup_key(event: dict[str, Any]) -> tuple:
    uid = event.get("uuid")
    if isinstance(uid, str) and uid:
        return ("uuid", uid)
    # Historical events (pre-uuid): composite key that includes the token fields
    # the old key dropped, so distinct same-second events no longer collapse.
    return (
        "composite",
        str(event.get("timestamp", "")),
        str(event.get("event", "")),
        str(event.get("task_class", "")),
        str(event.get("status", "")),
        str(event.get("model_used", "")),
        event.get("latency_ms", ""),
        event.get("estimated_tokens_saved", ""),
        event.get("delegate_input_tokens", ""),
        event.get("delegate_output_tokens", ""),
    )


def _rate(pricing: dict[str, Any], model: str) -> dict[str, float]:
    models = pricing.get("models", {}) or {}
    if model in models:
        return models[model]
    prefixes = pricing.get("prefixes", {}) or {}
    best_key = ""
    for key in prefixes:
        if key.startswith("_"):
            continue
        if model.startswith(key) and len(key) > len(best_key):
            best_key = key
    if best_key:
        return prefixes[best_key]
    return pricing.get("default", {"input_per_mtok": 0.0, "output_per_mtok": 0.0})


def compute_usd(event: dict[str, Any], pricing: dict[str, Any]) -> tuple[float, float]:
    """Return (computed_cost_usd, computed_savings_usd) from tokens + pricing."""
    model = str(event.get("model_used", ""))
    rate = _rate(pricing, model)
    in_tok = int(event.get("delegate_input_tokens", 0) or 0)
    out_tok = int(event.get("delegate_output_tokens", 0) or 0)
    cost = (in_tok * float(rate.get("input_per_mtok", 0.0))
            + out_tok * float(rate.get("output_per_mtok", 0.0))) / 1_000_000.0
    saved = int(event.get("estimated_tokens_saved", 0) or 0)
    parent = pricing.get("parent_model", {}) or {}
    savings = saved * float(parent.get("output_per_mtok", 0.0)) / 1_000_000.0
    return round(cost, 6), round(savings, 6)


def load_events(
    roots: Iterable[Path] | None = None,
    pricing: dict[str, Any] | None = None,
    days: int | None = None,
    delegate: str | None = None,
    repo: str | None = None,
) -> list[dict[str, Any]]:
    roots = list(roots) if roots else list(DEFAULT_ROOTS)
    pricing = pricing if pricing is not None else load_pricing()
    cutoff = None
    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    seen: set[tuple] = set()
    out: list[dict[str, Any]] = []
    for path, delegate_name in iter_event_files(roots):
        if delegate and delegate_name != delegate:
            continue
        try:
            handle = path.open("r", encoding="utf-8", errors="ignore")
        except OSError:
            continue
        with handle:
            for raw in handle:
                line = raw.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                key = dedup_key(event)
                if key in seen:
                    continue
                seen.add(key)

                if cutoff is not None:
                    ts = event.get("timestamp")
                    if isinstance(ts, str):
                        try:
                            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        except ValueError:
                            when = None
                        if when is not None and when < cutoff:
                            continue

                event_repo = repo_for(path, event)
                if repo and event_repo != repo:
                    continue
                cost, savings = compute_usd(event, pricing)
                event["_delegate"] = delegate_name
                event["_repo"] = event_repo
                event["_computed_cost_usd"] = cost
                event["_computed_savings_usd"] = savings
                event["_source"] = str(path)
                out.append(event)
    return out


def summarize(events: list[dict[str, Any]]) -> dict[str, Any]:
    calls = 0
    by_delegate: Counter = Counter()
    by_repo: Counter = Counter()
    by_status: Counter = Counter()
    fallback = 0
    auth_errors = 0
    total_cost = 0.0
    total_savings = 0.0
    total_saved_tokens = 0
    per_repo_cost: dict[str, float] = defaultdict(float)

    for ev in events:
        if ev.get("event") != "delegate_invocation":
            continue
        calls += 1
        by_delegate[ev.get("_delegate", "unknown")] += 1
        by_repo[ev.get("_repo", "unknown")] += 1
        by_status[str(ev.get("status", "unknown"))] += 1
        if ev.get("fallback_used"):
            fallback += 1
        if str(ev.get("fallback_reason", "")) == "auth_error":
            auth_errors += 1
        total_cost += float(ev.get("_computed_cost_usd", 0.0) or 0.0)
        total_savings += float(ev.get("_computed_savings_usd", 0.0) or 0.0)
        total_saved_tokens += int(ev.get("estimated_tokens_saved", 0) or 0)
        per_repo_cost[ev.get("_repo", "unknown")] += float(ev.get("_computed_cost_usd", 0.0) or 0.0)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "delegate_calls": calls,
        "by_delegate": dict(by_delegate),
        "by_repo": dict(by_repo),
        "status": dict(by_status),
        "fallback_rate_pct": round(fallback * 100.0 / calls, 2) if calls else 0.0,
        "auth_errors": auth_errors,
        "estimated_tokens_saved": total_saved_tokens,
        "computed_cost_usd": round(total_cost, 4),
        "computed_savings_usd": round(total_savings, 4),
        "computed_cost_usd_by_repo": {k: round(v, 4) for k, v in sorted(per_repo_cost.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("summary", help="Aggregate + summarize telemetry across all repos")
    s.add_argument("--days", type=int, default=None, help="Only events within the last N days")
    s.add_argument("--delegate", default=None, choices=DELEGATES, help="Filter to one delegate")
    s.add_argument("--repo", default=None, help="Filter to one repo (attribution name)")
    s.add_argument("--roots", nargs="*", default=None, help="Override search roots")
    s.add_argument("--alert", action="store_true", help="Exit non-zero if thresholds exceeded")
    s.add_argument("--fallback-threshold", type=float, default=15.0)
    s.add_argument("--auth-threshold", type=int, default=2)

    args = parser.parse_args()
    roots = [Path(r) for r in args.roots] if args.roots else None

    if args.command == "summary":
        events = load_events(roots=roots, days=args.days, delegate=args.delegate, repo=args.repo)
        data = summarize(events)
        print(json.dumps(data, indent=2))
        if args.alert:
            if data["fallback_rate_pct"] > args.fallback_threshold or data["auth_errors"] > args.auth_threshold:
                import sys
                sys.stderr.write(
                    f"ALERT: fallback_rate={data['fallback_rate_pct']}% "
                    f"(threshold={args.fallback_threshold}%), auth_errors={data['auth_errors']} "
                    f"(threshold={args.auth_threshold})\n"
                )
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
