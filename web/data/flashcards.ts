export type Category =
  | 'llm'
  | 'rag'
  | 'agent'
  | 'memory'
  | 'resiliency'
  | 'system-design'

export type Flashcard = {
  id: string
  term: string
  definition: string
  why: string
  category: Category
}

export const CATEGORY_LABELS: Record<Category, string> = {
  llm: 'LLM Basics',
  rag: 'RAG & Retrieval',
  agent: 'Agentic Patterns',
  memory: 'Memory',
  resiliency: 'Resiliency',
  'system-design': 'System Design',
}

export const CATEGORY_COLORS: Record<Category, string> = {
  llm: 'bg-blue-900/40 text-blue-300 border-blue-700',
  rag: 'bg-cyan-900/40 text-cyan-300 border-cyan-700',
  agent: 'bg-violet-900/40 text-violet-300 border-violet-700',
  memory: 'bg-emerald-900/40 text-emerald-300 border-emerald-700',
  resiliency: 'bg-orange-900/40 text-orange-300 border-orange-700',
  'system-design': 'bg-pink-900/40 text-pink-300 border-pink-700',
}

export const flashcards: Flashcard[] = [
  // ── LLM Basics ──────────────────────────────────────────────────────────────
  {
    id: 'token',
    term: 'Token',
    definition:
      'A unit of text processed by an LLM — roughly 0.75 words. Models have a fixed limit for total tokens (input + output) per request.',
    why: 'Affects cost, latency, and what fits in a single context window.',
    category: 'llm',
  },
  {
    id: 'context-window',
    term: 'Context Window',
    definition:
      'The maximum number of tokens an LLM can process at once (input + output combined). Claude supports up to 200k tokens.',
    why: 'Determines how much conversation history, documents, or code you can include per call.',
    category: 'llm',
  },
  {
    id: 'temperature',
    term: 'Temperature',
    definition:
      'Controls output randomness. t=0 always picks the highest-probability token (deterministic). t=1.0 samples proportionally — maximally varied.',
    why: 'Use t=0 for tool-calling and extraction; t=0.7 for conversation; t=1 for brainstorming.',
    category: 'llm',
  },
  {
    id: 'hallucination',
    term: 'Hallucination',
    definition:
      'When an LLM generates plausible-sounding but factually incorrect information. Caused by the model optimizing for fluency, not factual accuracy.',
    why: 'The #1 reliability problem in production. RAG, structured outputs, and uncertainty prompting are the main mitigations.',
    category: 'llm',
  },
  {
    id: 'embedding',
    term: 'Embedding',
    definition:
      'A dense vector (list of floats) representation of text that captures semantic meaning. Similar concepts produce similar vectors.',
    why: 'Enables semantic search — find documents by meaning, not exact keyword match.',
    category: 'llm',
  },
  {
    id: 'cosine-similarity',
    term: 'Cosine Similarity',
    definition:
      'dot(A, B) / (|A| × |B|). Measures the angle between two vectors, giving a score from -1 (opposite) to 1 (identical direction).',
    why: 'The standard metric for comparing embeddings — magnitude-invariant, so short and long docs about the same topic score the same.',
    category: 'llm',
  },
  {
    id: 'prompt-caching',
    term: 'Prompt Caching',
    definition:
      'Pre-computing and storing the KV cache for a fixed system prompt prefix. Cached hits are ~10× cheaper and ~5× faster than misses.',
    why: 'Essential for agents with long system prompts making many LLM calls — can cut costs by 80%+.',
    category: 'llm',
  },
  // ── RAG ──────────────────────────────────────────────────────────────────────
  {
    id: 'rag',
    term: 'RAG',
    definition:
      'Retrieval-Augmented Generation. Pattern: retrieve relevant documents → inject as context → generate a grounded answer. Two phases: ingestion (offline) and query (online).',
    why: 'Reduces hallucinations, enables real-time knowledge updates without retraining, and provides source citations.',
    category: 'rag',
  },
  {
    id: 'chunking',
    term: 'Chunking',
    definition:
      'Splitting documents into smaller pieces before embedding. Strategies: fixed-size, sliding window (with overlap), sentence boundary, or paragraph boundary.',
    why: 'Chunk size is the biggest knob in RAG tuning. Too small = lose cross-sentence context. Too large = retrieval noise.',
    category: 'rag',
  },
  {
    id: 'hybrid-search',
    term: 'Hybrid Search',
    definition:
      'Combining BM25 keyword search with vector similarity search and merging results (typically via RRF). Both methods run in parallel.',
    why: 'Outperforms either alone — BM25 handles exact term matches, vector handles synonyms and semantic equivalents.',
    category: 'rag',
  },
  {
    id: 'bm25',
    term: 'BM25',
    definition:
      'Best Match 25 — a probabilistic keyword ranking algorithm. Ranks documents by term frequency (TF) and inverse document frequency (IDF). No ML needed.',
    why: 'Used in Elasticsearch and Lucene. The keyword component in hybrid search. Fast and interpretable.',
    category: 'rag',
  },
  {
    id: 'rrf',
    term: 'RRF',
    definition:
      'Reciprocal Rank Fusion. Merges ranked lists: score(d) = Σ 1/(k + rank(d)) across all rankers. k=60 is the standard constant.',
    why: 'The go-to algorithm for combining BM25 and vector results. Simple, no training needed, consistently beats raw scores.',
    category: 'rag',
  },
  {
    id: 'vector-db',
    term: 'Vector Database',
    definition:
      'Purpose-built storage for embeddings with fast approximate nearest-neighbor (ANN) search. Options: Pinecone, Weaviate, pgvector, ChromaDB, FAISS.',
    why: 'Regular databases cannot do fast cosine similarity at scale. ANN indexes (HNSW, IVF) make it feasible.',
    category: 'rag',
  },
  // ── Agentic Patterns ─────────────────────────────────────────────────────────
  {
    id: 'agent',
    term: 'Agent',
    definition:
      'An LLM-powered system that observes, reasons, takes actions with tools, observes results, and repeats until a goal is met.',
    why: 'Agents handle multi-step tasks that a single LLM call cannot — anything requiring external data, computation, or iteration.',
    category: 'agent',
  },
  {
    id: 'react',
    term: 'ReAct Pattern',
    definition:
      'Reason + Act: the agent alternates between text (thinking) and tool calls (acting). Loop: Thought → Action → Observation → repeat until done.',
    why: 'The foundational agent pattern. All major frameworks (LangChain, LangGraph, AutoGen) implement a variation of this.',
    category: 'agent',
  },
  {
    id: 'plan-execute',
    term: 'Plan-and-Execute',
    definition:
      'Two-phase agent: Phase 1 = ask LLM to produce a structured step-by-step plan. Phase 2 = execute each step in order with tools.',
    why: 'Better than pure ReAct for long tasks. Allows human review of the plan. Easier to debug. Less adaptive mid-run.',
    category: 'agent',
  },
  {
    id: 'tool-calling',
    term: 'Tool Calling / Function Calling',
    definition:
      'LLM outputs a structured request (name + arguments). Your code executes it and returns the result. Claude calls this `tool_use` blocks.',
    why: 'Gives agents capabilities beyond the base model: search, code execution, database access, API calls.',
    category: 'agent',
  },
  {
    id: 'tool-registry',
    term: 'Tool Registry',
    definition:
      'Central registry of available tools with schemas, descriptions, version metadata, and access control. Agents discover tools from it dynamically.',
    why: 'Decouples agent code from tool implementations. Swap, version, or restrict tools without touching agent logic.',
    category: 'agent',
  },
  {
    id: 'orchestrator',
    term: 'Orchestrator',
    definition:
      'A coordinator agent that routes tasks to specialist sub-agents (researcher, calculator, writer), then aggregates their results.',
    why: 'Enables multi-agent systems with single responsibility. Centralizes control flow and makes the system debuggable.',
    category: 'agent',
  },
  // ── Memory ───────────────────────────────────────────────────────────────────
  {
    id: 'short-term-memory',
    term: 'Short-Term Memory',
    definition:
      'The `messages` array passed to the LLM each turn. Lives in the context window. Disappears when the session ends.',
    why: 'Limited by context window size. Managed with rolling window (drop oldest) or summarization (compress old turns).',
    category: 'memory',
  },
  {
    id: 'long-term-memory',
    term: 'Long-Term Memory',
    definition:
      'Persistent storage (vector DB) that survives process restarts. Queried by semantic similarity to retrieve relevant past facts.',
    why: 'Lets agents remember across sessions — user preferences, past tasks, accumulated knowledge.',
    category: 'memory',
  },
  {
    id: 'episodic-memory',
    term: 'Episodic Memory',
    definition:
      'A structured log of past agent runs — task, steps taken, outcome, success/failure. Queryable by recency or keyword.',
    why: "Enables learning from past failures: 'That approach failed last time — let me try differently.'",
    category: 'memory',
  },
  {
    id: 'semantic-memory',
    term: 'Semantic Memory',
    definition:
      'Key-value store for discrete facts: user.name, user.preferences, entity attributes. Queried by exact key, not semantic similarity.',
    why: 'Structured facts that do not need semantic search — just inject them into the system prompt directly.',
    category: 'memory',
  },
  // ── Resiliency ───────────────────────────────────────────────────────────────
  {
    id: 'exponential-backoff',
    term: 'Exponential Backoff',
    definition:
      'Retry strategy: wait 2s, 4s, 8s, 16s... between attempts. Add jitter (randomness) in distributed systems to prevent thundering herd.',
    why: 'The standard retry pattern for all external API calls. Never retry immediately — you will amplify the load on a struggling service.',
    category: 'resiliency',
  },
  {
    id: 'guardrails',
    term: 'Guardrails',
    definition:
      'Input and output validation layers: sanitize user input, validate LLM output against a schema, filter harmful content.',
    why: "Garbage in → garbage out. Validate at system boundaries — not inside your own code where you control the data.",
    category: 'resiliency',
  },
  {
    id: 'structured-outputs',
    term: 'Structured Outputs',
    definition:
      'Forcing LLM responses into a defined JSON schema using system prompts and Pydantic validation, with automatic re-prompting on parse failures.',
    why: 'Agents need machine-readable outputs for tool inputs, plans, and decisions. Free-form text requires fragile regex parsing.',
    category: 'resiliency',
  },
  {
    id: 'loop-control',
    term: 'Loop Control',
    definition:
      'Enforcing a maximum number of agent iterations, a wall-clock timeout, and detecting stuck loops (same action repeated N times).',
    why: 'Without this, a bug causes an infinite loop that drains your entire API budget overnight.',
    category: 'resiliency',
  },
  {
    id: 'circuit-breaker',
    term: 'Circuit Breaker',
    definition:
      'After N consecutive failures, stop calling a service immediately and return an error. Try again after a recovery timeout.',
    why: 'Prevents wasting time and money hammering a service that is clearly down. Fail fast rather than pile up latency.',
    category: 'resiliency',
  },
  {
    id: 'llm-as-judge',
    term: 'LLM-as-Judge',
    definition:
      'Using a second LLM call to grade the quality of a first LLM output: "Rate this answer 0-10 based on these criteria."',
    why: 'Enables automated quality checks for free-form outputs that cannot be exact-matched against a reference.',
    category: 'resiliency',
  },
  // ── System Design ────────────────────────────────────────────────────────────
  {
    id: 'stateless-agent',
    term: 'Stateless Agent',
    definition:
      'Agent holds no state in memory between requests. All state lives in external storage (Redis, DB). Each invocation is independent.',
    why: 'Horizontally scalable — any worker can handle any request. Crash-safe — state is not lost if a worker dies.',
    category: 'system-design',
  },
  {
    id: 'observability',
    term: 'Observability',
    definition:
      'Structured tracing of every agent step — tool called, inputs, outputs, latency, and tokens consumed. Think: OpenTelemetry spans for LLM calls.',
    why: "You cannot debug what you cannot see. Required for production: 'which step is slow?', 'why did this task fail?'",
    category: 'system-design',
  },
  {
    id: 'llm-gateway',
    term: 'LLM Gateway',
    definition:
      'A unified interface layer that abstracts the LLM provider. Provides fallback chains, retry logic, token tracking, and auth in one place.',
    why: 'Agents never reference model names directly. Swap providers or add fallback in one file, not in every agent.',
    category: 'system-design',
  },
]
