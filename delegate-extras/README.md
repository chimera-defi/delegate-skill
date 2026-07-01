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
