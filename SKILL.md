---
name: delegate-skill
description: "Route bounded tasks to the right lane: Codex (builds, fan-outs), Devin (unknown scope, browser/UI, sandbox), Grok (small mechanical work only)."
triggers:
  - which delegate should I use
  - delegate this task
  - use a subagent for this
  - should I use devin
  - should I use grok
  - codex fanout
  - fan out to codex
allowed-tools:
  - Bash
  - Read
---

# Delegate routing

Ladders, quota fallbacks and review slots live in `~/.claude/CLAUDE.md` ("Cheapest lane that works") and `~/.config/crss/staffing.md`. Read those first; this file only holds the commands. Always scope the task: goal, constraints, acceptance check, output format.

## Picking the right delegate and model

| Task | Lane | Command |
|---|---|---|
| Bulk read, summary, light plan or review-light (operator 2026-11-25) | Gemini via agy FIRST where the bench passes (Flash bulk, Neon planning); else Codex | see "Gemini via agy" below |
| Build / mechanical edit with a check | Codex `gpt-6.1-terra` low (sol61 high for hard uncovered work) | `codex exec -m gpt-6.1-terra -c model_reasoning_effort=low -c service_tier=priority --cd <dir> --sandbox workspace-write "<task>" </dev/null` |
| Codex blocked or out | Grok or Devin first (rows below), then Haiku low (Haiku high after a failed check) | Agent tool, `model: haiku` |
| Unknown scope, browser/UI, sandbox | Devin | `devin-delegate --task "..." --workspace <trusted git repo>` |
| Small mechanical work, never review | Grok | `grok -p "<task>" --cwd <dir> --always-approve --no-subagents </dev/null` |
| Review | gpt-6.1-sol or Claude; never Grok | see staffing.md |

Judge output, not price: a weak result is redone on a stronger lane without asking. Anything user-facing (UI, copy, API design) needs Sonnet or Opus taste, never raw Devin or Haiku.

## Gemini via agy (operator 2026-11-25; Google AI Pro, plan CA$26.99/mo, $30.50 charged 2026-11-25 with tax, Play Canada)
Numbers (pass rate, sec/call, quota points per 12 calls): the Gemini tables on the DispatchBench report, https://chimericlabs.xyz/dispatchbench/. Rough (small n). Use a model only where its row passes the check you need; unlisted models are not cleared.
- Call: `cd <scratch dir> && agy -p "<task>" --model gemini-4-neon-medium --output-format json </dev/null` (bulk reads: `--model gemini-3.8-flash-low`). Reply is in `.response`; ids: `agy models`. The level is in the id (the bench also passes `--effort`; a call without it worked 11-25). Never xhigh, never `/swarm`.
- Before a batch: `agy -p "/usage" --model gemini-3.8-flash-low --output-format json </dev/null` (free, no model call): Gemini weekly and 5-hour % remaining. Read again after.
- Stop rules: any 429 (exact text `RESOURCE_EXHAUSTED (code 429)`), one batch over 15 weekly points, or the 5-hour window under 15% remaining. Max 2 concurrent calls. No overnight loops, no repeats to "average out" a miss.
- Fallback: 429 or stop rule hit -> do not wait, go to the Codex row above (then Haiku per the ladder). Send the exact error text to the launcher. Gemini quota is separate from Claude and Codex.
- Verify output like any lane; Gemini output is advisory, never a review signature.

## gemini-api (media models and managed agents; `agy -p` stays for coding runs on the Pro plan)
Official CLI `~/.local/bin/gemini-api` v0.5.0. Key: `~/secrets/gemini_api_key` and `~/.config/gemini-api/config.yaml` (free tier; never print it, redact `AIza...` in logs). Always `--dry-run` first, then one real call; `--output-format json` for machine output; `--async` for video.
- Works on this key (2026-11-25, one call each): `tts "text" --out x.wav` (gemini-3.8-flash-tts), `transcribe -i x.wav --format text --out t.txt`, `generate "..." -m gemini-3.1-flash-lite`, `video "..." --async` accepts a job.
- Blocked on the free tier: `image` 429 "limit: 0 input tokens per minute on Free Tier" (gemini-nano-banana-2.1); `music` 429 "limit: 0 requests per day on Free Tier" (lyria-3-pro); `video` job ended "failed"; `analyze` (default gemini-4-hydrogen) 503 "currently experiencing high demand"; `generate -m gemini-3.8-flash` hung 90 s. Check each model once before relying on it; on 429/503 fall back, do not retry in a loop.

## Colab (operator 2026-11-25; `colab` CLI v0.8, login in `~/.config/colab-cli`, account on Google AI plan)
Use for GPU/TPU jobs, long benches and model runs the host cannot do (host is CPU only). Smoke tests 2026-11-25, 8192² matmul: CPU 2 vCPU 12.7 GB; T4 22 TFLOPS fp16, 12.7 GB RAM, 32 s; L4 62 TFLOPS fp16, 53 GB RAM, 12 CPUs, 19 s (2.33 units/h); TPU v5e-1 186 TFLOPS bf16, 47 GB RAM, 23 s. Not available: H100 ("Backend rejected accelerator 'H100'... quota or entitlement"), A100 and G4 (503 Service Unavailable on assign after ~190 s), TPU V6E1 (no session within 420 s). Availability moves; test before planning a run.
- One-shot: `colab run --gpu L4 script.py [args]` (creates, runs, stops; `--keep` leaves it up). Session: `colab new -s NAME --gpu L4|T4|--tpu V5E1`, `colab upload -s NAME LOCAL REMOTE`, `colab exec -s NAME -f job.py`, `colab download -s NAME REMOTE LOCAL`, `colab drivemount -s NAME /content/drive`, `colab stop -s NAME`.
- `colab exec` drops after about 30 s of silence and on connection loss: start long jobs in the background on the VM (`nohup ... &`) and poll with short execs. The CUDA llama.cpp build needs `/usr/lib64-nvidia` on LD_LIBRARY_PATH.
- Stop the meter: every session you start ends in `colab stop`, then `colab sessions` and `colab usage` must show none and 0.00/hr. Idle sessions burn units.
- Units budget: run `colab usage` before and after each job and report both balances and the burn rate. No purchases; `colab pay` is the operator's. Balance 198.54 units on 2026-11-25; no `usage` figure is available per accelerator, only the account rate while a session is live.

## Devin

`devin-delegate` is a thin wrapper over `devin -p`: no fallback, no history. Check it with `devin-delegate --check`.
- Exit 126: untrusted workspace or auth failure. Do not retry; trust the directory (Devin `trusted_workspaces.json`) or run `devin auth login`.
- Exit 124: timed out (`DEVIN_DELEGATE_TIMEOUT`, default 600 s). Treat as failure and move down the ladder.
- Verify its output; it is unreviewed.

## Grok

Grok: `grok login` to authenticate; never read `~/.grok/auth.json`.
