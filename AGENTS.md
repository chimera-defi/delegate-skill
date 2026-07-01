# delegate-skill — Agent Routing (Codex / OpenAI / ChatGPT)

> This file provides routing guidance for non-Claude agents. For Claude Code, see CLAUDE.md.

<!-- delegate-skill:begin -->
## AI Delegation Routing

> Canonical routing table lives in `SKILL.md`. This block mirrors it for non-Claude
> agents that do not auto-load the skill. Keep the two in sync when routing changes.

`devin-delegate` is the general implement/review workhorse (browser/sandbox is one of its
capabilities). `kimi-delegate` is for cheap, small, read-only tasks. `grok-delegate` is
**dormant** — revival gate: ≥5 successful calls + a documented devin failure on a large repo.

| Task type | Delegate | Command |
|-----------|----------|---------|
| General implementation / review / debug (workhorse) | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Browser, UI, screenshot, sandbox (a devin capability) | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Cheap **small read-only** search / summarize / draft / review | `kimi-delegate` | `kimi-delegate --task "..."` |
| Local Codex write-mode implementation | `spark` | invoke via Codex write-mode |
| Multi-file refactor on a very large codebase (DORMANT) | `grok-delegate` | `grok-delegate --task "..."` |
| Unknown / orchestration | `devin-delegate` (workhorse); if clearly cheap+small, `kimi-delegate` | `devin-delegate --task "scope: ..."` |

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
