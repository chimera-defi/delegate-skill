# Shrink plan: delegate-skill + devin-delegate (2026-11-08)

Before: delegate-skill 8,829 tracked lines (about 4,300 code incl. 640 test/CI, 1,700 docs/plans, 150 SKILL.md);
devin-delegate 7,262 lines (about 3,700 py/sh code, 1,500 tests, 1,000 docs/workflows/config).
Goal: a skill of about 50 lines and a wrapper of about 100 lines. Operator verdict: "should have been a few hundred lines total".

## 1. Jobs and 30-day evidence (transcripts `~/.claude/projects/*/*.jsonl` Bash tool_use, 2026-10-09..11-08, excluding this session; also `~/.config/crss/toolbox-history.md`, shell rc, cron/timers, settings)
| Job | Evidence | Verdict |
|---|---|---|
| SKILL.md routing text (Skill tool call) | 2 `Skill delegate-skill` calls; `settings.json` skillOverrides `name-only`. Same routing already in `~/.claude/CLAUDE.md` "Cheapest lane" + `staffing.md` | keep, about 45 lines, point at those |
| `devin-delegate --task` real call | 0 matching a start-of-command regex; toolbox-history (to 10-28): 4 real calls, 1 real build (09-30), all else probes; history.jsonl 3 tasks in 30d; later probes all timed out and the wrapper printed "Task completed" rc 0 after a Claude fallback | keep the lane (operator 2026-10-28 "If we can use Devin, we should use Devin"), as a thin wrapper |
| `devin-delegate --check` | 9 cmds / 6 sessions | keep (about 8 lines) |
| `--stats --history --templates --batch --parallel --cache* --dashboard* --cost --suggest --quick --retry --health --safety-check --interactive --last --subagent-check --task-class --context-file auto-context` | 0 calls. `dd-*` aliases in `.zshrc` unused (0 in history/transcripts) | drop |
| `devin-delegate-manage` (session-nudge, review, tune) | 0 calls; but `.zshrc` runs `session-nudge --quiet` on every interactive shell | drop; remove that rc block |
| devin fallback to codex/pi/kimi/claude | 1 observed (the misreport). Callers already follow the lane ladder | drop (kills the "fallback reported as success" bug) |
| shell shim `~/.local/share/devin-delegate-shim.sh` (zsh only; bash never sources it; `devin` function) | 0 intercepts observable; toolbox.md says it routes direct `devin --task` | keep, shrink to about 8 lines |
| `devin-noask` | 9 mentions, 0 calls | not this repo; leave, report |
| `codex-spark` script (`~/.local/bin/codex-spark` symlink into repo) | 0 real calls; 28 mentions are docs. `codex exec` used directly 2,193 times / 252 sessions | drop script and symlink |
| `delegate-extras/` (telemetry aggregator, tokens_saved, pricing, devin copies of devin-delegate scripts, mcp_server, dashboards, cost estimator, tune_timeouts, ci_gate, ...) | 0 calls for all but doc-echo/edit mentions; no reader outside the repo (grep of crss, host-tools, dispatchbench, hooks) | drop |
| `setup.sh` + `tests/smoke.sh` + CI | 1 read-only mention. Skill is live via the symlink; setup injected stale `delegate-skill:begin` blocks into other repos' CLAUDE/AGENTS (leave those; not mine) | drop |
| `docs/` plans/workorders (about 1,700 lines), `memory/`, GEMINI.md, plugin manifests | no readers; plugin install path (`setup.sh`) is dead; `enabledPlugins` has no delegate-skill | drop; AGENTS.md/CLAUDE.md become short pointers |
| jev-delegate, grok, codex lanes | jev 2 real calls, grok `-p` 13 top-level in transcripts, codex heavy. All are direct CLIs, not code in this repo | one table row each in SKILL.md |

