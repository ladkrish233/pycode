# Footprint of terminal UI options: raw ANSI vs prompt_toolkit vs rich

Issue: ladkrish233/pycode#10. Date: 2026-11-25. Throwaway branch, do not merge.
Targets from #5/#7: idle RSS <= 60 MB at the prompt before the first keystroke, prompt settled <= 100 ms, first request <= 1.0 s, install <= 100 MB. Method follows `research/code-mode-footprint` (#8).

## Method (all M = measured)

- x86_64 Linux, 16 threads, Python 3.12.14 (uv), one fresh uv venv per option, warm .pyc (one throwaway run first). Versions: prompt_toolkit 3.0.53 (+wcwidth 0.9.5), rich 15.0.0 (+markdown-it-py 4.3.0, mdurl, pygments 2.21.0), pydantic-ai-slim 2.74.0, pyte (screen emulator, test tool only).
- **Import/use probes** (`docs/research/terminal-ui-probes/*.py`, runner `run.py`): fresh `python -s` process per run, **11 runs, median**. Wall = `perf_counter` from first line of the probe to the end (excludes interpreter start, ~10 ms). RSS = `VmRSS` at the end. "Empty shell" = `python -s` that does nothing.
- **Prompt-settled probe** (`pty_run.py`, `pty_bench.py`): the demo runs in a real pty (24x80), and the driver answers cursor-position queries from a pyte screen. Time = spawn to last byte of the finished prompt (includes interpreter start); RSS = child `VmRSS` at that moment. **9 runs, median.** Keys are then sent (typing, Alt+Enter, Enter, `y`) and the final screen is dumped via pyte to check what was drawn.
- No model calls, no API key. The raw ANSI editor is a ~120-line sketch (`ui_raw.py`), a probe, not pycode code.

## Numbers

| Option | What is loaded | Import / use wall | RSS | Modules |
|---|---|---|---|---|
| Empty shell | nothing | 0.1 ms | 11.2 MB | 46 |
| Raw ANSI/stdlib | import readline, textwrap, shutil, termios, tty, select, signal, re | 4.9 ms | 12.9 MB | 71 |
| Raw ANSI/stdlib | `ui_raw` used: box + wrap + spinner frame + readline history | 4.3 ms | 12.8 MB | 66 |
| prompt_toolkit | `from prompt_toolkit import PromptSession` | 60.3 ms | 27.1 MB | 328 |
| prompt_toolkit | session built, history, key bindings, toolbar, one `prompt()` on a pipe input | 72.8 ms | 29.9 MB | 337 |
| rich | `Console` only | 24.8 ms | 17.4 MB | 136 |
| rich | Console, Markdown, Live, Panel, Spinner imported | 48.7 ms | 20.7 MB | 252 |
| rich | those + Panel + Live streaming of a small markdown char by char + `status()` | 83.2 ms | 23.0 MB | 258 |

**Prompt settled, in a real pty (spawn to finished box, median of 9):**

| Prompt | Settled | RSS at prompt |
|---|---|---|
| Empty python printing one line (reference) | 9 ms | 11.2 MB |
| Raw ANSI boxed prompt (`ui_raw.read_box`) | **14 ms** | **12.6 MB** |
| prompt_toolkit boxed prompt (`demo_pt.py`) | **83 ms** | **30.1 MB** |
| rich | n/a: rich has no input line | n/a |

