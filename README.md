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
