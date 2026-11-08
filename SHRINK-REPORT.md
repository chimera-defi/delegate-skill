# Shrink report: delegate-skill + devin-delegate (2026-11-08)

Plan: `SHRINK-PLAN.md` (read by an Opus-class advisor before any code; its 8 amendments are section 8 of the plan).

## Lines (tracked files)
| | before | after |
|---|---|---|
| delegate-skill code (py/sh) incl. codex-spark | 6,417 (of which tests/CI smoke 290) | 0 |
| delegate-skill docs/plans/memory/manifests | about 2,400 | 209 total (SKILL.md 45, AGENTS 12, CLAUDE 3, README 3, commit hook 52) plus plan and report |
| devin-delegate code | 3,758 | 29 (`scripts/devin-delegate`) |
| devin-delegate tests | 3,004 | 21 (`tests/e2e.sh`, fake devin: success/argv/cwd, 124, 126, --check, removed flag) |
| devin-delegate docs/config/workflows | 1,103 md plus config and 3 workflows | README 8, SKILL 8, AGENTS, one 10-line e2e workflow |
| totals | 8,829 + 7,262 | about 210 + 164 |

## Dropped (zero calls in 30 days, no reader outside the repos)
delegate-extras (telemetry aggregator, tokens_saved, pricing, dashboards, cost estimator, mcp_server, safety sandbox, result cache, parallel batch, timeout tuner, ci_gate, workspace auditors); setup.sh and its smoke test and CI; plugin manifests; planning docs; `codex-spark` script and `~/.local/bin/codex-spark` symlink target (dangling; left for the launcher, see undone); devin-delegate fallback engines, history, auto-context, envelope, templates, cache, batch, stats, manage CLI, MCP server, scheduled workflows.

## Kept and why
SKILL.md (name and the heading "Picking the right delegate and model" kept: cited by other repos' injected blocks and global CLAUDE.md), now carrying the actual codex/devin/grok/jev argv. `devin-delegate --task/--workspace/--check` (operator 2026-10-28: use Devin). Shim (8 lines). `.githooks/commit-msg`. The token-reduce block in AGENTS.md (owned by another tool).

## Live changes (backups in `~/.local/share/devin-bak-20261108/`)
- `~/.local/bin/devin-delegate` replaced by a copy of the repo script (verified `diff` equal to origin/main); `devin_delegate` symlink follows. Removed `dd` symlink, `devin-delegate-manage`, `devin_delegate_manage`.
- `~/.zshrc`: removed dd-* aliases and the startup session-nudge block. `~/.bashrc`: removed `alias dd`, `dd()` and `export -f dd` (it shadowed coreutils `dd`; `type -a dd` now resolves `/usr/bin/dd`).
- `~/.local/share/devin-delegate-shim.sh` rewritten (deployed copy was a subset of the repo's 101-line shim, no deployed-only logic).
- Live checks on the real thing: `devin-delegate --check` (Logged in), real task via the deployed path returned DEVIN_OK (rc 0), `DEVIN_DELEGATE_TIMEOUT=1` gave rc 124, shim in a bash shell routed `devin --print` and answered SHIM_OK, paper-track's `--help` flag-coverage logic: all 4 flags covered. 126 was exercised with the fake only (no logout).

## Decided
- Thin wrapper, no fallback (it removes the "fallback reported as success" bug; the ladder is the caller's).
- Timeout as env, not a flag (no new `--help` flag for paper-track's check).
- Two devin-delegate PRs (#51 add, #52 delete) with a live swap between; delegate-skill one PR (no CI left; neither repo has branch protection).
- Wrote the 29-line script myself instead of briefing a builder.
- Left the other repos' stale `delegate-skill:begin` blocks alone (not mine).

## Undone / for the operator or launcher
- `~/workspace/devin-delegate` live checkout is `main` ahead 3 / behind 26 with a dirty AGENTS.md and untracked `skills/` (another agent's unlanded work); untouched. Nothing live runs from it any more. Its 3 local commits (kimi doc wording, gpt-6.1 defaults) are superseded by the rewrite.
- `~/.local/bin/codex-spark` and `devin-noask` (0 calls) are dangling or unused; removal not done (codex-spark symlink points into the live skill dir, so removed in the ff step below if the file is gone).
- No zsh on this host: the new zshrc/shim could only be tested in bash.
- Fast-forward of `~/workspace/delegate-skill` after PR merge: see the final receipt below.
