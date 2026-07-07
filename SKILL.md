---
name: delegate-skill
preamble-tier: 4
version: 1.1.0
description: "Route bounded tasks to the right AI delegate: devin (browser/sandbox), kimi (cheap research/review), grok (large codebase), spark (local Codex write-mode)."
triggers:
  - which delegate should I use
  - delegate this task
  - use a subagent for this
  - route to an AI agent
  - should I use devin
  - should I use kimi
  - should I use grok
  - use a delegate
  - delegate to an agent
  - what delegate
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---

# Delegate Skill Router

Route bounded tasks to the fastest, cheapest AI for the job. Never call delegates
directly — always use the wrapper binaries (envelope, fallback, telemetry).

## Routing table

`devin-delegate` is the general implement/review workhorse; browser/sandbox is one of its
capabilities, not a separate delegate. `kimi-delegate` is for cheap, small, read-only tasks.
`grok-delegate` is **dormant** (see below).

| Task type | Delegate | Command |
|-----------|----------|---------|
| General implementation / review / debug (workhorse) | `devin-delegate` | `devin-delegate --task "..." --workspace /path` |
| Browser, UI, screenshot, sandbox (a devin capability) | `devin-delegate` | `devin-delegate --task "..." --workspace /path` |
| Cheap **small read-only**: search / summarize / draft / review small diffs | `kimi-delegate` | `kimi-delegate --task "..."` |
| Local Codex write-mode implementation | `spark` | `/spark` |
| Multi-file refactor on a very large codebase (DORMANT) | `grok-delegate` | `grok-delegate --task "..."` |
| Unknown scope / orchestration | `devin-delegate` (workhorse); if clearly cheap+small, `kimi-delegate` | `devin-delegate --task "scope: ..."` |

**grok is dormant, not deprecated.** It has one lifetime call (an auth error, i.e. broken
auth — not lack of demand). Revival gate: ≥5 successful calls **and** a documented devin
failure on a large repo. Until then, route large-codebase work to `devin-delegate` and only
reach for grok when devin demonstrably can't hold the context.

## Picking the right delegate and model

### Ratings

Higher = better. **Cost** = cheap/rate-limit-friendly (inverse of price). **Intelligence** = how hard a problem you can hand it unsupervised. **Taste** = output quality, code aesthetics, API design, copy. **Availability** = how reliably it's reachable without auth errors or quota issues.

**External delegates**

| delegate | cost | intelligence | taste | availability | notes |
|----------|------|--------------|-------|--------------|-------|
| devin | 4 | 8 | 6 | 6 | Auth-sensitive (exit 126 = re-auth required). Browser/sandbox built in. |
| kimi | 9 | 4 | 4 | 7 | Read-only, light auth. Fast for cheap parallel research. |
| grok | 5 | 7 | 5 | 0 | **Dormant** — revival gate not met. Do not route here. |
| spark/codex | 8 | 6 | 5 | 9 | Local, always-on. Ground-floor fallback for implementation. |

**Claude models** (for `model:` parameter in Agent tool / Workflow calls)

| model | cost | intelligence | taste |
|-------|------|--------------|-------|
| claude-haiku-4-5 | 9 | 4 | 4 |
| claude-sonnet-4-6 | 6 | 7 | 7 |
| claude-opus-4-7 | 3 | 9 | 8 |

### How to apply

- **Defaults, not ceilings.** You have standing permission to escalate: if a cheaper delegate's output doesn't meet the bar, retry or redo with a smarter one without asking. Judge the output, not the price tag. Escalating costs less than shipping mediocre work.
- **Availability overrides preference.** If the preferred delegate is down (auth error / exit 126), fall back immediately — don't wait for the user. Fallback chain: devin → spark → direct Claude (sonnet). For research: kimi → direct Claude.
- **Cost is a tie-breaker only.** When axes conflict for anything that ships: intelligence > taste > cost.
- **Bulk/mechanical work** (clear-spec implementation, data transformation, migrations): spark/codex — cheap, fast, local, always available.
- **Anything user-facing** (UI, copy, API design) needs taste ≥ 7: use devin or claude-sonnet-4-6 / claude-opus-4-7. Never kimi or claude-haiku-4-5 for shipped output.
- **Reviews and adversarial critique**: claude-opus-4-7 or `/gstack-claude challenge`. Optionally add spark/codex as an independent second opinion.
- **Research / summarize / small diffs**: kimi first (cheapest) → spark if kimi is unavailable.
- **Never use claude-haiku-4-5 for anything that ships.** Reserve it for pure triage/classification steps inside larger workflows.
- **Claude models only in Agent tool calls.** The `model:` parameter does not accept external delegates. For mechanical steps needing a non-Claude model, spawn a thin Sonnet wrapper whose prompt is to write a self-contained codex prompt and run `codex exec` via Bash.
- **Never bypass wrappers.** Raw calls skip envelope, fallback, and telemetry — always use `devin-delegate`, `kimi-delegate`, `grok-delegate` binaries.

## Rules

- **Never bypass wrappers.** Raw calls (`opencode`, `devin`, `pi --provider kimi-coding`) skip
  envelope injection, fallback, and telemetry. Always use the binary wrappers.
- **Always scope the task.** Include: goal, constraints, acceptance checks, expected output format.
- **Auth errors → exit 126.** Do not auto-retry. Print resume steps for the user (below).

## Fallback, auth, and latency

- **Fallback = codex/spark.** When a delegate's primary engine fails or returns an invalid
  schema, the wrapper falls back to `codex exec` with **no `--model`** pinned, so codex uses
  the user's Codex config default (same engine `/spark` uses). Configs set `fallback_model:
  null`; a real model name is only passed through when explicitly configured.
- **Auth failure → exit 126, no auto-retry.** The wrapper short-circuits *before* the fallback
  engine and prints resume steps. Typical fixes: `opencode` (grok, xAI SIWE) → run
  `opencode` then `/connect`; kimi/devin provider auth → re-run the provider login. Re-run the
  task after connecting.
- **Latency is long by design.** Delegate calls can run for minutes (observed tail past 500s on
  large repos). This is expected — the wrapper emits progress to stderr. Don't kill a call that
  is still streaming progress; budget for it or scope the task smaller.

## With Superpowers

`superpowers:subagent-driven-development` dispatches fresh subagents per task. Those
subagents can and should use delegate skills for bounded work within larger tasks:

- Implementation step that needs a browser → `devin-delegate`
- Review or research step → `kimi-delegate` (cheaper than a full subagent)
- Implementation step on a large codebase → `grok-delegate`

Delegates keep subagent context small: only the result summary enters the parent context,
not the full implementation.

## With GStack

GStack includes `/spark` (Codex write-mode) as a built-in. `delegate-skill` adds:

- `devin-delegate` — when spark needs a real browser, shell, or debugging sandbox
- `kimi-delegate` — when you want cheap parallel research without burning spark's context
- `grok-delegate` — when the codebase is too large for spark's context window

Install both GStack and `delegate-skill` to get the full execution layer.

## Health check

```bash
devin-delegate --check
kimi-delegate --check
grok-delegate --check
```

## Install / update

```bash
bash ~/.agents/skills/delegate-skill/setup.sh
```
