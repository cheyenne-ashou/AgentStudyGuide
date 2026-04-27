# Project 1: Tool-Using Agent

A complete agent demonstrating all the core patterns from sections 2 and 4.

## What it demonstrates

- **Tool use**: 4 tools (calculator, datetime, web search, note-taking)
- **Memory**: note-taking tool acts as working memory within a run
- **Retries**: tenacity backoff on RateLimitError
- **Loop control**: MAX_STEPS = 15 prevents runaway execution
- **Logging**: every step logged with structlog

## Run it

```bash
python 05_projects/project1_tool_agent/agent.py
```

## Architecture

```
User Task
    ↓
agent.py — ReAct loop
    ↓
_call_claude() — with tenacity retry
    ↓
Claude API — returns tool_use or end_turn
    ↓
execute_tool() — routes to tool implementation
    ↓
tools.py — calculator / datetime / search / notes
```

## Files

- `agent.py` — the main ReAct loop with retries and logging
- `tools.py` — tool schemas + implementations

## Key patterns used

1. `cached_system()` — prompt caching on the system prompt (saves tokens on long runs)
2. `@retry` decorator — automatic backoff on rate limit errors
3. `MAX_STEPS` — hard limit to prevent infinite loops
4. `structlog` — every step emits a structured log event

## Extending this project

- Add a real web search tool (Brave Search, Tavily, SerpAPI)
- Connect to ChromaDB for persistent memory between runs
- Add a `code_execution` tool (use `subprocess` safely)
- Track token usage and add a budget limit
