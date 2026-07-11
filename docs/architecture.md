# Architecture

## Scope

Agent Security Dojo is an educational, local simulation for evaluating indirect prompt injection in tool-using LLM agents. It has no web service, database, frontend, or real email, calendar, or drive integration. The optional OpenRouter client is not used by the default deterministic planner.

## Execution Path

`app.main` and `app.evaluation.evaluator` create a `Workspace` from seeded Pydantic state. `AgentExecutor` invokes the LangGraph graph in `app.agent.graph`; its executable node calls the deterministic planner in `app.agent.planner`.

The planner performs reads and writes through `ToolRuntime`. The runtime creates a `ToolCall` log entry for every attempt, applies the task allowlist in secure mode, and calls `guard_tool_call` before invoking the matching `Workspace` method.

## Component Responsibilities

| Area | Responsibility |
| --- | --- |
| `app/environment` | In-memory workspace state, seeded fixtures, and simulated side effects. |
| `app/tools` | Runtime entry point and thin domain wrappers for workspace tools. |
| `app/agent` | Graph shell, deterministic plan, executor, and prompts. |
| `app/defenses` | Tool allowlists, injection detection, untrusted-output handling, and write-call guard. |
| `app/attacks` | Controlled payloads and insertion into simulated untrusted data. |
| `app/evaluation` | Legitimate tasks, scenario execution, checks, and aggregate metrics. |
| `app/schemas` | Pydantic contracts shared across the application. |
| `app/llm` | Optional OpenRouter client. |

## Security Model

`vulnerable_mode` permits the deterministic simulation to follow selected malicious payloads so the benchmark can demonstrate attack impact. `secure_mode` limits tools by task, marks third-party content as untrusted, detects rule-based injection indicators, preserves the original task around untrusted output, and checks write calls for provenance, authorized recipients, sensitive markers, and attack objectives.

The principal security boundaries are `app.tools.runtime.ToolRuntime`, `app.defenses.tool_filter`, `app.defenses.tool_call_guard`, `app.defenses.injection_detector`, `app.defenses.delimiters`, and `app.defenses.prompt_sandwich`.

## Evaluation Model

`EvaluationEngine` runs each task first on clean seeded state and then on a separate attacked copy. It records utility, attack success, allowed/blocked calls, and false-positive/false-negative counters in `EvaluationResult`. `aggregate_metrics` derives the reported rates from those results.

## Current Boundaries

- Scenario data is currently defined in Python; `data/benign`, `data/malicious`, and `data/scenarios` are placeholders.
- The graph's named stages are pass-through nodes except for `execute_tool`; the planner currently owns behavior.
- No linter, formatter, type checker, or pre-commit command is configured. Do not claim one exists without adding it deliberately.
