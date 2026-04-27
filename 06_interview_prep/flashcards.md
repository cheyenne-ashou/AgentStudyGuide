# Flashcards — 30 Key Terms

Study these the day before. For each: know the definition AND the "why it matters."

---

## LLM Fundamentals

**Token**
A unit of text processed by an LLM (roughly 0.75 words). Models have token limits for input+output.
*Why: affects cost, latency, and what fits in context.*

**Context Window**
The maximum number of tokens a model can process at once (input + output).
*Why: determines how much conversation history, documents, or code you can include.*

**Temperature**
Controls output randomness. t=0 is deterministic (same output every time). t=1 is maximally varied.
*Why: use t=0 for structured/tool-calling; t=0.7 for conversation; t=1 for creative tasks.*

**Hallucination**
When an LLM generates plausible-sounding but factually incorrect information.
*Why: the #1 reliability problem in production; RAG and structured outputs are the main mitigations.*

**Embedding**
A dense vector representation of text capturing its semantic meaning (e.g., 768 or 1536 floats).
*Why: enables semantic search — find documents by meaning, not exact keywords.*

**Cosine Similarity**
Dot product of two vectors divided by their magnitudes. Measures semantic closeness (1.0 = identical).
*Why: the metric used to compare embeddings in vector search.*

**Prompt Caching**
Pre-computing and storing the KV cache for a fixed system prompt prefix. Cached hits: ~10x cheaper, ~5x faster.
*Why: essential for agents with long system prompts making many LLM calls.*

---

## Retrieval & RAG

**RAG (Retrieval-Augmented Generation)**
Pattern: retrieve relevant documents → inject as context → generate grounded answer.
*Why: reduces hallucinations, enables knowledge updates without retraining, provides citations.*

**Chunking**
Splitting documents into smaller pieces before embedding. Strategy (fixed/sliding/semantic) affects recall.
*Why: chunk size is the biggest knob in RAG tuning. Too small = lose context; too large = more noise.*

**Hybrid Search**
Combining keyword search (BM25) with vector search and merging results (RRF).
*Why: outperforms either alone — BM25 handles exact terms, vector handles synonyms.*

**BM25**
A statistical keyword ranking algorithm. Fast, no ML needed, great for exact term matching.
*Why: used in Elasticsearch, Lucene, and as the keyword component of hybrid search.*

**Reciprocal Rank Fusion (RRF)**
Merges ranked lists: score(d) = Σ 1/(k + rank(d)). Simple, effective, no training needed.
*Why: the standard way to combine BM25 and vector search results.*

**Vector Database**
Purpose-built storage for embeddings with fast approximate nearest-neighbor search.
*Why: regular DBs can't do fast cosine similarity at scale. Options: Pinecone, Weaviate, pgvector, Chroma.*

---

## Agentic Patterns

**Agent**
An LLM-powered system that observes, reasons, acts with tools, and repeats until a goal is met.
*Why: agents handle multi-step tasks that a single LLM call cannot.*

**ReAct**
Reason + Act: the agent alternates between thinking (text) and acting (tool calls).
*Why: the foundational pattern. All agent frameworks implement a variation of this loop.*

**Plan-and-Execute**
Two phases: create a structured plan, then execute each step.
*Why: better for long tasks, allows plan review before execution. Less adaptive mid-run.*

**Tool Calling / Function Calling**
LLM outputs a structured request; your code executes it and returns the result.
*Why: gives agents capabilities beyond the base model: search, calc, code execution, DB access.*

**Tool Registry**
Central registry of available tools with schemas, metadata, and access control.
*Why: decouples agent code from tool implementations. Enables dynamic discovery.*

**Orchestrator**
A controller agent that routes tasks to specialist sub-agents and aggregates results.
*Why: enables multi-agent systems with clear separation of concerns.*

---

## Memory

**Short-Term Memory**
The messages array passed to the LLM (context window). Disappears when session ends.
*Why: managed by rolling window or summarization when it gets too long.*

**Long-Term Memory**
Persistent storage (vector DB) that survives sessions. Retrieved by semantic similarity.
*Why: lets agents "remember" across sessions — user preferences, past tasks, knowledge.*

**Episodic Memory**
A log of past agent runs — what was done, what succeeded/failed.
*Why: enables learning from past mistakes: "last time this approach failed, let me try differently."*

**Semantic Memory**
Key-value store for facts: user.name, user.preferences, entity.data.
*Why: structured facts that don't need semantic search — just direct key lookup.*

---

## Resiliency

**Exponential Backoff**
Wait 2s, 4s, 8s, 16s... between retries. Prevents thundering herd on rate limits.
*Why: the standard retry pattern for all external API calls in production.*

**Guardrails**
Input/output validation (Pydantic schemas, content classifiers, schema enforcement).
*Why: garbage in → garbage out. Validate at system boundaries.*

**Structured Outputs**
Forcing LLM to respond in a defined JSON schema, with re-prompting on failure.
*Why: agents need machine-readable outputs; free-form text requires fragile parsing.*

**Loop Control**
Max iterations + timeout + stuck-loop detection for agent loops.
*Why: without it, bugs cause infinite loops that drain your API budget.*

**Circuit Breaker**
After N consecutive failures, stop calling a service immediately. Try again after timeout.
*Why: prevents wasting time/money on a clearly-broken dependency.*

**LLM-as-Judge**
Using a second LLM call to grade the quality of a first LLM's output.
*Why: enables automated quality checks for free-form outputs that can't be exact-matched.*

---

## System Design

**Stateless Agent**
Agent holds no state in memory — all state in the request + external storage (Redis/DB).
*Why: horizontally scalable. Two instances can handle the same conversation.*

**Observability**
Structured tracing of every agent step: tool, input, output, latency, tokens.
*Why: "you can't debug what you can't see." Essential for production agents.*

**LLM Gateway**
Unified interface abstracting the LLM provider. Adds fallback, retry, usage tracking.
*Why: agents never reference model names directly. Swap providers in one place.*
