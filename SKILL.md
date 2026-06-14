---
name: delegate-skill
preamble-tier: 4
version: 1.0.0
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

| Task type | Delegate | Command |
|-----------|----------|---------|
| Browser, UI, screenshot, sandbox impl | `devin-delegate` | `devin-delegate --task "..." --workspace /path` |
| Cheap search / summarize / draft / review | `kimi-delegate` | `kimi-delegate --task "..."` |
| Multi-file refactor, large-codebase impl | `grok-delegate` | `grok-delegate --task "..."` |
| Local Codex write-mode implementation | `spark` | `/spark` |
| Unknown scope / orchestration | `kimi-delegate` first, then escalate | `kimi-delegate --task "scope: ..."` |

## Rules

- **Never bypass wrappers.** Raw calls (`opencode`, `devin`, `pi --provider kimi-coding`) skip
  envelope injection, fallback, and telemetry. Always use the binary wrappers.
- **Always scope the task.** Include: goal, constraints, acceptance checks, expected output format.
- **Auth errors → exit 126.** Do not auto-retry. Print resume steps for the user.

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
