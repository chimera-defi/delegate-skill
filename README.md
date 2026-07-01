# delegate-skill

One-stop index for AI delegation skills. Install all four with a single command.

## Install

```bash
git clone https://github.com/chimera-defi/delegate-skill
cd delegate-skill
bash setup.sh
```

## Skills

| Skill | Purpose | Source |
|-------|---------|--------|
| `devin-delegate` | Browser, UI, screenshot, sandbox implementation | [chimera-defi/devin-delegate](https://github.com/chimera-defi/devin-delegate) |
| `kimi-delegate` | Cheap bounded research, summarize, draft, review | [chimera-defi/kimi-delegate-skill](https://github.com/chimera-defi/kimi-delegate-skill) |
| `grok-delegate` | Multi-file refactor, large-codebase implementation | [chimera-defi/grok-delegate](https://github.com/chimera-defi/grok-delegate) |
| `spark` | Local Codex write-mode implementation | via [gstack](https://github.com/chimera-defi/gstack) |

## Routing

Canonical routing table (with rules, fallback, auth, and latency notes) lives in
[`SKILL.md`](SKILL.md). Quick summary:

| Task | Use |
|------|-----|
| General implement / review / debug (workhorse) | `devin-delegate` |
| Browser / UI / screenshot / sandbox (a devin capability) | `devin-delegate` |
| Cheap **small read-only** search / summarize / review | `kimi-delegate` |
| Local Codex write-mode | `/spark` |
| Multi-file refactor / very large repo (DORMANT) | `grok-delegate` |
| Unclear scope | `devin-delegate` (workhorse); if cheap+small, `kimi-delegate` |

`grok-delegate` is **dormant** — revival gate: ≥5 successful calls + a documented devin
failure on a large repo.

Never call delegates directly (`opencode`, `devin`, `pi --provider kimi-coding`). Always use the wrapper binaries — they provide envelope, fallback, and telemetry.

## Superpowers & GStack integration

`setup.sh` wires delegate-skill into your global agent environment automatically:

- **`~/.claude/skills/delegate-skill`** → symlinked so Claude Code loads the skill in every workspace
- **`~/.claude/CLAUDE.md`** → routing block injected so every session can route to delegates without opening this repo
- **SKILL.md** → triggers auto-load: say "delegate this task" or "which delegate should I use" and routing is invoked

### With Superpowers

`superpowers:subagent-driven-development` dispatches fresh subagents per task. Those subagents can use delegate skills for bounded work:

- Implementation step needing a browser → `devin-delegate`
- Review or research step → `kimi-delegate` (cheaper than a full subagent)
- Implementation step on a large codebase → `grok-delegate`

Delegates keep subagent context small: only the result summary enters the parent context.

### With GStack

GStack includes `/spark` (Codex write-mode) as a built-in. `delegate-skill` extends it:

- `devin-delegate` — real browser, shell, debugging sandbox
- `kimi-delegate` — cheap parallel research without burning spark's context
- `grok-delegate` — large-codebase tasks beyond spark's context window

Install both to get the full execution layer.

## Claude plugin

Install as a Claude Code plugin to make all skills available via slash commands:

```bash
claude plugin install .
```

## Agent compatibility

| Agent | Routing file |
|-------|-------------|
| Claude Code | CLAUDE.md |
| Codex / ChatGPT | AGENTS.md |
| Gemini CLI | GEMINI.md |
