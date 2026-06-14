# delegate-skill — Agent Routing (Codex / OpenAI / ChatGPT)

> This file provides routing guidance for non-Claude agents. For Claude Code, see CLAUDE.md.

<!-- delegate-skill:begin -->
## AI Delegation Routing

| Task type | Delegate | Command |
|-----------|----------|---------|
| Browser, UI, screenshot, sandbox implementation | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Cheap search / summarize / draft / review | `kimi-delegate` | `kimi-delegate --task "..."` |
| Multi-file refactor, large-codebase implementation | `grok-delegate` | `./skills/grok-delegate/scripts/delegate.py --task "..."` |
| Local Codex write-mode implementation | `spark` | invoke via Codex write-mode |
| Unknown / orchestration | `kimi-delegate` first, then escalate | `kimi-delegate --task "scope: ..."` |

### Rules

- **Never call delegates directly** (`opencode`, `pi --provider kimi-coding`, `devin`) — always use the wrapper scripts. Wrappers inject the envelope, fallback chain, and telemetry.
- **Always include scope** in the task prompt: goal, constraints, acceptance checks, expected output format.
- **Auth errors exit 126** — do not auto-retry. Print resume steps for the user.

### Quick-start

```bash
# Check all delegates are healthy
devin-delegate --check
kimi-delegate --check
grok-delegate --check

# Run setup if binaries are missing
bash setup.sh
```
<!-- delegate-skill:end -->
