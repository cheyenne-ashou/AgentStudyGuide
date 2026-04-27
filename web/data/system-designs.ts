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
│  Agent Orchestrator (ReAct loop, max_steps, timeouts)            │
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
│   │               ├── Short-term: Redis (messages, TTL)         │
│   │               └── Long-term: Pinecone (user facts)          │
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
        name: 'Agent Orchestrator',
        description:
          'Manages the ReAct loop. Enforces max_steps=15, wall-clock timeout=60s, and detects stuck loops. Handles retry escalation.',
      },
      {
        name: 'LLM Gateway',
        description:
          'Unified interface. Handles model fallback (Sonnet → Haiku), exponential backoff on rate limits, and token usage tracking.',
      },
      {
        name: 'Tool Registry',
        description:
          'Centralized, versioned. Each tool has a schema, description, category, and access control tags. Agents discover tools dynamically.',
      },
      {
        name: 'Memory Layer',
        description:
          'Redis for in-flight conversation state (expires with session). Pinecone for long-term semantic memory retrieved on each turn.',
      },
      {
        name: 'Observability',
        description:
          'OpenTelemetry spans for every agent step. Send to Langfuse or Jaeger. Track: step number, tool, inputs, outputs, latency, tokens.',
      },
    ],
    scaling: [
      'Stateless orchestrator workers → horizontal scaling behind a load balancer (ECS/K8s)',
      'Redis for all session state → any worker can handle any user request',
      'Async parallel tool calls → run independent tools concurrently, not serially',
      'Embedding cache (Redis, TTL=1h) → avoid re-embedding the same documents',
      'Semantic response cache → return cached answer for repeated identical queries',
      'LLM routing → simple queries to Haiku (fast/cheap), complex to Sonnet',
      'Batch API for non-realtime tasks (10× cheaper than realtime)',
    ],
    keyDecisions: [
      'Stateless workers: all state in Redis, not in process memory',
      'LLM Gateway abstracts providers: swap models without touching agent code',
      'Tool Registry with access control: tools can be restricted per user tier',
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
    title: 'Multi-Agent Workflow',
    subtitle:
      'Design a multi-agent system that can research a topic, analyze data, and write a report.',
    diagram: `┌─────────────────────────────────────────────────────────────────┐
│                   MULTI-AGENT PIPELINE                           │
│                                                                   │
│  User Task: "Research and report on X"                           │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐                                                │
│  │   PLANNER    │ ← Decomposes task into JSON step plan          │
│  │  (Claude)    │   Each step: description + tool + expected     │
│  └──────┬───────┘                                                │
│         │ Structured JSON Plan                                   │
│         ▼                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  RESEARCHER  │  │   ANALYZER   │  │    WRITER    │           │
│  │ (web_search  │  │ (calculator  │  │ (synthesis)  │           │
│  │  + RAG)      │  │  + code)     │  │              │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                  │                   │
│         └─────────────────┼──────────────────┘                   │
│                     Step Results (JSON)                          │
│                           │                                      │
│                   ┌───────┴───────┐                              │
│                   │   VALIDATOR   │ ← Score 0-1 per step         │
│                   │              │   < 0.7: retry execution      │
│                   └───────┬───────┘   > 3 retries: human         │
│                           │                                      │
│                   ┌───────┴───────┐                              │
│                   │  SYNTHESIZER  │ ← Final answer               │
│                   └───────────────┘                              │
│                                                                   │
│  Shared: Tool Registry ∙ Memory ∙ Observability ∙ Loop Control   │
└─────────────────────────────────────────────────────────────────┘`,
    components: [
      {
        name: 'Planner',
        description:
          'Receives the task and outputs a structured JSON plan (Pydantic-validated). Each step specifies: description, tool to use, and expected output.',
      },
      {
        name: 'Researcher',
        description:
          'Specialist agent for information gathering. Uses web_search and RAG retrieval. Passes results to the next step as structured context.',
      },
      {
        name: 'Analyzer',
        description:
          'Specialist for computation: calculator, code execution, data processing. Receives research results as input context.',
      },
      {
        name: 'Writer',
        description:
          'Synthesizes all prior results into a coherent output. No tool use — pure generation from accumulated context.',
      },
      {
        name: 'Validator',
        description:
          'Quality gate: scores each step 0-1. Overall score < 0.7 → request re-execution. After 3 retries → flag for human review.',
      },
      {
        name: 'Synthesizer',
        description:
          'Final agent that produces the user-facing answer by combining all validated step results. Applies formatting and structure.',
      },
    ],
    scaling: [
      'Parallelize independent plan steps (researcher + analyzer can run concurrently)',
      'Stateless agents → each agent call is a separate, horizontally-scalable request',
      'Event-driven: use SQS/Kafka to decouple steps — agents publish results, next agent subscribes',
      'Validator as async sidecar: validate in parallel with synthesizer, only block on failures',
      'Cost optimization: use Haiku for Planner/Validator; Sonnet only for Researcher/Writer',
    ],
    keyDecisions: [
      'Orchestrator pattern (vs swarm): more predictable, easier to debug, explicit control flow',
      'Structured JSON between agents: Pydantic-validated — no free-form hand-offs',
      'Validator is the quality gate: prevents bad results from silently propagating',
      'Shared observability: all agents emit to the same trace, giving a full picture of one run',
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
    '[ ] Retry with exponential backoff (tenacity, 3 attempts)',
    '[ ] Model fallback chain (primary → cheaper fallback)',
    '[ ] Max iterations + wall-clock timeout',
    '[ ] Input guardrails (sanitize, validate schema)',
    '[ ] Output guardrails (validate response schema)',
    '[ ] Human escalation path (confidence threshold)',
  ],
}
