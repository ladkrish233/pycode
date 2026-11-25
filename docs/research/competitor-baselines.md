# Competitor baselines: RAM, cold start, latency, install size

Resolves ladkrish233/pycode#2. Date: 2026-11-25.

Legend: **M** = measured by me, **S** = sourced from a primary source, **E** = estimate, **N/A** = not obtained.

## Environment (all M)

Intel i5-14400, 16 threads, 64 GB RAM, Linux 7.0 x86_64, Node v24.21.0, uv-managed Python 3.12, warm disk cache.
Everything was installed into a throwaway scratchpad (npm prefix / venv / extracted tarball) with an empty `HOME`, and no credentials.

## Versions tested

| Tool | Version | Source of binary |
|---|---|---|
| Claude Code | 2.1.332 | `npm i @anthropic-ai/claude-code` (npm registry) |
| Codex CLI | 0.172.0 | `npm i @openai/codex` |
| OpenCode | 1.19.6 | `npm i opencode-ai` |
| aider | 0.86.2 | `uv pip install aider-chat` (Python 3.12) |
| goose | v1.61.0 | GitHub release `goose-x86_64-unknown-linux-gnu.tar.gz` (block/goose) |

## Results

| Tool | Install size on disk (M) | Download artifact (S) | `--version` wall, median of 10 (M) | `--version` max RSS (M) | Idle TUI RSS, process tree, 10 s after launch, **unauthenticated first screen** (M) |
|---|---|---|---|---|---|
| Claude Code | 393 MB (single 402 MB native binary; `npm i` total 393160 KB) | n/a | <10 ms (fast path, see caveat) | 24 MB | 177 MB |
| Codex CLI | 439 MB (native Rust binary package) | n/a | 20 ms | 49 MB | 308 MB |
| OpenCode | 422 MB (`npm i` total; a 211 MB binary ships twice: x64 + x64-baseline, so ~211 MB effective) | n/a | 310 ms | 133 MB | 910 MB |
| aider | 555 MB (venv total 555152 KB) | n/a | 450 ms | 81 MB | 77 MB (prompt screen) |
| goose | 209 MB (single binary + tarball contents) | 63.7 MB `.tar.gz` (S, GitHub release asset list) | <10 ms | 30 MB | 130 MB (first-run telemetry prompt) |

Sizes are `du -sk`, i.e. disk blocks, so slightly above byte sizes.

## Not obtained

- **Peak RAM during a real agent turn: N/A.** Needs a paid API key and a fixed task; I had no credentials and was told not to use any outside the scratchpad. The reproducible method is below.
- **Per-turn overhead (client-side latency excluding model time): N/A.** Same reason. Method below.
- **Vendor-published RAM or latency figures: N/A.** I grepped the READMEs of openai/codex, sst/opencode, Aider-AI/aider and Claude Code's setup docs for RAM/memory/GB/requirement and found no numbers. No primary source states them, so any figure from blog posts would be secondary and is deliberately omitted.

## Caveats (read before citing)

1. **`--version` is not cold start.** Claude Code, goose and Codex short-circuit before loading the app. Real cold-start-to-prompt is longer; the interpreted tools (OpenCode 310 ms, aider 450 ms) show the cost of loading modules even on that path. Treat `--version` as a floor.
2. **Idle RSS is a first-screen snapshot, not a working session.** Claude showed the theme picker, Codex the login screen, goose the telemetry prompt, OpenCode its full home UI (hence the 910 MB, which is the likeliest to be representative of a signed-in idle state), aider a prompt. Authenticated idle with a loaded repo and MCP servers will be higher for all. Sum includes child processes.
3. Single machine, single run for RSS, warm cache, no CPU pinning. Run-to-run variance not characterised (E: expect +/-10-20%).
4. Install size includes platform binaries only as npm ships them; Claude/Codex/OpenCode embed a runtime in the binary, which explains ~200-400 MB.

## Takeaways for pycode (E, derived from the above)

- The bar to beat on footprint is low only for aider (~77 MB idle) and goose (~130 MB). The Node/Bun/Rust TUIs idle at 177-910 MB.
- Python import cost is real: aider needs 450 ms just to print its version. A pydantic-ai CLI will pay a similar tax unless imports are lazy. Worth benchmarking `python -X importtime` on a pydantic-ai skeleton early.
- Install size: a pure-Python wheel set with pydantic-ai + one provider SDK will likely land well under aider's 555 MB (E, not measured).

## Reproduce

```sh
# install (per tool, into a scratch dir)
npm i @anthropic-ai/claude-code @openai/codex opencode-ai
uv venv v && VIRTUAL_ENV=v uv pip install aider-chat
curl -LO https://github.com/block/goose/releases/download/v1.61.0/goose-x86_64-unknown-linux-gnu.tar.gz
du -sk <install dir>
./bench_version.sh <name> <binary>        # median wall + max RSS over 10 `--version` runs
python3 -I tui_rss.py <name> <binary> [args]   # pty, 10 s, sums VmRSS over process tree
```

Scripts: `bench_version.sh`, `tui_rss.py` (this directory).

To get the missing numbers: with a key set, run each tool headless on one fixed task (e.g. `claude -p`, `codex exec`, `opencode run`, `aider --message`, `goose run -t`) under `/usr/bin/time -f "%e %M"`, with a mock OpenAI-compatible server returning a fixed reply to isolate client overhead from model latency. Peak RAM = `%M`; per-turn overhead = wall time minus mock server think time.

## Sources

- npm registry packages: `@anthropic-ai/claude-code`, `@openai/codex`, `opencode-ai`, PyPI `aider-chat` (versions above).
- https://github.com/block/goose/releases/tag/v1.61.0 (asset sizes).
- READMEs checked for vendor claims (none found): github.com/openai/codex, github.com/sst/opencode, github.com/Aider-AI/aider, code.claude.com/docs/en/setup.
