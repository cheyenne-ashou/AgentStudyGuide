export type SystemDesign = {
  id: string
  title: string
  subtitle: string
  diagram: string
  components: { name: string; description: string }[]
  scaling: string[]
  keyDecisions: string[]
}

export const systemDesigns: SystemDesign[] = [
  {
    id: 'ai-assistant',
    title: 'AI Assistant with Tools',
    subtitle: 'Design an AI assistant that can search the web, run code, and answer questions.',
    diagram: `┌─────────────────────────────────────────────────────────────────┐
│                     AI ASSISTANT SYSTEM                          │
│                                                                   │
│  User                                                            │
│   │                                                              │
│   ▼                                                              │
│  API Gateway ──── Auth / Rate Limiting / Input Validation        │
│   │                                                              │
│   ▼                                                              │
│  LangGraph StateGraph (ReAct: agent ↔ ToolNode, recursion_limit) │
│   │         │                                                    │
│   │         ├──► Resilient LLM ── claude-sonnet-4-6             │
│   │         │    (.with_retry() + .with_fallbacks([haiku]))      │
│   │         │                                                    │
│   │         ├──► ToolNode (@tool-decorated functions)            │
│   │         │     ├── web_search ──── Brave/Tavily API           │
│   │         │     ├── code_exec ───── Docker sandbox             │
│   │         │     └── calculator ─── inline Python eval          │
│   │         │                                                    │
│   │         └──► Memory Layer                                    │
│   │               ├── MemorySaver/RedisSaver (thread_id)        │
│   │               └── Pinecone (long-term semantic memory)      │
│   │                                                              │
│   ▼                                                              │
│  Response ──── Streaming (SSE / WebSocket)                       │
│                                                                   │
│  Observability: OpenTelemetry ──► Langfuse / Jaeger              │
└─────────────────────────────────────────────────────────────────┘`,
    components: [
      {
        name: 'API Gateway',
        description:
          'Auth, rate limiting per user/tier, input validation (Pydantic guardrails), request logging.',
      },
      {
        name: 'LangGraph StateGraph',
        description:
          'create_react_agent() or custom StateGraph. Manages the ReAct loop (agent node ↔ ToolNode). recursion_limit enforces max_steps. MemorySaver checkpointer preserves state per thread_id.',
      },
      {
        name: 'Resilient LLM',
        description:
          'ChatAnthropic with .with_retry(stop_after_attempt=3) + .with_fallbacks([fast_llm]). Replaces tenacity decorators and custom fallback chains. Works on any Runnable.',
      },
      {
        name: 'ToolNode (@tool)',
        description:
          'Pre-built LangGraph node. Python functions decorated with @tool — docstrings become descriptions, signatures become JSON schemas. Replaces hand-written tool dispatch loops.',
      },
      {
        name: 'Memory Layer',
        description:
          'MemorySaver (dev) or RedisSaver (prod) keyed by thread_id for conversation persistence. Pinecone for long-term semantic memory retrieved on each turn.',
      },
      {
        name: 'Observability',
        description:
          'OpenTelemetry spans for every graph node. Send to Langfuse or Jaeger. Track: node name, inputs, outputs, latency, token counts.',
      },
    ],
    scaling: [
      'Stateless StateGraph workers → horizontal scaling (MemorySaver → RedisSaver for multi-worker)',
      'RedisSaver for all session state → any worker can handle any user request',
      'Async parallel tool calls → ToolNode can execute tool_calls concurrently',
      'Embedding cache (Redis, TTL=1h) → avoid re-embedding the same documents',
      'Semantic response cache → return cached answer for repeated identical queries',
      'LLM routing → simple queries to Haiku (.with_fallbacks()), complex to Sonnet',
      'Batch API for non-realtime tasks (10× cheaper than realtime)',
    ],
    keyDecisions: [
      'StateGraph edges ARE the control flow: conditional edges replace if/elif routing code',
      'MemorySaver thread_id = session identifier: one thread_id per conversation',
      '.with_retry() + .with_fallbacks() on the LLM: composable resiliency without decorators',
      'ToolNode replaces hand-written tool dispatch: add @tool, pass to ToolNode, done',
      'Streaming via SSE: return tokens as generated for better perceived latency',
    ],
  },
  {
    id: 'rag-system',
    title: 'RAG System',
    subtitle: "Design a document Q&A system for a company's internal knowledge base.",
    diagram: `┌─────────────────────────────────────────────────────────────────┐
│                         RAG SYSTEM                               │
│                                                                   │
│  INGESTION (offline)                QUERY (online, per request)  │
│  ───────────────────               ──────────────────────────── │
│                                                                   │
│  Documents (.txt/.pdf/.md)          User Question                │
│       │                                  │                       │
│       ▼                                  ▼                       │
│  Chunker                           Embed Query                   │
│  (80w, 10-15% overlap)             (voyage-3 / ada-002)         │
│       │                                  │                       │
│       ▼                             ┌────┴────┐                  │
│  Embedder (batch)                   │         │                  │
│       │                          Vector    BM25                  │
│       ▼                          Search    Search                │
│  Vector DB                          │         │                  │
│  (Pinecone / pgvector)              └────┬────┘                  │
│       │                               RRF Fusion                 │
│       └───────────────────────────►      │                       │
│                                     Top-K Chunks                 │
│                                          │                       │
│                                     Augment Prompt               │
│                                          │                       │
│                                     LLM Generate                 │
│                                          │                       │
│                                    Answer + Sources              │
└─────────────────────────────────────────────────────────────────┘`,
    components: [
      {
        name: 'Chunker',
        description:
          'Splits documents into 80-word chunks with 10-15% overlap (sliding window). Sentence-aware splitting preserves semantic units.',
      },
      {
        name: 'Embedder',
        description:
          'Batch-encodes chunks using voyage-3 or text-embedding-ada-002. Pre-computes and caches all embeddings at ingestion time.',
      },
      {
        name: 'Vector DB',
        description:
          'Stores embeddings and metadata. Options: Pinecone (managed, fast), pgvector (Postgres extension), ChromaDB (local dev).',
      },
      {
        name: 'BM25 Index',
        description:
          'Keyword search index over raw document text. Built in-memory or via Elasticsearch. Fast, no ML needed, handles exact terms.',
      },
      {
        name: 'RRF Fusion',
        description:
          'Merges BM25 and vector ranked lists: score(d) = Σ 1/(60 + rank). Documents appearing in both lists are boosted.',
      },
      {
        name: 'LLM Generator',
        description:
          'Receives top-k chunks as context. System prompt: "Answer ONLY from the provided context. Cite your sources." Prompt-cached system prompt.',
      },
    ],
    scaling: [
      'Pre-compute all embeddings at ingestion — never re-embed at query time',
      'Cache query→chunks pairs (semantic cache, Redis, TTL=10min) for repeated questions',
      'Run BM25 and vector search in parallel (async), not sequentially',
      'Cross-encoder re-ranker (optional): re-score top-20 before selecting top-5 for higher precision',
      'Shard vector DB by document source for multi-tenant deployments',
      'Async ingestion pipeline: new documents ingested via queue, not blocking query path',
    ],
    keyDecisions: [
      'Chunk size 80 words: balance context preservation vs retrieval precision',
      'Hybrid search: BM25 handles exact terms, vector handles synonyms — combined beats either',
      'RRF over score normalization: simpler, no calibration needed, consistently works well',
      'Source citations: every answer includes which documents were used — essential for trust',
    ],
  },
  {
    id: 'multi-agent',
    title: 'Multi-Agent Workflow (LangGraph Supervisor)',
    subtitle:
      'Design a multi-agent system that can research a topic, analyze data, and write a report.',
    diagram: `┌─────────────────────────────────────────────────────────────────┐
│             MULTI-AGENT PIPELINE (LangGraph StateGraph)          │
│                                                                   │
│  User Task: "Research and report on X"                           │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐                                                │
│  │   PLANNER    │ ← .with_structured_output(TaskPlan)            │
│  │   (node)     │   TypedDict state: plan, past_steps            │
│  └──────┬───────┘                                                │
│         │ ── conditional edge ──────────────────────────────►    │
│         ▼                                                        │
│  ┌──────────────┐  Command(goto="supervisor") from each          │
│  │  SUPERVISOR  │ ◄──── researcher ──────────────────────────    │
│  │   (node)     │ ◄──── analyzer ────────────────────────────    │
│  │              │ ◄──── writer ──────────────────────────────    │
│  └──────┬───────┘                                                │
│   Command(goto=...)                                              │
│         │                                                        │
│                   ┌───────────────┐                              │
│                   │   VALIDATOR   │ ← .with_structured_output()  │
│                   │   (node)      │   conditional edge:          │
│                   └───────┬───────┘   score<0.7 → executor       │
│                           │           else → synthesizer         │
│                   ┌───────┴───────┐                              │
│                   │  SYNTHESIZER  │ ← LCEL chain → final answer  │
│                   └───────────────┘                              │
│                                                                   │
│  Shared: ToolNode ∙ MemorySaver ∙ Observability ∙ PlanExecuteState│
└─────────────────────────────────────────────────────────────────┘`,
    components: [
      {
        name: 'Planner (node)',
        description:
          '.with_structured_output(TaskPlan) — no JSON extraction needed. Populates PlanExecuteState["plan"] with typed TaskStep objects.',
      },
      {
        name: 'Supervisor (node)',
        description:
          'Routes tasks to specialists using Command(goto="researcher"|"analyzer"|"writer"). Command(goto=END) when done. Replaces hand-written if/elif routing.',
      },
      {
        name: 'Specialist nodes (researcher, analyzer, writer)',
        description:
          'Each is a LangGraph node that does one thing. Returns Command(goto="supervisor") with updated messages. Uses ToolNode for tool execution.',
      },
      {
        name: 'Validator (node)',
        description:
          '.with_structured_output(ValidationReport). Conditional edge: score < 0.7 → executor; max retries exceeded → synthesizer.',
      },
      {
        name: 'Synthesizer (node)',
        description:
          'LCEL chain: prompt | llm | StrOutputParser(). Writes final answer to PlanExecuteState["response"]. Leads to END.',
      },
      {
        name: 'MemorySaver checkpointer',
        description:
          'Persists PlanExecuteState after every node. Crash mid-run? Resume from last checkpoint. Switch to RedisSaver for multi-worker deployments.',
      },
    ],
    scaling: [
      'Parallelize independent plan steps: run researcher + analyzer as concurrent subgraphs',
      'Stateless graph workers → RedisSaver for multi-worker session persistence',
      'Event-driven: use SQS/Kafka to decouple graph invocations across services',
      'Validator as conditional edge: only adds latency when score is below threshold',
      'Cost optimization: use Haiku for Planner/Validator; Sonnet for Researcher/Writer',
    ],
    keyDecisions: [
      'Supervisor pattern with Command(goto=...): routing is declared in graph edges, not code',
      '.with_structured_output() throughout: Pydantic-validated hand-offs, no JSON parsing',
      'PlanExecuteState with operator.add on past_steps: results accumulate without overwriting',
      'MemorySaver checkpointer: long-running tasks survive crashes without restarting from scratch',
      'Conditional edges on validator: retry logic declared in the graph, not nested if/else',
    ],
  },
]

