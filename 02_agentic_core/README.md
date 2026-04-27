# Agentic Core (Week 2–3)

The three pillars of every agent: tools, memory, and control flow.

## 2.1 Tool Use

```
tool_registry.py    → Tool ABC + ToolRegistry pattern
sample_tools.py     → concrete tools: calculator, datetime, mock search
function_calling.py → end-to-end Claude tool_use block demo
```

**Key interview question:** *"How does function calling work?"*

1. Define tools as JSON schemas in the API request
2. Model returns a `tool_use` content block instead of text
3. Your code executes the tool and returns a `tool_result`
4. Model receives the result and continues reasoning

## 2.2 Memory Types

```
short_term.py  → context window manager (rolling + summarization)
long_term.py   → ChromaDB vector persistence
episodic.py    → JSON log of past runs, queryable
semantic.py    → key-value fact store with TTL
```

**Key interview question:** *"How would you design memory for an agent?"*

| Type | Storage | Lifetime | Use case |
|---|---|---|---|
| Short-term | Context window | Current session | Conversation history |
| Long-term | Vector DB | Persistent | Cross-session knowledge |
| Episodic | File/DB | Persistent | "What did I do last time?" |
| Semantic | Key-value | Persistent | User preferences, facts |

## 2.3 Agent Patterns

```
react_agent.py       → Thought→Action→Observation loop (THE core pattern)
plan_and_execute.py  → make a plan, then execute steps
human_in_loop.py     → approval gates and feedback injection
```

**Most important file in this section:** `react_agent.py`

All modern agent frameworks (LangChain, LangGraph, AutoGen) are variations
on the ReAct loop. Understand this and you understand the rest.

### ReAct Loop Anatomy:
```
User Query
    ↓
[Claude thinks] → Thought: "I need to look up X"
    ↓
[Claude acts]   → tool_use: web_search(query="X")
    ↓
[Your code]     → execute tool, get result
    ↓
[Claude observes] → "The result says Y, now I can answer"
    ↓
[Claude responds] → Final answer (stop_reason = "end_turn")
```
