# Project 3: Multi-Agent Workflow

A complete Planner → Executor → Validator pipeline — the most advanced pattern in this repo.

## Run it

```bash
python 05_projects/project3_multi_agent/workflow.py
```

## Architecture

```
User Task
    ↓
[Planner Agent]
  Claude decomposes task into N steps
  Each step: description + tool + expected output
    ↓
[Executor Agent] × N steps
  Runs each step with the specified tool
  Passes results from prior steps as context
    ↓
[Validator Agent]
  Scores each step result (0.0 – 1.0)
  If overall score < 0.7: retry execution
  If 3 retries fail: escalate to human
    ↓
[Synthesizer]
  Combines all step results into final answer
```

## Files

| File | Agent | Responsibility |
|---|---|---|
| `planner.py` | Planner | Decompose task → structured JSON plan |
| `executor.py` | Executor | Run each step, return results |
| `validator.py` | Validator | Score results, approve or request retry |
| `workflow.py` | Orchestrator | Coordinate all three agents |

## Patterns demonstrated

1. **Structured outputs** — every agent exchanges JSON (Pydantic-validated)
2. **Context passing** — executor receives results from prior steps
3. **Retry logic** — workflow retries execution if validator score < threshold
4. **Human escalation** — validator flags for human review on low confidence
5. **Observability** — every phase logged with structlog
6. **Prompt caching** — system prompts cached across retries

## This is what LangGraph, AutoGen, and CrewAI abstract

The patterns here map directly to framework concepts:
- **Planner** = task decomposition node
- **Executor** = action node with tool calling
- **Validator** = conditional edge (score threshold)
- **Workflow** = state machine / graph
