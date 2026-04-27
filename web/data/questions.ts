export type QuestionCategory = 'conceptual' | 'system-design' | 'practical'

export type Question = {
  id: string
  question: string
  answer: string
  category: QuestionCategory
  tags: string[]
}

export const CATEGORY_LABELS: Record<QuestionCategory, string> = {
  conceptual: 'Conceptual',
  'system-design': 'System Design',
  practical: 'Practical',
}

export const questions: Question[] = [
  // ── Conceptual ───────────────────────────────────────────────────────────────
  {
    id: 'what-is-agent',
    category: 'conceptual',
    tags: ['agent', 'fundamentals'],
    question: 'What is an AI agent?',
    answer: `An agent is an LLM-powered system that can take sequences of actions to accomplish a goal. Unlike a simple chatbot, an agent has a loop: it observes the current state, reasons about what to do next, calls tools or APIs to take action, observes the results, and repeats until the task is done.

The four key properties:
- **Autonomy** — it decides what to do, step by step
- **Tool use** — it can interact with external systems (search, code, APIs)
- **State** — it maintains context across multiple steps
- **Stopping condition** — it knows when it's done

The canonical loop is the **ReAct pattern**: Thought → Action → Observation → repeat.`,
  },
  {
    id: 'rag-end-to-end',
    category: 'conceptual',
    tags: ['rag', 'retrieval', 'embeddings'],
    question: 'How does RAG work? Walk me through it end-to-end.',
    answer: `RAG (Retrieval-Augmented Generation) has two phases:

**Ingestion (offline):**
1. Load documents (.txt, .pdf, .md, etc.)
2. Chunk into smaller pieces (~80-150 words with 10-15% overlap)
3. Embed each chunk using an embedding model
4. Store embeddings in a vector database (Pinecone, ChromaDB, pgvector)

**Query (online, per request):**
1. Embed the user's question using the same model
2. Search the vector DB for the most semantically similar chunks
3. Retrieve top-k results
4. Inject them as context into the LLM prompt
5. Generate an answer grounded in those chunks

**In production:** Use hybrid search — combine BM25 keyword search with vector search and merge with Reciprocal Rank Fusion (RRF). This outperforms either alone because BM25 catches exact term matches while vector search catches semantic equivalents.`,
  },
  {
    id: 'hallucinations',
    category: 'conceptual',
    tags: ['hallucination', 'reliability', 'rag'],
    question: 'Why do LLMs hallucinate and how do you reduce it?',
    answer: `**Why they hallucinate:**
LLMs are trained to generate the most likely next token — not to verify factual accuracy. They are pattern-matching machines that produce fluent text. There is no internal "I don't know" signal, so they always output something plausible-sounding.

**Mitigations:**
1. **RAG** — ground every answer in retrieved documents; model can only use what you give it
2. **Structured outputs** — constrain what the model can say with JSON schemas; it can't invent fields
3. **Uncertainty prompting** — system prompt: "If you are not certain, say 'I don't know' rather than guessing"
4. **Temperature 0** — for factual tasks, deterministic output reduces creative confabulation
5. **Human review** — required for high-stakes outputs (medical, legal, financial)

**Key insight:** No single mitigation is sufficient. Production systems layer all of them.`,
  },
  {
    id: 'rag-vs-finetuning',
    category: 'conceptual',
    tags: ['rag', 'fine-tuning', 'architecture'],
    question: 'RAG vs fine-tuning — when do you use each?',
    answer: `**Use RAG when:**
- Knowledge changes frequently (news, prices, documentation updates)
- You need source citations / attribution
- Working with private data that wasn't in training data
- Reducing hallucinations is critical
- Budget is limited (indexing costs pennies; fine-tuning costs hundreds of dollars)

**Use fine-tuning when:**
- You need a specific output format or style the model doesn't naturally produce
- The domain vocabulary is highly specialized (medical, legal, financial)
- You have thousands of labeled examples
- Prompt engineering has hit a ceiling
- Latency/cost at inference scale matters (smaller fine-tuned model)

**Use both together when:**
- You need dynamic knowledge AND consistent format (e.g., customer support bot with company docs + formal tone)

**One-liner:** "RAG for dynamic knowledge with citations; fine-tuning for style/format adaptation."`,
  },
  {
    id: 'memory-design',
    category: 'conceptual',
    tags: ['memory', 'architecture', 'design'],
    question: 'How would you design memory for an agent?',
    answer: `Use a **four-layer memory architecture**:

| Layer | Storage | Lifetime | Use case |
|---|---|---|---|
| **Short-term** | Context window (messages array) | Current session | Conversation history |
| **Long-term** | Vector DB (ChromaDB, Pinecone) | Persistent | Cross-session knowledge |
| **Episodic** | JSON/DB log of past runs | Persistent | "What did I do last time?" |
| **Semantic** | Key-value store | Persistent | User facts, preferences |

**On each turn:**
1. Retrieve top-3 most relevant long-term memories (semantic similarity)
2. Load user facts from semantic memory (name, preferences)
3. Inject both into the system prompt
4. Run the agent loop
5. After completion, store new learnings back to long-term memory

**Practical notes:**
- Short-term: use rolling window (keep last N) or summarization when context fills up
- Long-term: always query before running — 50ms retrieval beats re-explaining context every time
- Episodic: great for debugging ("this task failed 3 times with the same approach")`,
  },

  // ── System Design ────────────────────────────────────────────────────────────
  {
    id: 'design-ai-assistant',
    category: 'system-design',
    tags: ['architecture', 'tools', 'scaling'],
    question: 'Design an AI assistant with tools.',
    answer: `**Five core components:**

1. **API Gateway** — auth, rate limiting per user, input validation (Pydantic/guardrails)
2. **Orchestrator** — manages the ReAct loop, enforces max_steps, handles retries and timeouts
3. **LLM Gateway** — unified interface, model fallback chain (Sonnet → Haiku), token tracking
4. **Tool Registry** — centralized, versioned, with access control per tool and per caller
5. **Memory Layer** — Redis for in-flight conversation state; Pinecone for long-term semantic memory

**Resiliency:** exponential backoff on all API calls, max_steps=15, circuit breakers on external tools, Pydantic validation on all tool inputs/outputs, human escalation for low-confidence outputs.

**Observability:** every step emits a structured span with timing, tool name, inputs, outputs, and token counts → send to Langfuse or OpenTelemetry backend.

**Scaling:**
- Stateless orchestrator workers → horizontal scaling behind a load balancer
- Async parallel tool calls → run independent tools concurrently
- Embedding cache (Redis TTL) → avoid re-embedding same documents
- Semantic response cache → return cached answer for repeated identical queries`,
  },
  {
    id: 'design-multi-agent',
    category: 'system-design',
    tags: ['multi-agent', 'architecture', 'orchestration'],
    question: 'Design a multi-agent system for research and report writing.',
    answer: `**Three specialist agents coordinated by an orchestrator:**

**Planner** → receives the task, outputs a JSON plan with N steps (each with: description, tool, expected output).

**Executor agents** (run in order or parallel):
- **Researcher**: web_search + RAG retrieval
- **Analyzer**: calculator, code execution, data processing
- **Writer**: synthesis and formatting

**Validator**: quality-gates the output with a score 0–1. Below threshold (0.7) → retry execution. After 3 retries → human escalation.

**Synthesizer**: combines all step results into a coherent final answer.

**Communication:** all agents exchange structured JSON (Pydantic validated). No free-form hand-offs.

**Key design decisions:**
- Orchestrator pattern (vs swarm) = more predictable, easier to debug, single bottleneck
- Validator prevents low-quality results from propagating silently
- Shared tool registry, observability, and memory layer across all agents

**Tradeoff:** orchestrator is a single point of failure; swarm is more resilient but harder to reason about.`,
  },
  {
    id: 'scale-100k',
    category: 'system-design',
    tags: ['scaling', 'architecture', 'distributed'],
    question: 'How would you scale an agentic system to 100k users?',
    answer: `**Core principle: stateless agent workers.**

All state must live in external storage — not in process memory.

**Infrastructure:**
- Stateless agent workers → ECS/Kubernetes, auto-scale on queue depth
- Redis for in-flight conversation state (TTL = session lifetime)
- Message queue (SQS/Kafka) to decouple agent steps and handle bursts
- Managed vector DB (Pinecone serverless) for semantic memory

**LLM bottleneck (the main constraint):**
- Rate limit per user to prevent abuse
- Queue excess requests rather than dropping them
- Use Batch API for non-realtime tasks (10× cheaper)
- Route simple queries to Haiku, complex to Sonnet (LLM router)
- Prompt caching on long system prompts (saves 80% of input tokens)

**Caching layers:**
1. Embedding cache: don't re-embed the same document twice
2. Response cache: exact-match cache for repeated identical queries
3. Tool result cache: cache web search results (TTL = 5 min)

**Observability at scale:** sample 1% of traces for dev/monitoring; capture 100% on errors.

**Bottleneck order:** LLM tokens/sec → tool API rate limits → embedding throughput.`,
  },
  {
    id: 'handle-failures',
    category: 'system-design',
    tags: ['resiliency', 'failures', 'reliability'],
    question: 'How do you handle failures in a long-running agent?',
    answer: `**Layered defenses:**

1. **Retry with backoff** — \`@retry(stop=stop_after_attempt(3), wait=wait_exponential(...))\` on every LLM and tool call. Never retry immediately.

2. **Loop control** — \`max_steps=15\`, timeout=60s, stuck-loop detection (same action 3× in a row → break).

3. **Circuit breaker** — after 3 consecutive failures on a tool, stop calling it and return a cached/fallback response.

4. **Graceful degradation** — if web search fails, answer from training knowledge with a "I couldn't verify this" caveat.

5. **Structured output validation** — if LLM returns invalid JSON, re-prompt up to 3 times with the parse error before giving up.

6. **Human escalation** — if confidence < 0.5 after retries, route to a human review queue rather than returning a bad answer.

7. **Checkpointing** — for tasks > 60s, save progress to a DB so the agent can resume after crashes rather than restart.

**Key principle:** always have a fallback. Every component must have an "I failed" path that degrades gracefully, not catastrophically.`,
  },

  // ── Practical ────────────────────────────────────────────────────────────────
  {
    id: 'debug-agent',
    category: 'practical',
    tags: ['debugging', 'observability', 'operations'],
    question: 'How do you debug a failing agent?',
    answer: `**Start with the trace.** Every step should emit a span: tool called, inputs, outputs, latency, tokens.

**Diagnostic questions:**
- **Loop issues**: Did the agent hit max_steps? Is it repeating the same tool call?
- **Tool failures**: Check tool call inputs — is the agent generating valid arguments? Check tool outputs — did the tool return an error?
- **Poor answers**: Check retrieval — are the right chunks being surfaced? Is the context relevant to the query?
- **High latency**: Which span is slowest? (Usually: LLM synthesis > retrieval > tool execution)
- **Token bloat**: Is the system prompt growing unexpectedly? Is the messages array accumulating without trimming?

**Practical tips:**
- Log the full \`messages\` array on failure — you can replay it exactly in the Anthropic console
- Add step-level logging with \`structlog\`: step number, tool, duration, stop_reason
- Use a tracer (Langfuse, Arize Phoenix) with session grouping so you can see an entire multi-turn run at once

**Tooling:** Langfuse, OpenTelemetry + Jaeger, Arize Phoenix, LangSmith.`,
  },
  {
    id: 'test-agent',
    category: 'practical',
    tags: ['testing', 'evaluation', 'quality'],
    question: 'How do you test an agent?',
    answer: `**Three levels of testing:**

**1. Unit tests (prompt assertions)**
Test individual behaviors in isolation. Use \`pytest\` with real API calls.
- Assert output contains expected keywords
- Assert output length is in a reasonable range
- Assert structured outputs parse correctly
- Assert the agent calls the right tool for a given query type

**2. Golden dataset evaluation**
Maintain 20-50 known question/answer pairs. Run the full agent and score outputs.
- Scoring: keyword match (fast), LLM-as-judge (slower, more nuanced), exact match (for structured)
- Run in CI: alert if score drops >5% from baseline
- Store results with timestamps to track regressions

**3. Simulation testing**
Run the full agent in a sandboxed environment against realistic scenarios.
- Verify handling of: tool failures, rate limits, empty search results, malformed responses
- Test edge cases: max_steps reached, circular reasoning, conflicting tool outputs

**Key insight:** you cannot unit test the LLM itself, but you CAN test your agent's behavior on known inputs. Treat it like integration testing.`,
  },
  {
    id: 'langchain-vs-langgraph',
    category: 'practical',
    tags: ['frameworks', 'langchain', 'langgraph'],
    question: "What's the difference between LangChain and LangGraph?",
    answer: `**LangChain** provides composable building blocks: chains, retrievers, tools, memory modules. You wire them together into pipelines. Great for simple linear workflows (retrieve → augment → generate) and RAG chains.

**LangGraph** (built on LangChain) models agent workflows as a **state machine graph**. Each node is a processing step; edges are conditional transitions.

**Why LangGraph matters:**
- Explicit loops — define "if tool_use, go to executor node; else, go to response node"
- Conditional edges — "if validation score < 0.7, go back to executor"
- Multi-agent — each agent is a node; coordination is explicit in the graph definition
- Persistence — built-in checkpointing for long-running workflows

**When to use which:**
- LangChain: RAG pipelines, simple tool-use chains, quick prototypes
- LangGraph: multi-step agents with loops, multi-agent workflows, production systems needing explicit control flow

**Interview tip:** saying "I'd use LangGraph for anything with conditional logic or loops" shows you understand the framework landscape.`,
  },
  {
    id: 'stateless-vs-stateful',
    category: 'practical',
    tags: ['architecture', 'scaling', 'state'],
    question: 'What are the tradeoffs between stateless and stateful agents?',
    answer: `**Stateless:**
Agent holds no state in memory. Each request is independent. State lives in Redis/DB.

✅ Horizontally scalable — any worker handles any request
✅ Crash-safe — restart a worker and it picks up from stored state
✅ Easy to load balance and deploy
❌ Requires external state store (Redis round-trip per turn)
❌ Slightly more infrastructure complexity

**Stateful:**
Agent holds conversation state in process memory.

✅ Simpler code — no state serialization/deserialization
✅ Lower latency — no DB round-trip for state reads
❌ Sticky sessions required — a specific user must always hit the same worker
❌ Loses state on crash or deployment
❌ Cannot scale horizontally without session affinity

**Recommendation:** stateless in production, stateful in development.
The Redis round-trip (~1ms) is trivial compared to LLM call latency (~500ms). The scalability benefits vastly outweigh the extra Redis call.`,
  },
  {
    id: 'react-pattern',
    category: 'practical',
    tags: ['react', 'patterns', 'fundamentals'],
    question: 'What is the ReAct pattern and why is it important?',
    answer: `**ReAct = Reason + Act.**

The agent alternates between two output types:
1. **Text** (thinking): "I need to find the current price, let me search for it"
2. **Tool call** (acting): \`web_search(query="AAPL stock price")\`

After each action, it observes the result and reasons again. The loop continues until the model produces text with \`stop_reason="end_turn"\` (no more tool calls needed).

**Why it matters:**
- Before ReAct, agents were either pure chatbots (no tools) or pure function-callers (no reasoning)
- ReAct showed that interleaving reasoning and action dramatically improves multi-step task performance
- It gives you visibility into *why* the agent took each action (the thought before the tool call)
- All major frameworks implement a variation: LangChain's AgentExecutor, LangGraph's tool-calling nodes, AutoGen's conversational agents

**Anatomy of one loop iteration:**
\`\`\`
1. messages → Claude API
2. Claude returns: text block (thought) + tool_use block (action)
3. Your code: execute tool → get result
4. Append tool_result to messages
5. Go to step 1 (unless stop_reason == "end_turn")
\`\`\``,
  },
  {
    id: 'advanced-topics',
    category: 'practical',
    tags: ['advanced', 'senior', 'cutting-edge'],
    question: 'What advanced topics differentiate a senior agentic AI engineer?',
    answer: `**Self-reflection / critique loops:** agent generates an answer, then critiques it against criteria, then revises. Reduces errors on complex reasoning by 20-40% without human intervention.

**Tree-of-Thoughts:** instead of one linear reasoning chain, explore N branches in parallel and pick the best. Used in planning-heavy tasks where one wrong step derails everything.

**Multi-agent negotiation:** agents debate and refine answers through structured disagreement (Debate, Constitutional AI). Produces more robust, less hallucinated outputs.

**Streaming responses:** return partial tokens as generated for better UX. Requires SSE or WebSocket throughout the stack, async handling, and careful buffering for tool calls.

**LLM routing:** classify query complexity and route to the appropriate model. Simple queries → Haiku (fast, cheap). Complex reasoning → Sonnet/Opus. Saves 60-80% on LLM costs.

**Evaluation infrastructure:** regression testing pipelines with golden datasets, A/B testing prompt variants with statistical significance testing, LLM-as-judge at scale with calibration.

**Cost optimization:** prompt caching for long system prompts, batch API for non-realtime workloads, context compression before expensive synthesis calls.`,
  },
]
