# Common Interview Questions — Prepared Answers

15 questions with full answers. Read these aloud until they feel natural.

---

## Conceptual Questions

### 1. "What is an AI agent?"

An agent is an LLM-powered system that can take sequences of actions to accomplish a goal. Unlike a simple chatbot, an agent has a loop: it observes the current state, reasons about what to do next, calls tools or APIs to take action, observes the results, and repeats until the task is done.

The key properties are: autonomy (it decides what to do), tool use (it can interact with external systems), state (it maintains context across steps), and a stopping condition (it knows when it's done).

---

### 2. "How does RAG work? Walk me through it end-to-end."

There are two phases. In the ingestion phase: load your documents, split them into chunks (typically 80-150 words with some overlap), generate embeddings for each chunk, and store them in a vector database like Pinecone or ChromaDB.

In the query phase: embed the user's question using the same embedding model, search the vector DB for the most semantically similar chunks, retrieve the top-k results, inject them as context into the LLM prompt, and generate an answer grounded in those chunks.

In production I'd use hybrid search — combining BM25 keyword search with vector search and merging with RRF, because it outperforms either alone. BM25 catches exact term matches; vector search catches semantic equivalents.

---

### 3. "Why do LLMs hallucinate and how do you reduce it?"

LLMs are trained to generate the most likely next token, not to verify factual accuracy. They're pattern-matching machines that produce fluent text — there's no internal "I don't know" signal.

The main mitigations are:
1. **RAG**: ground every answer in retrieved documents; model can only use what you give it
2. **Structured outputs**: constrain what the model can output with JSON schemas
3. **Uncertainty prompting**: instruct the model to say "I don't know" rather than guess
4. **Temperature 0**: for factual tasks, deterministic output reduces creative confabulation
5. **Human review**: required for high-stakes outputs

---

### 4. "RAG vs fine-tuning — when do you use each?"

Use **RAG** when: knowledge changes frequently (news, prices, documentation), you need source citations, you're working with private data that wasn't in training, or reducing hallucinations is critical. RAG is also much cheaper — indexing documents costs pennies, while fine-tuning costs hundreds of dollars.

Use **fine-tuning** when: you need the model to adopt a specific output format or style, the domain vocabulary is highly specialized (legal, medical), you have thousands of labeled examples, or prompt engineering has hit a ceiling. Fine-tuned models are also faster and cheaper at inference time.

Most production systems use both: RAG for dynamic knowledge, fine-tuning for consistent output format.

---

### 5. "How would you design memory for an agent?"

I'd use a layered memory architecture with four types:

**Short-term**: the messages array passed to the LLM each turn. Managed with a rolling window (keep last N turns) or summarization when it gets too long.

**Long-term**: a vector database (ChromaDB for dev, Pinecone for production). On each turn, I'd retrieve the top-3 most relevant memories and inject them into the system prompt.

**Episodic**: a structured log of past agent runs (task, steps, outcome, success/failure). Queried by recency and keyword. Useful for "what did I try last time this failed?"

**Semantic**: a key-value store for user facts (name, preferences, settings). Queried by exact key, not semantic similarity.

On each new turn: retrieve relevant long-term memories + user semantic facts → inject into context → run the agent → update memory with new learnings.

---

## System Design Questions

### 6. "Design an AI assistant with tools."

I'd build it as five components:

1. **API Gateway**: auth, rate limiting, input validation
2. **Orchestrator**: manages the ReAct loop, enforces max steps, handles retries
3. **LLM Gateway**: unified interface, fallback chain (Sonnet → Haiku), token tracking
4. **Tool Registry**: centralized, versioned, with access control per tool
5. **Memory Layer**: Redis for short-term (conversation), Pinecone for long-term (user facts)

For resiliency: exponential backoff on all API calls, max_steps = 15, circuit breakers on external tools, Pydantic validation on all tool inputs/outputs.

For observability: every step emits a structured span with timing, tool name, inputs, outputs, and token counts. I'd send this to Langfuse or an OpenTelemetry backend.

For scaling: stateless orchestrator workers (state in Redis), async parallel tool calls, embedding cache for semantic memory.

---

### 7. "Design a multi-agent system for research and report writing."

Three specialist agents coordinated by an orchestrator:

**Planner**: receives the task, outputs a JSON plan with N steps, each specifying which agent and tool to use.

**Executor agents**: Researcher (web search), Analyzer (calculator/code), Writer (synthesis). They run in sequence (or parallel where independent), passing results forward as context.

**Validator**: quality gates the output with a score 0-1. Below threshold → retry execution. After 3 retries → human escalation.

All agents share a tool registry, memory layer, and observability stack. Communication is via structured JSON (Pydantic validated).

The key tradeoff: orchestrator pattern (my design) is more predictable and debuggable, but a swarm architecture allows more parallelism and adaptability.

---

### 8. "How would you scale an agentic system to 100k users?"

The key insight is: agent steps must be stateless. All state goes to external storage.

At 100k users:
- **Compute**: stateless agent workers behind a load balancer (AWS ECS / Kubernetes). Auto-scale on queue depth.
- **State**: Redis for in-flight conversation state, TTL = session lifetime
- **Memory**: managed vector DB (Pinecone serverless) for semantic memory
- **LLM**: rate limit per user, queue excess requests, use batch API for non-realtime tasks
- **Caching**: semantic response cache (Redis), embedding cache for documents, tool result cache with TTL
- **Tools**: async parallel execution (run independent tool calls concurrently)
- **Observability**: structured tracing with sampling (1% for dev, 100% for errors)

The bottleneck is almost always LLM tokens/sec. Mitigation: prompt caching, smaller fallback models, async processing for non-realtime tasks.

---

### 9. "How do you handle failures in a long-running agent?"

Layered defenses:

1. **Retry with backoff**: `@retry(stop=stop_after_attempt(3), wait=wait_exponential(...))` on every LLM and tool call
2. **Loop control**: `max_steps = 15`, timeout = 60s, stuck-loop detection (same action 3x in a row)
3. **Circuit breaker**: stop calling a service after 3 consecutive failures, retry after 30s
4. **Graceful degradation**: if web search fails, answer from training knowledge with a caveat
5. **Human escalation**: if confidence < 0.5 after retries, route to human review queue
6. **Checkpointing**: for very long tasks, save progress to DB so you can resume after crashes

The key principle: always have a fallback. Never let a single point of failure kill the whole task.

---

## Practical Questions

### 10. "How do you debug an agent?"

First, check the traces. Every step should emit a span with: which tool was called, with what inputs, what came back, how long it took, and how many tokens were used.

From there:
- **Loop issues**: look for max_steps being hit; check if the agent is repeating the same action
- **Tool failures**: check tool call inputs — is the agent generating valid arguments?
- **Poor answers**: check retrieval — are the right chunks being returned? Is the context relevant?
- **High latency**: check which span is slowest (usually LLM synthesis > retrieval > tool execution)
- **Token bloat**: check system prompt length; is it growing with each turn?

For reproducibility: log the full messages array on failure so you can replay it.

---

### 11. "How do you test an agent?"

Three levels:

**Unit tests**: test individual components in isolation. Mock the LLM, assert tool call arguments are correct, validate that guardrails reject bad inputs.

**Golden dataset tests**: run the agent on 20-50 known question/answer pairs, score with keyword matching or LLM-as-judge, track score over time in CI. Alert if score drops > 5%.

**Simulation testing**: run the full agent against realistic scenarios in a sandboxed environment. Verify it handles edge cases: tool failures, rate limits, empty search results, malformed responses.

For LLM behavior specifically: assert outputs contain expected keywords, test that the model admits uncertainty on unknown entities, verify structured outputs parse correctly.

---

### 12. "What's the difference between LangChain and LangGraph?"

LangChain provides components (chains, tools, retrievers, memory) that you compose into pipelines. It's great for simple linear workflows but becomes hard to control when you need conditional logic or loops.

LangGraph (from the LangChain team) models agent workflows as a state machine graph. Each node is an agent step; edges are transitions with conditions. This makes it much easier to build: agents with loops, agents with conditional branches (e.g., "if validation fails, go back to step 2"), and multi-agent systems with explicit coordination.

For an interview: LangGraph is the preferred choice for complex multi-step agents. LangChain is good for RAG pipelines and simple tool chains. Knowing both shows depth.

---

### 13. "What are the tradeoffs between stateless and stateful agents?"

**Stateless**: each request is independent. State lives in the request payload + external DB. 
✓ Horizontally scalable, crash-safe, easy to load balance
✗ Requires external state store (Redis/DB), more infrastructure

**Stateful**: agent holds state in process memory.
✓ Simpler code, lower latency (no DB round-trip for state)
✗ Sticky sessions, can't scale horizontally easily, loses state on crash

In production: stateless is almost always the right choice. The extra Redis round-trip is worth the scalability. During development: stateful is fine — less infrastructure overhead.

---

### 14. "What is the ReAct pattern and why is it important?"

ReAct stands for Reason + Act. The agent alternates between two types of output: text (thinking out loud about what to do) and tool calls (taking action). After each action, it observes the result and reasons again.

It's important because it's the foundational pattern behind all modern agents. Before ReAct, agents were either pure chatbots (no tools) or pure function-callers (no reasoning). ReAct showed that interleaving reasoning and action dramatically improves performance on multi-step tasks.

Every major agent framework — LangChain, LangGraph, AutoGen, CrewAI — implements a variation of the ReAct loop. Understanding it at the raw API level (as in react_agent.py) means you understand what those frameworks are actually doing.

---

### 15. "What advanced topics should a senior agentic AI engineer know?"

The ones that differentiate senior candidates:

**Self-reflection loops**: agents that critique their own output and revise before returning a response. Dramatically reduces errors on complex reasoning tasks.

**Tree-of-Thoughts**: instead of one reasoning chain, explore multiple branches and pick the best. Useful for planning-heavy tasks.

**Multi-agent negotiation**: agents that debate and refine answers through structured disagreement (Debate, Constitutional AI).

**Streaming**: returning partial tokens as they're generated for better UX. Requires SSE or WebSocket and async handling throughout the stack.

**Cost optimization**: prompt caching, batch API for non-realtime, routing to cheaper models based on task complexity (LLM routing).

**Evaluation infrastructure**: regression testing pipelines, A/B testing prompt variants, LLM-as-judge at scale.
