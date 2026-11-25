# Footprint of code mode, MCP SDK and provider SDKs

Issue: ladkrish233/pycode#8. Date: 2026-11-25. Throwaway branch, do not merge.
Method and baselines reused from `research/pydantic-footprint` (#3) and `research/competitor-baselines` (#2). Not redone.

## Method (all M = measured)

- x86_64 Linux, 16 threads, Python 3.12.14, fresh uv venv, warm .pyc (one throwaway run first), `python -I`, `PYDANTIC_AI_NO_BANNER=1`.
- Each probe is a fresh process, **7 runs, median**. Wall = `perf_counter` from first line to end of probe (excludes interpreter start, ~10 ms). RSS = `VmRSS` at end of probe (idle, after imports/construction); equals peak here (VmHWM identical or within 1.5 MB).
- No model calls and no API key. "Request" = `run_sync` against a local `FunctionModel`/`TestModel`.
- Versions: pydantic-ai-slim 2.74.0, pydantic-ai-harness 0.74.0, pydantic-monty 1.7.0, mcp 2.3.0, fastmcp-slim 4.2.6, anthropic 2.14.0, openai 3.59.0.
- Probes + runner: `docs/research/code-mode-probes/*.py`, `docs/research/code-mode-run.sh` (run from the venv's parent dir).
- Install size = `du -sk` of `site-packages` of a fresh venv per extra (disk blocks, slightly above byte size).

## Results

Baseline (agent with one tool, `FunctionModel`, one request): **424 ms, 64.6 MB, 699 modules** (consistent with #3: 0.51 s / 64 MB with TestModel). Bare `python -I`: 11.2 MB.

| Added piece | Wall (ms) | RSS (MB) | Delta vs baseline | Install delta (MB) |
|---|---|---|---|---|
| (a) `pydantic_monty` import alone (no pydantic-ai) | 33 | 26.1 | +15 MB over bare python | ~12 (monty, monty-client, monty-runtime) |
| (a) `from pydantic_ai_harness.code_mode import CodeMode` | 442 | 67.8 | +27 ms / +3 MB over 415 ms / 63.6 MB construct-only baseline | harness +8.4 |
| (a) Agent with `CodeMode()` + 1 tool + 1 request | 470 | 73.6 | **+46 ms, +9 MB** | harness 8.4 + monty ~12 = ~20 |
| (a) Real `run_code` round trip (`sum(range(100))` via monty) | 55 for the whole run | 75 | no child processes left | -- |
| (b) `import mcp` + `ClientSession`, `stdio_client` (no pydantic-ai) | 372 | 62.1 | n/a (standalone; 587 modules) | -- |
| (b) pydantic-ai `MCPToolset` import (`[mcp]` extra) | 887 | 104.1 | **+463 ms, +40 MB** over 415 ms / 63.6 MB | **+45.4** (32 extra packages) |
| (c) anthropic SDK import alone | 615 | 76.3 | n/a standalone (3508 modules) | +20.3 (3 pkgs) |
| (c) openai SDK import alone | 258 | 47.6 | n/a standalone (843 modules) | +25.5 (9 pkgs) |
| (c) pydantic-ai + Anthropic model/provider, eager | 995 | 107.2 | **+580 ms, +43.6 MB** (3886 modules) | +20.3 |
| (c) pydantic-ai + OpenAI model/provider, eager | 626 | 81.0 | **+211 ms, +17.4 MB** (1262 modules) | +25.5 |
| Lazy: `Agent("anthropic:...", defer_model_check=True)` | 390 | 58.6 | **-25 ms, -5 MB** (no provider imported, 685 modules) | (still installed) |
| Lazy, then first `infer_model(...)` (pays the import) | 977 | 107.3 | same as eager, just moved to first request | -- |

Install sets (fresh venv, `site-packages`): `pydantic-ai-slim` 26.6 MB (17 pkgs); `+harness` 35.0 MB; `slim[anthropic]` 46.9 MB; `slim[openai]` 52.1 MB; `slim[mcp]` 72.0 MB (49 pkgs); everything above plus monty (the earlier venv) 137 MB.
Estimate (E, sum of deltas, not installed together): slim + anthropic + harness + monty ~ 67 MB.

Gotchas:
- `Agent("anthropic:model")` **imports the SDK eagerly at construction** (989 ms, 109.8 MB). Lazy needs `defer_model_check=True` or building the model on first use.
- `pydantic-ai-harness` does not install monty by itself; `CodeMode` needs the `code-mode` extra (`pydantic-ai-harness[code-mode]`, per the ImportError text in `code_mode/_toolset.py`). The harness venv had 18 pkgs vs 17 for slim.
- `run_code` ran in-process here (default executor); pydantic_monty also offers subprocess worker pools (`pydantic_monty` docs string: "pool of `monty` subprocess workers") and a remote client. Per-pool RSS not measured.
- With `TestModel`, `CodeMode` fails (it calls `run_code` with junk args); use a `FunctionModel` for tests.

Fleet (M, 5 runs each, 50 agents in one process, each with 1 tool + 1 request): ~10 KB/agent without CodeMode, ~11-13 KB/agent with it, 74 MB process total. Modules are shared, so in-process agents are nearly free. Process-per-agent = 50 x ~65-75 MB = ~3.3-3.7 GB (E, arithmetic, not run); fork/COW sharing not measured.

## Verdict against pycode targets

| Target | Without code mode | Code mode adds | Fits? |
|---|---|---|---|
| Idle RSS <= 60 MB | 58.6 MB only if provider + MCP lazy (pydantic-ai baseline alone is 63.6 MB constructed) | +9 MB when active, +3 MB import only | **No, borderline even without it**; code mode pushes to ~68-74 MB |
| Prompt ready <= 100 ms | ~390-415 ms (pydantic-ai import alone) | +27 to +46 ms | **No**; dominated by pydantic-ai, not code mode |
| First request <= 1.0 s | Anthropic lazy import ~0.98 s total (E: ~1.0 s); OpenAI ~0.63 s | +~46 ms | **Marginal** for Anthropic, ok for OpenAI (combination not measured) |
| Install <= 100 MB | ~47 MB (slim+anthropic) | ~+20 MB (harness 8 + monty 12) | **Yes, ~67 MB**; MCP extra alone adds 45 MB and breaks it with other extras (~112 MB E) |
| 50-agent fleet <= 500 MB | ~74 MB in one process | ~+0.2 MB total | **Yes in-process**; **no** as 50 separate processes (~3.5 GB) |

Plain reading: code mode is cheap at the margin (+~9 MB RSS, +~25-45 ms, +~20 MB disk, no idle child process). The big costs are pydantic-ai itself (~400 ms, ~64 MB), the MCP client (+463 ms / +40 MB / +45 MB disk) and the Anthropic SDK (+580 ms / +44 MB). RSS and prompt-ready targets are already missed before code mode and cannot be met with pydantic-ai in the process; they need to be revisited or the agent core must not be pydantic-ai.

## Recommendation (plan only, no pycode code)

1. Make code mode **opt-in**: lazy-import `pydantic_ai_harness.code_mode` and `pydantic_monty` only when enabled. Idle cost then 0.
2. Lazy-import MCP and each provider (`defer_model_check=True`); import the single configured provider on first request. Accept the first-request hit, or show the prompt first and import in a background thread (E, untested).
3. Run fleets as one process with many Agent objects, not process-per-agent.
4. Treat the 60 MB / 100 ms targets as unattainable with pydantic-ai; decide in #7 whether to relax them (suggest ~75 MB idle, ~450 ms prompt) or drop pydantic-ai from the hot path.
5. Pin exact versions; harness is Alpha and moves in lockstep with slim.

## Not measured

Combined stacks (anthropic + MCP + code mode), real model/network latency, long-conversation memory, Windows, cold (no .pyc) start, monty worker-pool/remote RSS, fork/COW fleets, a real MCP server connection.
