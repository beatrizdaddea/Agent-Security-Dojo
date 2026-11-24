# Architecture

## Scope

Agent Security Dojo evaluates indirect prompt injection with an in-memory inbox, calendar, and drive. Tool effects stay inside `Workspace`. In LLM mode the planner sends synthetic data to OpenRouter and receives structured assistant turns.

## Graph execution

1. `load_user_task` snapshots the caller-supplied `UserTask` and initializes the runtime and conversation.
2. `select_tools` derives function schemas from the simulated tool registry and the chosen security profile.
3. `plan_next_action` uses either the fixed mock planner or `OpenRouterClient`. The mock planner gets the fixture label to replay a fixed action when the fixture is observed. The LLM gets the user instruction, tool catalog, and ordinary conversation messages.
4. `tool_call_guard` asks `ToolRuntime` to validate and authorize one request. The runtime rejects unknown tools and invalid arguments in both profiles.
5. `execute_tool` consumes the pending authorization, logs the attempt, and dispatches eligible calls to `Workspace`. Failed lookup and policy errors return as tool results.
6. `inspect_tool_output` stores the observation, records heuristic signals, and appends the tool message for LLM planning. The runtime marks observations as tainted from workspace metadata and records their IDs on later attempts. Calls in the same model turn are processed in order.
7. `final_answer` handles completion or an execution limit. `evaluate_result` applies the legitimate task check and records run telemetry.

The graph bounds planner turns and tool requests. In defensive mode, the runtime checks authorization against the original task snapshot. That snapshot supplies the allowed document scope, calendar date, recipients, or exact event parameters. The model cannot supply its own authorization or provenance fields. One successful write consumes the defensive run's write allowance.

## Evaluation

`app.evaluation.evaluator` clones each seeded workspace before injecting a fixture into the attacked copy. It scores legitimate utility, checks the targeted effect against the resulting workspace, and labels calls against intended task behavior. Labels are independent of tool policy decisions and heuristic signals. The attack fixtures live under `app/attacks` and the task fixtures live under `app/evaluation`. The `data/` directories are placeholders.

The benchmark artifacts contain counts, denial codes, model metadata, and usage summaries. Raw messages, tool arguments, canaries, and final answer text stay out of the artifacts. `mock` and `llm` runs use separate output files.