export const blankTemplate = {
  components: [
    'API / Entry point (auth, rate limiting, validation)',
    'Orchestrator / Workflow engine (loop, max steps, timeout)',
    'LLM Gateway (model routing, fallback, token tracking)',
    'Tool Registry (schemas, versioning, access control)',
    'Memory Layer (short-term: Redis; long-term: vector DB)',
    'Observability (structured tracing, error tracking)',
  ],
  dataFlow: [
    'User Request → [input validation] → [routing/auth]',
    '→ [LLM + tools loop]',
    '→ [output validation] → Response',
  ],
  scaling: [
    '[ ] Stateless workers (horizontal scale, no sticky sessions)',
    '[ ] Caching: embeddings, responses, tool results',
    '[ ] Async tool execution (parallel calls reduce latency)',
    '[ ] Rate limiting per tool and per user',
    '[ ] Circuit breakers on external dependencies',
    '[ ] Queue-based ingestion for non-realtime work',
  ],
  resiliency: [
    '[ ] Retry with exponential backoff (.with_retry(stop_after_attempt=3, wait_exponential_jitter=True))',
    '[ ] Model fallback chain (.with_fallbacks([backup_llm]))',
    '[ ] Max iterations via recursion_limit on the graph',
    '[ ] Input guardrails (sanitize, validate schema)',
    '[ ] Output guardrails (.with_structured_output() + Pydantic)',
    '[ ] Human escalation via interrupt() + Command(resume=...)',
    '[ ] Checkpointing (MemorySaver / RedisSaver) for crash recovery',
  ],
}
