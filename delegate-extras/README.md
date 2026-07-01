# delegate-extras

"Extra" tooling for the devin and kimi delegates, moved **out** of their
individual delegate repos to keep each delegate small, and the shared telemetry
aggregator used across all delegates.

- `devin/` — devin-delegate extras (dashboards, audits, ci_gate, MCP server,
  parallel batch, safety sandbox, tuning, review/summarize, etc.).
- `kimi/` — kimi-delegate extras (dashboard, audits, ci_gate, interactive mode,
  session nudge, tuning, etc.).
- `shared/` — cross-repo telemetry aggregator (`aggregate_telemetry.py`,
  `pricing.json`, `tests/`). USD-costed, scans all delegate repos.

## Install-path contract

The delegate repos' rewired call sites (`manage.sh`, `delegate.py`) resolve
these scripts from a **stable install path**:

```
~/.claude/skills/delegate-skill/delegate-extras/<d>/
```

Resolution used by every rewired call site (overridable for testing):

```sh
EXTRAS=${DELEGATE_EXTRAS_DIR:-$HOME/.claude/skills/delegate-skill/delegate-extras/<d>}
```

## Graceful degradation

The extras path is **not** on the core `--task` path. When it is absent:

- `manage.sh` subcommands guard `[ -x "$EXTRAS/<file>" ]` and print an install
  hint pointing at the router skill instead of failing.
- `delegate.py` extras imports are wrapped in `try/except` and fall through to
  existing fallbacks.
- Dashboards and `ci_gate` skip the telemetry section (empty summary) rather
  than crashing when `shared/` is unavailable.

## Canonical `tokens_saved` helper

`shared/tokens_saved.py` is the authoritative reference for computing
`estimated_tokens_saved` across all delegate wrappers.  See
`docs/workorder_standardize_tokens_saved_formula_20260701.md` for the full
work-order.

**Formula (K = 3, ratified 2026-07-01):**

```
parent_tokens = envelope.metrics.parent_context_tokens  (falls back to delegate_input_tokens when absent/zero)
estimated_tokens_saved = max(0, parent_tokens * 3 - delegate_output_tokens)
```

The K=3 multiplier reflects that a parent re-reading and reasoning over its
context consumes roughly 3× the tokens a delegate needs for the same work.

**Vendored copies — core path independence:**  Every wrapper (`devin-delegate`,
`kimi-delegate`, `grok-delegate`) maintains a byte-identical copy at
`scripts/tokens_saved.py`.  The core `--task` path in each wrapper must import
from its local `scripts/tokens_saved.py` and must NOT depend on the index repo
being installed.  The canonical home here (`shared/tokens_saved.py`) is the
documentation/reference source; `scripts/` copies are the runtime source.

**Drift prevention:**  `shared/tests/test_tokens_saved.py` (11 pinned tests) is
also vendored byte-identical into each wrapper's test suite.  CI in each wrapper
runs these tests against the local `scripts/` copy; any divergence from the
canonical formula fails that repo's CI immediately.

**Forward-only policy:**  This standardization changes how *new* telemetry events
compute `estimated_tokens_saved`; historical `events.jsonl` records are never
rewritten.  Each delegate's `tokens_saved` series will show a one-time step at
the cutover date — this is expected and intended, not a data error.

## Telemetry wiring

- `devin/ci_gate.py` reads cross-repo, USD-costed telemetry via the co-located
  `shared/aggregate_telemetry.py` (`load_events(delegate="devin-delegate")` →
  `summarize`), degrading to a zero-count summary if `shared/` is missing.
- The dashboards (`devin/telemetry_dashboard.py`, `kimi/generate_dashboard.py`)
  keep their **rich per-delegate** analytics via bundled sibling telemetry
  modules (`devin_delegate_telemetry.py`, `kimi_delegate_telemetry.py`), which
  expose fields the thinner shared aggregator does not (fallback reasons, error
  categories, repo-scale distribution, average latency, savings percent).

## Self-contained bundling

Because these scripts no longer live beside the core delegate modules, a few
small dependencies are bundled here as siblings so each script runs without an
ImportError when invoked with a delegate-repo cwd:

- `repo_scan.py`, `detect_bypass.py`, and the per-delegate telemetry modules are
  copied in (imported via a `try / sys.path.append(__file__ dir)` fallback).
- `devin/delegate_shim.py` provides `run_delegate` / `current_repo_root` /
  `load_json` by shelling out to the installed `devin-delegate` wrapper binary,
  so `mcp_server.py` and `parallel_batch.py` never import the ~70KB core
  `delegate.py`. The wrapper is resolved via `$DEVIN_DELEGATE_BIN` →
  `PATH` → `~/.local/bin/devin-delegate`.