**On top of the agent** (`pydantic-ai-slim`, one `TestModel` request, same method; the #8 baseline reproduced: 431 ms / 64.4 MB vs 424 ms / 64.6 MB):

| Stack | Wall | RSS | Delta vs agent only |
|---|---|---|---|
| pydantic-ai agent only (`pai_base.py`) | 430.7 ms | 64.4 MB | -- |
| + rich Console/Markdown/Live, one render (`pai_rich.py`) | 477.5 ms | 68.7 MB | **+47 ms, +4.3 MB** |
| + prompt_toolkit PromptSession/confirm imported (`pai_pt.py`) | 460.9 ms | 70.1 MB | **+30 ms, +5.7 MB** |

Sharing makes the sums smaller than the standalone numbers (pydantic-ai already loads typing, asyncio, etc.).

**Install size** (`du -sk` of `site-packages` in a fresh venv, disk blocks, includes .pyc after use):

| Piece | MB |
|---|---|
| stdlib only | 0 |
| prompt_toolkit (+ wcwidth) | 7.9 |
| rich (+ markdown-it-py, mdurl, pygments) | 9.0 |
| pydantic-ai-slim alone | 26.6 |
| pydantic-ai-slim + rich + prompt_toolkit together | 39.4 (rich+pt delta 12.8) |

From #8, slim + anthropic + harness + monty is ~67 MB (E); adding rich + prompt_toolkit gives ~80 MB (E, sum, not installed together). Both together or either alone stay under 100 MB.

## What each can render (checked in the pty, screen dumped via pyte)

| Need | Raw ANSI/stdlib | prompt_toolkit | rich |
|---|---|---|---|
| Boxed multiline prompt | **Yes (M)**. `ui_raw.read_box`: rule above, `> ` first line, `  ` continuation, rule below, status line; Alt+Enter and Ctrl+J insert a newline; box stays in scrollback after Enter. Must write the editor yourself. | **Yes (M)** with `multiline=False` + a key binding for Alt+Enter, a multi-line `ANSI` message for the top rule, `prompt_continuation`, `bottom_toolbar` (style `noreverse`). On Enter the bottom toolbar (bottom rule + status) is **erased**, so only the top rule and input remain in scrollback; keeping the bottom rule needs extra work (not tried). It also queries the cursor position (CPR) at start. | **No input.** `Panel` draws a static box; `rich.prompt` calls `console.input()` which calls `input()` (source: `console.py:2189`, `prompt.py:211`): one line, Enter required. |
| History | Up/Down over an in-memory list (M). Persistent file history, search (Ctrl+R) are yours to write. `readline` also works but only for single-line `input()`. | Yes (M): `InMemoryHistory`/`FileHistory`, search built in. | No. |
| Streamed markdown | Line-buffered mini renderer (`MdStream`: headings, bold, italic, inline code, bullets, fenced code) **works (M)**. No tables, links, nested lists, syntax colours, or wrapping-aware lists unless written. | **No markdown.** `print_formatted_text` only prints styled text; you still need a renderer. | **Yes**, the full CommonMark-ish renderer (tables, code with pygments, lists). See the Live caveat below. |
| Spinner | Thread + `\r\x1b[K` frame loop (M, `Spinner`). | Not for free outside a prompt (`ProgressBar` exists, not tested). Same raw loop works. | Yes (M): `Console.status()` / `Spinner`. |
| Status line | Printed line under the box (M). | `bottom_toolbar` (M), live-updating while typing. | Only via `Live`. |
| y/n permission | Single key via `tty.setcbreak` (M, `confirm`). | `shortcuts.confirm` single key (M). | `Confirm.ask`: needs Enter (`input()`). |

### The rich Live caveat (M, 24-row pty, 46-line markdown answer)

| Streaming method | Wall | Clean scrollback? |
|---|---|---|
| `Live(Markdown)` default `vertical_overflow="ellipsis"` | 544 ms | Final answer is printed in full at the end, but while streaming only the last screenful shows (cropped). |
| `Live(..., vertical_overflow="visible")` | 544 ms | **No**: 88 "item" lines for 40 items, the heading appears twice; each frame taller than the screen leaves a copy in scrollback. |
| Print each finished block once with `console.print(Markdown(block))` | **56 ms** | **Yes**: 40 items once. |

`Live` re-parses and re-renders the whole document on every update (O(n^2)), so it is ~10x slower and misbehaves in scrollback once the answer is taller than the terminal. Block-wise printing (flush on blank line) fits a scrollback UI; the cost is that a block appears only when it ends.

## Verdict against pycode targets

| Target | Raw ANSI shell | prompt_toolkit shell | rich (lazy, with agent) |
|---|---|---|---|
| Idle RSS <= 60 MB before first keystroke | **12.6 MB, fits** | **30.1 MB, fits** | not in the shell; +4.3 MB once loaded |
| Prompt settled <= 100 ms | **14 ms, fits** | **83 ms, fits but takes 83% of the budget** (M on a 16-thread desktop; slower machines will exceed) | not on the start path |
| First request <= 1.0 s | adds nothing | adds ~0 if pt is already loaded; +30 ms/+5.7 MB only if imported after the agent | +47 ms / +4.3 MB on first answer |
| Install <= 100 MB | 0 MB | +7.9 MB | +9.0 MB |

Combination that fits:

1. **Start-up shell = raw ANSI/stdlib** (prompt 14 ms, 12.6 MB). prompt_toolkit passes the targets alone but spends 83 ms of the 100 ms budget and 30 MB of the 60 MB, and the agent import on the first keystroke would then sit on top of it (pt + agent = 70 MB, #8 numbers + this).
2. **Markdown: either rich imported lazily with the agent (+47 ms, +4.3 MB, +9 MB disk), printed block by block, not with Live; or the ~25-line stdlib renderer** if tables and syntax colouring can be dropped.
3. **Spinner, status line, y/n: raw ANSI.** No library needed.
4. **prompt_toolkit only if** the owner does not want to maintain a line editor. Cost of owning one: wide-character widths, line wrap beyond terminal width, resize, bracketed paste, Ctrl+R search, Home/End/Ctrl-word keys. The sketch implements none of these. Load pt lazily or on a thread only after first paint if used (E, untested).

Note on the #7 plan: it says the agent imports on first keystroke. The 64 MB/430 ms from #8 then lands after the prompt; none of the UI options changes that, and none breaks the pre-first-keystroke target.

## Not measured

- Real terminals (only a pty with a pyte emulator): key encodings of Alt+Enter differ per terminal (Kitty protocol, Windows Terminal, tmux); wide characters/emoji width; paste; resize.
- Windows: `termios`/`tty` do not exist there, so the raw editor needs `msvcrt`/VT mode; prompt_toolkit and rich support Windows. Not tested.
- Cold (no .pyc) start; slower machines; hot-path CPU of the raw editor under heavy paste.
- Keeping the prompt_toolkit bottom rule in scrollback; `ProgressBar`; rich `Live` with `transient=True`.
- First keystroke latency with lazy pt import (E only).
- Claude Code's exact visuals (no side-by-side comparison done).
