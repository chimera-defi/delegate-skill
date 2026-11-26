---
name: delegate-skill
description: "Route bounded tasks to the right lane, Gemini via agy first (tiered by DispatchBench Rounds 2-3), then Codex, Devin, Grok, Claude fallbacks."
triggers:
  - which delegate should I use
  - delegate this task
  - use a subagent for this
  - use gemini
  - use agy
  - use neon
  - gemini routing
  - should I use devin
  - should I use grok
  - codex fanout
  - fan out to codex
allowed-tools:
  - Bash
  - Read
---

# Delegate routing

Ladders, quota fallbacks and review slots live in the host config . Read those first; this file only holds the commands. Always scope the task: goal, constraints, acceptance check, output format.

## Picking the right delegate and model

Evidence: DispatchBench Rounds 2-3, https://chimericlabs.xyz/dispatchbench/ (small n, rough). Use a model only where its row passes the check you need; unlisted models are not cleared.

| Task | Lane / model | Evidence |
|---|---|---|
| Bulk read, scan, summary | `gemini-3.8-flash-low` or `gemini-4-hydrogen-low` | 50/60 @ 9.3 s; 56/60 @ 9.7 s |
| Bounded build / edit with a test check | `gemini-4-argon-medium` or `gemini-4-hydrogen-medium` | argon 58/60 (96.7%) L1-L6 @ 12.0 s median, 15/15 L7 @ 13.1 s; hydrogen-medium 59/60 (98.3%) @ 16.3 s |
| Harder logic (escalate from above) | `gemini-4-neon-low` (cheapest, ~2.6% weekly per 48 calls), `gemini-4-neon-medium`, `gemini-4-hydrogen-high` | neon-low 60/60 @ 21.7 s, L7 4/4; neon-medium 60/60 @ 37.4 s; hydrogen-high 60/60 @ 26.9 s |
| Multi-file parallel read/scan fan-out | `gemini-pro-orchestrator-neon`, max 3 subagents, never `--effort` | 12/12 @ 70.5 s |
| Hard/uncovered build, or independent second-family review (agy Claude/GPT pool) | `claude-sonnet-5-5` (builder), `claude-opus-5-5-medium` (planning/review, never `--effort`) | use when direct Claude/Codex is tight |
| Build with a check (non-Gemini) | Codex `gpt-6.1-terra` low (`sol61` high for hard uncovered work) | `codex exec -m gpt-6.1-terra -c model_reasoning_effort=low -c service_tier=priority --cd <dir> --sandbox workspace-write "<task>" </dev/null` |
| Unknown scope, browser/UI, sandbox | Devin | `devin-delegate --task "..." --workspace <trusted git repo>` |
| Small mechanical work, never review | Grok | `grok -p "<task>" --cwd <dir> --always-approve --no-subagents </dev/null` |
| Fallback when others are out | Haiku low (high after a failed check) | Agent tool, `model: haiku` |
| Review | gpt-6.1-sol or Claude; Opus via agy for a second family; never Grok | host staffing file |

Judge output, not price: a weak result is redone on a stronger lane without asking. Anything user-facing (UI, copy, API design) needs Sonnet or Opus taste, never raw Devin or Haiku. Gemini output is advisory, never a review signature.

## Gemini via agy

Ids: `agy models`. The level is in the id; never pass `--effort` to orchestrator or Opus ids. Never xhigh, never `/swarm`. Reply is in `.response`.
- Read-only Q&A / plan: `cd <scratch> && agy -p "<task>" --model <id> --output-format json </dev/null`
- **Worktree harness loop (default for bounded builds)**: make an isolated git worktree, put `BRIEF.md` (goal, constraints, acceptance test) in it, then `cd <worktree> && agy -p "Read BRIEF.md. plan, build, test, refactor/review, verify" --model gemini-4-argon-medium --dangerously-skip-permissions --output-format json </dev/null`. Review the diff and rerun the test yourself. Shell-less alternative: `--mode accept-edits` with "No shell access; edit files only", and the orchestrator runs the tests.
- Fan-out: `agy -p "<scan task over files in cwd>" --model gemini-pro-orchestrator-neon --output-format json </dev/null` (no `--effort`, max 3 subagents).
- Vision: put the images in the cwd and name them in the prompt.
- Telemetry (free, no model call): `agy -p "/usage" --model gemini-3.8-flash-low --output-format json </dev/null` before and after a batch.

### Pools, stop rules, fallback
- Two separate agy quota pools: **Gemini** and **Claude/GPT** (the `claude-*` ids). Read both in `/usage`.
- Max 3 concurrent calls. Floors: Gemini 5-hour remaining >= 15% and weekly remaining >= 15%; below either, stop launching. Overnight runs are allowed within the floors.
- Hard stop on the first `RESOURCE_EXHAUSTED (code 429)` or `UNAVAILABLE (code 503)`: no retry loops, no repeats to average out a miss. Report the exact error text.
- Quota-out ladder: Gemini pool out -> Claude/GPT agy pool (`claude-sonnet-5-5`) for builds, Haiku high for reads -> Codex -> Grok (mechanical) or Devin -> Sonnet builder. Claude/GPT pool out too -> direct Claude/Codex lanes.

