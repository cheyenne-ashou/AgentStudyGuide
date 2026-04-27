# System Design Templates

Three designs you should be able to sketch in 20 minutes.
For each: know the components, the data flow, and 3 scaling considerations.

---

## Design 1: AI Assistant with Tools

**Prompt:** "Design an AI assistant that can search the web, run code, and answer questions."

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI ASSISTANT SYSTEM                          │
│                                                                   │
│  User                                                            │
│   │                                                              │
│   ▼                                                              │
│  API Gateway ──── Auth / Rate Limiting                           │
│   │                                                              │
│   ▼                                                              │
│  Agent Orchestrator                                              │
│   │         │                                                    │
│   │         ├──► LLM Gateway ──── claude-sonnet-4-6             │
│   │         │         └────────── claude-haiku (fallback)        │
│   │         │                                                    │
│   │         ├──► Tool Registry                                   │
│   │         │     ├── web_search ──── Brave/Tavily API           │
│   │         │     ├── code_exec ───── Docker sandbox             │
│   │         │     └── calculator ─── inline Python eval          │
│   │         │                                                    │
│   │         └──► Memory Layer                                    │
│   │               ├── Short-term: Redis (messages)              │
│   │               └── Long-term: Pinecone (user facts)          │
│   │                                                              │
│   ▼                                                              │
│  Response ──── Streaming (SSE / WebSocket)                       │
│                                                                   │
│  Observability: OpenTelemetry ──► Langfuse / Jaeger              │
└─────────────────────────────────────────────────────────────────┘
```

**Component responsibilities:**
- API Gateway: auth, rate limiting, request validation
- Orchestrator: manages the ReAct loop, enforces max steps
- LLM Gateway: model routing, fallback, retry, token tracking
- Tool Registry: tool schemas, access control, usage metrics
- Memory Layer: context window management + cross-session facts

**Scaling:**
1. Stateless orchestrator workers → horizontal scaling behind load balancer
2. Embed caching → avoid re-embedding the same documents (Redis TTL)
3. Async tool execution → parallel tool calls reduce total latency

---

## Design 2: RAG System

**Prompt:** "Design a document Q&A system for a company's internal knowledge base."

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG SYSTEM                                │
│                                                                   │
│  INGESTION PIPELINE (offline)            QUERY PIPELINE (online) │
│  ────────────────────────────           ─────────────────────── │
│  Documents                              User Question            │
│      │                                       │                   │
│      ▼                                       ▼                   │
│  Chunker                               Embed Query               │
│  (sentence-aware, 80 words)            (voyage-3 / ada-002)      │
│      │                                       │                   │
│      ▼                                   ┌───┴───┐              │
│  Embedder                                │       │               │
│  (batch, cached)                      Vector   BM25             │
│      │                                Search   Search           │
│      ▼                                   │       │               │
│  Vector DB                               └───┬───┘              │
│  (Pinecone / pgvector)                       │                   │
│      │                                    RRF Fusion             │
│      └──────────────────────────────────►    │                   │
│                                          Top-K Chunks            │
│                                              │                   │
│                                          Augment Prompt          │
│                                              │                   │
│                                          LLM Generate            │
│                                              │                   │
│                                         Answer + Sources         │
└─────────────────────────────────────────────────────────────────┘
```

**Key decisions to explain:**
- Chunk size: 80 words with 15-word overlap (balance context vs precision)
- Hybrid search: BM25 catches exact terms; vector catches semantic matches
- Re-ranking: RRF fusion, or cross-encoder re-ranker for higher accuracy
- Source citations: every answer includes which documents were used

**Scaling:**
1. Pre-compute and cache all embeddings (don't re-embed on every query)
2. Cache query→answer pairs for repeated identical questions (semantic cache)
3. Async parallel retrieval: run BM25 and vector search concurrently

---

## Design 3: Multi-Agent System

**Prompt:** "Design a multi-agent system that can research a topic, analyze data, and write a report."

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT PIPELINE                          │
│                                                                   │
│  User Task: "Research and report on X"                           │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐                                                │
│  │   PLANNER    │ ← Decomposes task into steps                   │
│  │  (Claude)    │   Returns structured JSON plan                 │
│  └──────┬───────┘                                                │
│         │ Plan (JSON)                                            │
│         ▼                                                        │
│  ┌──────────────┐   ┌─────────────┐   ┌──────────────┐          │
│  │  RESEARCHER  │   │  ANALYZER   │   │   WRITER     │          │
│  │  (Claude +   │   │  (Claude +  │   │  (Claude)    │          │
│  │  web_search) │   │  calculator)│   │              │          │
│  └──────┬───────┘   └──────┬──────┘   └──────┬───────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │ Results                             │
│                            ▼                                     │
│                   ┌──────────────┐                               │
│                   │  VALIDATOR   │ ← Quality gate                │
│                   │  (Claude)    │   Score ≥ 0.7 → proceed       │
│                   └──────┬───────┘   Score < 0.7 → retry         │
│                          │                                       │
│                          ▼                                       │
│                   ┌──────────────┐                               │
│                   │ SYNTHESIZER  │ ← Combine → final report      │
│                   └──────────────┘                               │
│                                                                   │
│  Shared: Tool Registry, Memory, Observability, Loop Control      │
└─────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- Agents communicate via structured JSON (Pydantic schemas)
- Validator is the quality gate — prevents low-quality output from propagating
- Orchestrator enforces max retries and escalates to human if needed
- All agents share the same tool registry and observability stack

**Scaling:**
1. Parallelize independent steps (researcher + analyzer can run concurrently)
2. Stateless agents → each agent call is independent, horizontally scalable
3. Event-driven: use a message queue (SQS, Kafka) to decouple agent steps

---

## Blank Template

Use this for any system design question:

```
COMPONENTS:
  [ ] User interface / API gateway
  [ ] Orchestrator / workflow engine
  [ ] LLM gateway (with fallback)
  [ ] Tool registry
  [ ] Memory layer (short + long term)
  [ ] Observability

DATA FLOW:
  User Request → [validation] → [routing] → [LLM + tools] → [validation] → Response

SCALING:
  [ ] Stateless workers (horizontal scale)
  [ ] Caching (embeddings, responses, tool results)
  [ ] Async execution (parallel tool calls)
  [ ] Rate limiting per tool / user
  [ ] Circuit breakers on external deps

RESILIENCY:
  [ ] Retry with exponential backoff
  [ ] Model fallback chain
  [ ] Max iterations + timeout
  [ ] Input/output guardrails
  [ ] Human escalation path
```
