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

| Task | Use |
|------|-----|
| Browser / UI / screenshot | `devin-delegate` |
| Search / summarize / review | `kimi-delegate` |
| Multi-file refactor / large repo | `grok-delegate` |
| Local Codex write-mode | `/spark` |
| Unclear scope | `kimi-delegate` to scope, then escalate |

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