## gemini-api (media models; `agy -p` stays for coding runs on the Pro plan)
Official `gemini-api` CLI. Key from the host secret store (free tier; never print it, redact `AIza...` in logs). Always `--dry-run` first, then one real call; `--output-format json` for machine output; `--async` for video.
- Works on this key (2026-11-25, one call each): `tts "text" --out x.wav` (gemini-3.8-flash-tts), `transcribe -i x.wav --format text --out t.txt`, `generate "..." -m gemini-3.1-flash-lite`, `video "..." --async` accepts a job.
- Blocked on the free tier: `image` 429 "limit: 0 input tokens per minute on Free Tier" (gemini-nano-banana-2.1); `music` 429 "limit: 0 requests per day on Free Tier" (lyria-3-pro); `video` job ended "failed"; `analyze` (default gemini-4-hydrogen) 503 "currently experiencing high demand"; `generate -m gemini-3.8-flash` hung 90 s. Check each model once before relying on it; on 429/503 fall back, do not retry in a loop. On 429 or 503 use agy or Haiku for text tasks; media has no fallback, report it.

## Colab (operator 2026-11-25; `colab` CLI v0.8, login stored by the CLI)
Use for GPU/TPU jobs, long benches and model runs the host cannot do (host is CPU only). Smoke tests 2026-11-25, 8192² matmul: CPU 2 vCPU 12.7 GB; T4 22 TFLOPS fp16, 12.7 GB RAM, 32 s; L4 62 TFLOPS fp16, 53 GB RAM, 12 CPUs, 19 s (2.33 units/h); TPU v5e-1 186 TFLOPS bf16, 47 GB RAM, 23 s. Not available: H100 ("Backend rejected accelerator 'H100'... quota or entitlement"), A100 and G4 (503 Service Unavailable on assign after ~190 s), TPU V6E1 (503 Service Unavailable after about 3 min); A100, G4 and V6E1 all kept returning 503 over about 1 h of retries every 5 min (01:38-02:39Z 2026-11-26), so treat them as no capacity for this account. Availability moves; test before planning a run.
- One-shot: `colab run --gpu L4 script.py [args]` (creates, runs, stops; `--keep` leaves it up). Session: `colab new -s NAME (--gpu L4, --gpu T4 or --tpu V5E1)`, `colab upload -s NAME LOCAL REMOTE`, `colab exec -s NAME -f job.py`, `colab download -s NAME REMOTE LOCAL`, `colab drivemount -s NAME /content/drive`, `colab stop -s NAME`.
- `colab exec` drops after about 30 s of silence and on connection loss: start long jobs in the background on the VM (`nohup ... &`) and poll with short execs. The CUDA llama.cpp build needs `/usr/lib64-nvidia` on LD_LIBRARY_PATH.
- Callable model endpoint (verified 2026-11-26, Inkling 2 Mini IQ4_NL on L4, 36 tok/s, 7 s for a 200-token reply; cold start 24 s session + 2 min downloads (llama.cpp b12600 CUDA tarball and the 17.6 GB GGUF from `ggml-org/Inkling-2-Mini-GGUF`) + about 1.5 min model load, so about 4 min to healthy): `colab new -s S --gpu L4`; on the VM start `llama-server -m m.gguf --jinja -ngl 99 -c 16384 --host 127.0.0.1 --port 8123` in the background (not 8080, it is taken) with `LD_LIBRARY_PATH=<dir>:/usr/lib64-nvidia`; the CUDA backend also needs the `cudart-llama-b12600-bin-ubuntu-cuda-12.8-x64.tar.gz` extracted with `--strip-components=1` into the binary dir (without it the server silently runs on CPU at 5.8 tok/s, GPU 0 MiB). Tunnel from the host (use a dedicated Colab-only SSH key; never print or commit it): `ssh -N -i <key> -o ProxyCommand="colab ssh --proxy-mode -s S -i <key>.pub" -L 18123:127.0.0.1:8123 root@colab` (record its PID), then POST an OpenAI-style chat request to `localhost:18123/v1/chat/completions`. Only one `colab ssh` connection per session (second gets HTTP 429), so use `colab exec -s S -f x.py` for side commands. Ending the session kills the tunnel, the server and the disk: a restart pays the full 4 min again. Cost 2.33 units/h (about US$0.23/h at list price; USD assumed, not read from a Google page); a 200-token call is under 0.01 unit, a reasoning-heavy bench task about 0.18 unit.
- Plan and browser check: the Google AI Plans card shows the unit balance; runtime types and capacity gaps match the CLI results above (A100/v6e-1 fall back or hang, H100 greyed). The browser UI creates Drive notebooks: prefer the CLI.
- Stop the meter: every session you start ends in `colab stop`, then `colab sessions` and `colab usage` must show none and 0.00/hr. Idle sessions burn units.
- Units budget: run `colab usage` before and after each job and report both balances and the burn rate. No purchases; `colab pay` is the operator's. no `usage` figure is available per accelerator, only the account rate while a session is live. No fallback: the host is CPU only; if Colab is down, report it.

## Devin

`devin-delegate` is a thin wrapper over `devin -p`: no fallback, no history. Check it with `devin-delegate --check`.
- Exit 126: untrusted workspace or auth failure. Do not retry; trust the directory (Devin `trusted_workspaces.json`) or run `devin auth login`.
- Exit 124: timed out (`DEVIN_DELEGATE_TIMEOUT`, default 600 s). Treat as failure and move down the ladder.
- Verify its output; it is unreviewed.

## Grok

Grok: `grok login` to authenticate; never read its auth file.
