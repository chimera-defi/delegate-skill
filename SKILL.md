---
name: delegate-skill
preamble-tier: 4
version: 1.1.0
description: "Route bounded tasks to Spark/Codex for local mechanical work and Devin for general implementation, review, browser, and sandbox work, with safe fallbacks."
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

Spark/Codex is preferred for local mechanical implementation; `devin-delegate` is the
general implement/review workhorse, with browser/sandbox as one of its capabilities.
Kimi is optional compatibility for cheap read-only work and is never the default route.
`grok-delegate` is **dormant** (see below).

| Task type | Delegate | Command |
|-----------|----------|---------|
| General implementation / review / debug (workhorse) | `devin-delegate` | `devin-delegate --task "..." --workspace /path` |
| Browser, UI, screenshot, sandbox (a devin capability) | `devin-delegate` | `devin-delegate --task "..." --workspace /path` |
| Local mechanical implementation / transformation / migration | `spark` / Codex Spark | `/spark` or the configured Codex Spark worker |
| Cheap **small read-only** search / summarize / draft / review | Spark/Codex bounded subagent | scoped read-only subagent call |
| Multi-file refactor on a very large codebase (DORMANT) | `grok-delegate` | `grok-delegate --task "..."` |
| Unknown scope / orchestration | `devin-delegate` (workhorse) | `devin-delegate --task "scope: ..."` |

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
| devin | 4 | 8 | 2 | 6 | Auth-sensitive (exit 126 = re-auth required). Browser/sandbox built in. Raw output needs human review before shipping. |
| kimi | 9 | 4 | 4 | 7 | Read-only, light auth. Fast for cheap parallel research. |
| grok | 5 | 7 | 5 | 0 | **Dormant** — revival gate not met. Do not route here. |
| spark/codex | 8 | 6 | 5 | 9 | Local, always-on. Ground-floor fallback for implementation. |

**Claude models** (for the `model:` parameter in Agent tool / Workflow calls — it takes the
bare aliases below, not full ids; each alias tracks the latest release for its tier)

| `model:` | resolves to (2026-10-23) | cost | intelligence | taste | `advisor` tool |
|----------|--------------------------|------|--------------|-------|----------------|
| `haiku` | claude-haiku-5-5 | 9 | 6 | 4 | — |
| `sonnet` | claude-sonnet-5-5 | 6 | 7 | 7 | yes |
| `opus` | claude-opus-5-5 | 3 | 9 | 8 | yes (CLI ≥ 2.1.300) |

`advisor` is gated on the agent's own model and the CLI: before CLI 2.1.300 a subagent on
Opus 5.x had no `advisor` tool, silently. For implementation subagents that should be able
to ask for a second opinion, `sonnet` (or `subagent_type: builder`, pinned to it) works on
any recent CLI.

### How to apply

- **Defaults, not ceilings.** You have standing permission to escalate: if a cheaper delegate's output doesn't meet the bar, retry or redo with a smarter one without asking. Judge the output, not the price tag. Escalating costs less than shipping mediocre work.
- **Availability overrides preference.** If a preferred route is unavailable, fall back immediately — don't wait for the user. Mechanical fallback: spark → devin → direct parent. General/browser/review fallback: devin → spark → direct parent. Read-only fallback: spark/Codex → direct parent; use Kimi only when explicitly enabled and healthy.
- **Cost is a tie-breaker only.** When axes conflict for anything that ships: intelligence > taste > cost.
- **Bulk/mechanical work** (clear-spec implementation, data transformation, migrations): Codex `gpt-6.1-sol` at high effort first (it and `gpt-6-astra` medium were the only Codex configs that never failed in the 2026-10-23 routing bench; sol61 high costs about a quarter of astra at list price but is slower). Run the task's own check or the statement's examples; only if they fail, Haiku low repairs it (`claude -p --model haiku --effort low --tools ""` with the statement, the code and the failing examples); after a failed repair, escalate to `gpt-6-astra` medium (also the pick when latency matters). Don't build with `gpt-6-luna` at any effort or sol61 medium. When Codex is quota-out (exact error text), `haiku` low builds with the same check, and `haiku` medium takes a failed check or a costly miss.
- **Anything user-facing** (UI, copy, API design) needs taste ≥ 7: use `sonnet` or `opus` directly. Never ship raw devin, kimi, or `haiku` output — their taste scores (2, 4, 4) are below the threshold. Devin is fine for implementation substrate when a human or high-taste Claude pass reviews before shipping.
- **Reviews and adversarial critique**: `opus` or `/gstack-claude challenge`. Optionally add spark/codex as an independent second opinion.
- **Research / summarize / small diffs**: use a bounded Spark/Codex subagent first (gpt-6.1-sol low via the host relay or `codex exec`; medium for large or ambiguous; Claude `builder` only when Codex is out); if the task needs live pages, a browser, or screenshots, use `devin-delegate`. Kimi is an opt-in compatibility route only.
- **`haiku` can ship clear-spec code, not taste work.** In a 2026-10-22 routing benchmark (tools-off Python function problems), Haiku 5.5 at medium effort passed 59/60 and every attempt on the hardest set, and Haiku low repairing Codex output that failed its check was the cheapest repair measured. That is function-level evidence only: use it for implementation and repairs with a check behind them, never for UI, copy or API design (taste), and not unreviewed on repo-scale changes.
- **`model:` parameter accepts Claude models only.** The Agent tool's `model:` field does not route to external delegates. Use the configured Spark/Codex worker or `codex-spark --task "..."` adapter for local mechanical work and `devin-delegate --task "..."` for general or browser subtasks. Always use wrappers or the configured skill entrypoint — never call raw engines directly.
- **Never bypass wrappers.** Raw calls skip envelope, fallback, and telemetry — always use `devin-delegate` or the configured Spark/Codex entrypoint; use Kimi only when explicitly enabled.

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
- Review or research step → Spark/Codex bounded subagent; use Devin when browser/sandbox access is required
- Implementation step on a large codebase → `grok-delegate`

Delegates keep subagent context small: only the result summary enters the parent context,
not the full implementation.

## With GStack

GStack includes `/spark` (Codex write-mode) as a built-in. `delegate-skill` adds:

- `devin-delegate` — when spark needs a real browser, shell, or debugging sandbox
- Kimi remains an optional compatibility route for cheap read-only research when explicitly enabled
- `grok-delegate` — when the codebase is too large for spark's context window

Install both GStack and `delegate-skill` to get the full execution layer.

## Health check

```bash
devin-delegate --check
codex --version
codex-spark --check
# Optional compatibility route:
kimi-delegate --check
grok-delegate --check
```

## Install / update

```bash
bash ~/.agents/skills/delegate-skill/setup.sh
```