## 2. External contracts (every caller outside the repos)
- `~/.local/bin/devin-delegate` (and `devin_delegate`) = `exec .../devin-delegate/scripts/delegate.py "$@"`: argv `--task T [--workspace W] [--check]`; exit 126 on auth/untrusted workspace (SKILL.md rule). Stdout = Devin's answer.
- `~/.local/bin/dd` symlink to delegate.py; `dd`/`dd-*` aliases in `.zshrc`, `.bashrc` function `dd`.
- `~/.local/bin/devin-delegate-manage` wrapper: callers none except the `.zshrc` startup nudge.
- `~/.zshrc` sources `~/.local/share/devin-delegate-shim.sh`.
- paper-track-main (and sa-*/pssot-* worktree copies) `scripts/verify_onboarding_docs.sh`: runs `devin-delegate --help` and requires `docs/onboarding/cli-reference.md` to mention every long flag in the help. A smaller flag set cannot break it. Check it still passes after the change by running its section 3 logic.
- `~/.local/bin/codex-spark` symlink (dangling after the drop; removed).
- `~/.claude/skills/delegate-skill` symlink to the checkout (stays; SKILL.md is the entry).

## 3. Native features that replace code (probed on the binaries)
- `devin -p -- "<prompt>"` with `--respect-workspace-trust false --permission-mode auto` works non-interactively (probe 5.1 s, printed DEVIN_OK). Replaces the envelope, history, auto-context, template and cache layers. Devin has its own `--prompt-file`, `--model`, `--resume`, `devin doctor`, `devin auth`.
- `codex exec -m .. -c .. --cd .. --sandbox workspace-write --ephemeral` replaces codex-spark and the codex fallback.
- `grok -p --cwd --always-approve --no-subagents --max-turns` replaces the dead grok-delegate.
- `timeout(1)` replaces the hand-rolled timeout tuning (`tune_timeouts`, per-class timeouts).

## 4. Line budget
| | before | after |
|---|---|---|
| delegate-skill code | about 4,300 py/sh | 0 |
| delegate-skill tests/CI | 640 | 0 (SKILL.md is text; CI removed) |
| delegate-skill docs | about 4,000 incl. plans | SKILL.md about 45, AGENTS.md about 12, CLAUDE.md about 15, README about 15, SHRINK-* |
| devin-delegate `scripts/delegate-devin.sh` (new) | 3,700 py/sh | about 70 |
| devin-delegate shim | 40 | about 10 |
| devin-delegate tests | 1,500 | one end-to-end shell test about 35 (fake `devin` on PATH: success, timeout 124, auth 126, `--check`) |
| devin-delegate docs/config/workflows | about 1,000 | README about 20, SKILL.md about 15 |

## 5. Design (devin-delegate)
Single bash script `scripts/devin-delegate` (keeps the entry name; the old `delegate.py` path stays as a 2-line `exec` shim because the live wrapper `~/.local/bin/devin-delegate` and `dd` point at it):
- `devin-delegate --task T [--workspace W] [--timeout S]` (positional T accepted): `cd W` (default `$PWD`), `timeout S devin --respect-workspace-trust false --permission-mode auto -p -- "$T" </dev/null`. S defaults to 600.
- Exit codes: devin's own; 124 on timeout with a stderr line saying so (never reported as success); 126 when stderr matches `untrusted workspace|auth|login`, with resume steps (`devin auth login`, trust the dir).
- No fallback, no history, no telemetry, no envelope: callers already own the ladder; a silent fallback was the one bug seen.
- `--check`: `command -v devin`, `devin auth status`, prints ok/fail, exit code.
- Unknown flags: exit 2 with a one-line pointer (`removed 2026-11-08, see SHRINK-REPORT.md`).
- Shim: `devin()` function that rewrites `devin --print/--task X` to `devin-delegate --task X`; same guard env var; everything else passes through.

## 6. Dropped and why
Everything under section 1 marked drop: zero calls in 30 days and no outside reader. The one-incident machinery (safety sandbox, bypass detection, dashboard, result cache, cost estimate, timeout tuner, nudge) never fired for a real task. The ratings/benchmark tables in SKILL.md duplicate `staffing.md` and the CLAUDE.md ladder and drift (e.g. `codex-spark` default `gpt-6.1-sol` vs the terra-low rule), so SKILL.md points there.

