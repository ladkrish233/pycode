# pydantic-ai and pydantic harness: what they give us, and their footprint

Issue: ladkrish233/pycode#3. Date: 2026-11-25.

Legend: **[M]** measured by me; **[S]** sourced from the installed package source/metadata (pydantic-ai-slim 2.74.0, pydantic-ai-harness 0.74.0, PyPI JSON) read in a throwaway venv. I did not read the hosted docs site pages line by line; docs URLs below are from package metadata.

## 0. Naming gotcha

- **[S]** PyPI `pydantic-harness` 0.1.1 is *Deprecated: renamed to `pydantic-ai-harness`* (Development Status: Inactive). The live package is `pydantic-ai-harness` (0.74.0, Alpha; versions track pydantic-ai; docs https://pydantic.dev/docs/ai/harness/, source https://github.com/pydantic/pydantic-ai).
- **[M]** Installing the old name pulls a stale `pydantic-ai-harness 0.1.2`; `pip install -U pydantic-ai-harness` was needed. pycode must depend on `pydantic-ai-harness`.
- **[S]** `pydantic-ai-harness` requires `pydantic-ai-slim==<same version>` (exact pin) plus `genai-prices`, `httpx2`. Both move in lockstep.
- **[S]** Pydantic AI is now V2: old names removed (e.g. `MCPServerStdio` raises ImportError; use `MCPToolset`). Old tutorials are wrong.

## 1. What pydantic-ai-slim gives us

All **[S]** unless noted.

- **Agent loop**: `Agent`, `run`, `run_sync`, `run_stream`, `run_stream_events`, `iter` (node-by-node graph iteration, built on pydantic-graph).
- **Tools**: `@agent.tool` / `tool_plain`, `Toolset`s, schema from type hints/docstrings, retries (`ModelRetry`), deferred tools / human approval (`DeferredToolRequests`, `DeferredToolResults`), tool search, prepare_tools, prefix_tools.
- **Hooks**: `Hooks` capability with decorators (`hooks.on.before_model_request` etc.). Lifecycle points in `AbstractCapability`: `before/after/wrap/on_*_error` for run, node_run, model_request, tool_validate, tool_execute, output_validate, output_process; plus `on_event`, `wrap_run_event_stream`. This is richer than Claude-Code-style PreToolUse/PostToolUse; it can rewrite args, results, requests.
- **Capabilities** (composable bundles of tools+hooks+instructions): thinking, web_search/web_fetch (provider-native or local fallback), model_fallback, retry_on_model_errors, process_history, caching, instrumentation, local_workspace, thread_executor, request_input, citations.
- **Streaming**: text deltas, tool-call events, `event_stream_handler`, structured-output streaming. Event types in `pydantic_ai.messages`.
- **Models/providers**: OpenAI, Anthropic, Google, Bedrock, Groq, Mistral, Cohere, OpenRouter, xAI, Ollama, etc.; `TestModel`/`FunctionModel` for tests; `FallbackModel`; batch models.
- **MCP**: client via `MCPToolset` (extra `mcp` -> `fastmcp-slim[client]`); also MCP sampling model. No MCP *server* needed by us.
- **Durability**: `pydantic_ai.durable_exec.{temporal,dbos,prefect}` capabilities (each needs its extra and an external engine/service).
- **Conversation state**: message history is plain serializable objects; `conversation.py`/`conversation_store.py` exist.
- **Context/history management**: history processors; token counting per model.
- **Observability**: OpenTelemetry/Logfire instrumentation (opt-in).
- **Built-in CLI**: `pydantic_ai._cli` / `python -m pydantic_ai` (extra `cli`: prompt-toolkit, rich, pyperclip, argcomplete, pyyaml). Chat REPL, not a coding agent. Also `web`/`ui`/`ag-ui` extras (not wanted).

## 2. What pydantic-ai-harness gives us

All **[S]** (module layout and docstrings of 0.74.0; ~130 sub-packages). Most are irrelevant to a lightweight local coding agent (sandbox backends: e2b, modal, daytona, k8s, docker...; integrations: slack, notion, linear, github, posthog...; browsers; media). Relevant ones:

| Need | Harness module | Notes |
|---|---|---|
| File tools | `file_system.FileSystem` | read_file, write_file, edit_file, list_directory, search_files, find_files, create_directory, file_info, list_files, grep. Bounded, emits events (diffs). Needs a workspace capability (`LocalWorkspace('.')`), else run fails (**[M]**). |
| Shell | `shell.Shell` | run_command, start_command, check_command, stop_command, shell; background jobs, limits, policy, PowerShell support. |
| Permissions | `permissions.Permissions` | modes, allow/ask/deny rules for tools and shell commands, remembered approvals, approver callback. |
| Subagents | `sub_agents.SubAgents` | Delegate to named child agents; task control, background tasks, remote agents, model-created agents. |
| Planning | `planning.Planning` | model-owned plan/todo tool; in-memory, Postgres, Redis stores. |
| Compaction | `compaction.*` | ClearToolResults, CompactOnRequest, ClampOversizedMessages, context-window resolution. |
| Repo context | `repo_context.RepoContext` | discovers/loads AGENTS.md / CLAUDE.md-style files. |
| Skills | `skills.Skills` | Agent Skill (SKILL.md) loading; needs pyyaml. |
| Memory | `memory.*` | persistent notebook + memory files. |
| Safety rails | `detect_loops`, `tool_budgets`, `tool_output_limits`, `overflowing_tool_output`, `spend_limits`, `require_verification`, `report_stale_files`, `wrap_up_at_limits`, `system_reminders` | Cheap guards for a coding loop. |
| Durability | `step_persistence.StepPersistence` | Append-only event log, continuable snapshots, tool-effect ledger; `FileStepStore`, `InMemoryStepStore`; Postgres/Mongo optional. Gives resume/fork without Temporal. |
| Other | `code_mode`, `coder`, `dynamic_workflow`, `conversation_search`, `ask_user`, `goal` | Not evaluated in depth. |

**[S]** Harness is "Alpha"; sub-packages are being renamed (`filesystem` -> `file_system`, `subagents` -> `sub_agents` emit `HarnessDeprecationWarning`). Expect churn; pin exact versions.

## 3. Footprint (measured) [M]

Machine: x86_64 Linux, 16 cores, Python 3.12.14, venv via uv, warm bytecode cache, `python -I`, median of 7 runs, `/usr/bin/time` max RSS. "Wall" includes imports plus one `run_sync` against `TestModel` (no network). Script: probes in the scratchpad venv (`probes/*.py`).

| Config | Wall (s) | Peak RSS (MB) |
|---|---|---|
| bare `python -I` | 0.01 | 11 |
| `pydantic-ai-slim` only, Agent + 1 tool | 0.51 | 64 |
| + `anthropic` provider/model import | 1.21 | 109 |
| + `mcp` extra, `MCPToolset` import | 1.78 | 147 |
| + harness (`FileSystem`, `Shell`, `SubAgents`, `Permissions`, `ClearToolResults` imported; 4 capabilities active) | 2.08 | 157 |

Other numbers **[M]**:
- Modules loaded: 685 (slim alone), 4880 (full harness config).
- Install size of venv site-packages: 139 MB total (pydantic_ai 18 MB, pydantic_ai_harness 9.9 MB, anthropic SDK 36 MB, pydantic-core 5 MB, fastmcp 5 MB). 56 packages with `slim[anthropic,mcp]` + harness.
- `-X importtime`: `pydantic_ai.models.anthropic` ~0.60 s cumulative (anthropic SDK ~0.57 s), `pydantic_ai.mcp` ~0.51 s (fastmcp client ~0.48 s), `pydantic_ai_harness.sub_agents` ~0.12 s, `file_system` ~0.02 s. Pydantic-ai core ~0.4 s.
- First real use prints a startup banner to stdout (`agent: ... observability: off ...`); suppress with `PYDANTIC_AI_NO_BANNER=1` (**[M]** seen; var name from banner text). A CLI must set it.

Reading: a "cold start under 100 ms" CLI is not possible with these deps; ~2 s to first prompt and ~160 MB RSS for the full stack. Largest levers: lazy-import the model provider and MCP (only when used), import only the harness modules used. Not measured: real network call overhead, memory after a long conversation, Windows, cold (no pyc) start.

## 4. Gaps we fill ourselves

Inferred from the above (**[S]** for what exists; the gap list is judgment):

1. **The CLI/TUI itself**: prompt input, slash commands, rendering of streamed tokens/tool calls/diffs, interrupt (Ctrl-C) handling, config, session picker. pydantic-ai's `cli` is a basic chat REPL; harness has no terminal UI. (Pick rich/prompt-toolkit ourselves, or a lighter option.)
2. **Approval UX**: `Permissions` offers an approver callback; the interactive prompt, "always allow" persistence, and policy file format are ours.
3. **Session storage/resume UX**: `StepPersistence` + `FileStepStore` give the mechanism; naming sessions, listing, resuming from CLI are ours.
4. **System prompt and coding-agent tuning**: harness gives tools, not a tuned prompt or evals. Ours.
5. **Startup-time discipline**: lazy imports, single provider, no banner, avoid pulling `logfire`/`otel`. Ours.
6. **Config and secrets**: model/provider selection, API keys, per-project settings.
7. **Git integration** (diff/checkpoint/undo): not seen in harness; confirm.
8. **Sandboxing**: Shell has policy/limits; OS-level isolation (bubblewrap sandbox exists in harness as `bubblewrap_sandbox`, not evaluated) is a choice to make.
9. **Version churn insurance**: exact pins, thin adapter layer over harness names, smoke tests on upgrade.
10. **Subagent UX**: surfacing child progress in the terminal (events exist: `ChildMessageEvent`, `DelegationFinishedEvent`).

## 5. Open questions for follow-ups

- Does the install pull anything undesirable at the `slim[anthropic]` level only (no mcp)? Measured above as 109 MB RSS.
- Which hosted-docs claims differ from installed source? Not checked.
- A real tool-call loop against a live model (latency, RAM growth) was not measured.
