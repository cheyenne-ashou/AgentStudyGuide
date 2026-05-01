# Agentic Core (Week 2–3)

The three pillars of every agent: tools, memory, and control flow.

## 2.1 Tool Use

```
tool_registry.py    → Tool ABC + ToolRegistry pattern
sample_tools.py     → concrete tools: calculator, datetime, mock search
function_calling.py → end-to-end Claude tool_use block demo
```

**Key interview question:** *"How does function calling work in LangGraph?"*

1. Decorate Python functions with `@tool` (docstring → description, signature → schema)
2. Call `llm.bind_tools(tools)` to attach schemas to the model
3. LLM returns an `AIMessage` with `.tool_calls` populated (non-empty = wants to call a tool)
4. `ToolNode` executes all tool calls and returns `ToolMessages`
5. LLM receives the results and continues reasoning

## 2.2 Memory Types

```
short_term.py  → MemorySaver checkpointer + thread_id (rolling/summarization concepts)
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

### ReAct Loop Anatomy (as LangGraph StateGraph):
```
User Query → AgentState["messages"]
    ↓
call_model node   → LLM produces AIMessage (with or without tool_calls)
    ↓
should_continue   → if tool_calls: → "tools" node; else: → END
    ↓
ToolNode          → executes tool calls, returns ToolMessages
    ↓
(edge back to call_model — loop continues)
    ↓
END               → state["messages"][-1].content = final answer
```

One-liner shorthand: `agent = create_react_agent(get_llm(), tools=[...])`