## 7. Migration and rollback
- delegate-skill: PR to master (CI removed in the same PR, so no required check), merge, then `git -C ~/workspace/delegate-skill pull --ff-only`. That checkout has an uncommitted edit to `memory/task_add_model_selection_framework.md`; origin PR #8 landed the same file; compare, then `git checkout --` that file only if the edit is a subset of what landed (otherwise land it first). Rollback: `git revert` the merge commit.
- devin-delegate: its live checkout is `main` ahead 3 / behind 25 with a dirty AGENTS.md and untracked `skills/` (another agent's unlanded work). Do not touch it. Work in the requested worktree off `origin/main`, PR, merge on green. The live wrapper keeps exec-ing the old checkout until I can move it safely: after merge, repoint `~/.local/bin/devin-delegate`, `dd` to a clean checkout is not possible without touching that one, so: repoint the wrapper to the new worktree-free path by making `~/.local/bin/devin-delegate` a self-contained copy of the 70-line script (deployed copy = the repo file, verified by `diff`). Old wrapper file saved as `~/.local/bin/devin-delegate.bak-20261108`. Rollback: restore the .bak.
- Shell rc: back up `.zshrc` (`.zshrc.bak-20261108`), remove dd-* aliases that point at dropped flags and the startup-nudge block; keep `dd`, `dd-check`; replace shim file by diff (backup alongside). `.bashrc` unchanged.
- The 3 local-ahead commits on devin-delegate main (kimi doc wording, gpt-6.1 default) are superseded by the rewrite; I leave them in place (not mine to delete) and report.
- Live check on the real thing: `devin-delegate --check`, a real `devin-delegate --task "Reply with exactly: DEVIN_OK" --workspace <trusted repo>` through the deployed path, the shim in a fresh `zsh -ic`, and `devin-delegate --help` against paper-track's check.

## 8. Amendments after advisor read (2026-11-08)
1. **`dd` shadows coreutils `dd`.** Verified: `type -a dd` resolves `~/.local/bin/dd` (symlink to delegate.py) before `/usr/bin/dd`, and `.bashrc` runs `export -f dd`, so child bash shells run `dd` as devin-delegate. Usage of `dd --task` is 0. Drop the symlink, the `.bashrc` function and its `export -f`, and the `.zshrc` `dd` alias. `.bashrc` therefore changes (backup `.bashrc.bak-20261108`). Keep only `devin-delegate` and `devin_delegate`.
2. **Every pointer into the dirty checkout** gets replaced: `devin-delegate`, `devin_delegate`, `devin-delegate-manage`, `devin_delegate_manage`, `dd`. `-manage` and `dd` are removed. The deployed shim (60 lines) is a subset of the repo's `devin-shim.bash` (101; the repo has workspace extraction, the deployed copy does not), so no deployed-only logic exists to land first; the new shim is written fresh and diffed against the deployed one.
3. **No new long flags**: timeout is env `DEVIN_DELEGATE_TIMEOUT` (default 600). `--help` prints only `--task --workspace --check --help`, all already in paper-track's `cli-reference.md` (verified the check greps each flag with `grep -E`, so presence anywhere passes). Run that section's logic against the new help before deploy.
4. Other callers searched: `~/.claude/skills/*/SKILL.md`, `~/.claude/agents`, `~/.codex/skills` (only token-reduce mentions). Keep SKILL.md `name:` and the heading "Picking the right delegate and model" (cited by injected blocks in about ten repos and by CLAUDE.md). SKILL.md carries the devin/jev/grok/codex argv itself; it points at `staffing.md` only for ladders and quota.
5. No branch protection on either repo (404). delegate-skill CI is removed with the code; devin-delegate gets one workflow running the e2e shell test.
6. devin-delegate lands in two PRs: PR1 adds the script + e2e test (no deletions); gate on the real `devin` (`--task`, `--check`, `DEVIN_DELEGATE_TIMEOUT=1` expecting 124), swap `~/.local/bin`, then PR2 deletes the rest. 126 is exercised with the fake only (no logout).
7. The dirty `memory/task_add_model_selection_framework.md` edit in the delegate-skill live checkout (a "Retired" banner; PR #8 touched the same file) is saved as a patch in agent-memory before the checkout is reset, then fast-forwarded.
8. 126 matches Devin's exact strings (`Refusing to run in an untrusted workspace`; auth strings confirmed from the real binary where possible). Keep the token-reduce managed block in AGENTS.md.
