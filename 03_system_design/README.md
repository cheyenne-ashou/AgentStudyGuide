# System Design for Agentic AI (Week 3–4)

The four components every system design interviewer expects you to know.

## Architecture

```
User Request
     ↓
[ API / Gateway ]
     ↓
[ Orchestrator ]  ←→  [ Tool Registry ]
     ↓                       ↓
[ LLM Gateway ]        [ Tool Executors ]
     ↓
[ Memory Layer ]
     ↓
Response
```

## Files

| File | Pattern | Key concept |
|---|---|---|
| `orchestrator.py` | Orchestrator | Routes tasks to specialized agents |
| `llm_gateway.py` | Gateway + Fallback | Unified LLM interface, retry, model fallback |
| `tool_registry.py` | Central Registry | Discoverability, versioning, metadata |
| `observability.py` | Tracing | Step-level logs, timing, agent spans |

## Key Design Decisions

### Stateless vs Stateful Agents
- **Stateless**: Each invocation is independent. Easy to scale horizontally.
  State lives in the request payload + external storage.
- **Stateful**: Agent holds conversation state in memory. Simpler code,
  harder to scale. Good for development.

### Orchestrator vs Swarm
- **Orchestrator**: Central controller routes tasks. Easy to reason about,
  single point of failure, less parallelism.
- **Swarm**: Agents self-organize, no central control. More parallelism,
  harder to debug.

### Tool Registry Benefits
- Single place to see what tools exist
- Easy to add/remove/version tools without touching agent code
- Enables dynamic tool discovery by the LLM
- Central place for access control and rate limiting per tool

## Scaling Checklist (for system design interviews)

When asked "how would you scale this?":

1. **Stateless agent workers** — horizontally scalable, state in Redis/DB
2. **Async tool execution** — parallel tool calls reduce total latency
3. **Response caching** — cache identical queries (exact + semantic)
4. **Embedding caching** — pre-compute embeddings for static knowledge bases
5. **Rate limiting per tool** — prevent runaway agents from hammering APIs
6. **Circuit breakers** — stop calling a failing tool immediately
7. **Observability** — you can't scale what you can't measure
