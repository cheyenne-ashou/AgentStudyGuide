export type GlossaryEntry = {
  short: string   // 1-2 sentence definition
  example: string // concrete example
}

// Keys are lowercase. AnnotatedText matches case-insensitively.
export const glossary: Record<string, GlossaryEntry> = {
  // ── LLM internals ───────────────────────────────────────────────────────────
  token: {
    short: 'The smallest unit of text an LLM processes. Roughly 0.75 words — "chatbot" is 1 token, "unbelievably" is 3.',
    example: 'The sentence "Hello world" = 2 tokens. GPT-4 has a 128k token limit.',
  },
  tokens: {
    short: 'Plural of token — the chunks of text an LLM reads and generates one at a time.',
    example: '"How are you?" = 5 tokens. Longer prompts use more tokens and cost more.',
  },
  'kv cache': {
    short: "Key-Value cache — stores the intermediate attention computations for a prompt prefix so they don't need to be recalculated on the next call.",
    example: 'A 5,000-token system prompt costs full price on the first call, then ~10× less on subsequent calls when cached.',
  },
  tokenizer: {
    short: 'Software that splits raw text into tokens before feeding to an LLM. Different models use different tokenizers.',
    example: 'GPT uses BPE (Byte Pair Encoding). Claude uses a similar subword tokenizer.',
  },
  'probability distribution': {
    short: 'A set of values (0–1) that describe how likely each possible next token is. Temperature reshapes this distribution.',
    example: 'At t=0: token "cat" = 0.9, "dog" = 0.08, others ≈ 0. At t=1: "cat" = 0.4, "dog" = 0.35, others split the rest.',
  },
  'greedy decoding': {
    short: 'Always picking the single most probable next token. Equivalent to temperature=0. Deterministic but can be repetitive.',
    example: 'Greedy: "The sky is blue." every time. With sampling: sometimes "The sky is azure", "cerulean", etc.',
  },
  sampling: {
    short: 'Randomly selecting the next token from the probability distribution, weighted by likelihood. Temperature controls how flat the distribution is.',
    example: 'At t=0.7, "cat" has 70% chance and "dog" has 30% — both are possible outputs.',
  },
  'attention mechanism': {
    short: 'The core operation in a transformer that lets each token "attend to" (look at) all other tokens in the context to understand relationships.',
    example: 'In "The bank by the river was muddy", attention helps the model link "bank" to "river" not "money".',
  },
  transformer: {
    short: 'The neural network architecture that underpins all modern LLMs. Uses attention mechanisms to process entire sequences in parallel.',
    example: 'GPT-4, Claude, Llama — all are transformer models.',
  },

  // ── Embeddings & search ──────────────────────────────────────────────────────
  vector: {
    short: 'A list of numbers (floats) representing a point in N-dimensional space. In AI, text is converted to vectors to capture its meaning.',
    example: '"dog" might be [0.2, 0.8, 0.1, ...] (1536 numbers). "cat" would be nearby in that space.',
  },
  vectors: {
    short: 'Plural of vector — lists of numbers representing text meaning in high-dimensional space.',
    example: 'Two vectors are "similar" if their cosine similarity is close to 1.0.',
  },
  'dot product': {
    short: 'A mathematical operation: multiply each pair of numbers across two vectors and sum the results. Used to measure directional alignment.',
    example: 'dot([1,2], [3,4]) = 1×3 + 2×4 = 11. Used inside cosine similarity: cosine = dot(A,B) / (|A| × |B|).',
  },
  magnitude: {
    short: "The 'length' of a vector — the square root of the sum of squared values. Used to normalize vectors for cosine similarity.",
    example: 'magnitude([3,4]) = √(9+16) = 5. Cosine similarity divides by both vectors\' magnitudes.',
  },
  'semantic similarity': {
    short: 'How closely two pieces of text mean the same thing, regardless of exact wording. Measured by cosine similarity of their embeddings.',
    example: '"car" and "automobile" have high semantic similarity (~0.92). "car" and "banana" have low similarity (~0.1).',
  },
  'semantic search': {
    short: 'Finding documents by meaning rather than exact keyword matches. Uses embeddings + cosine similarity instead of keyword lookup.',
    example: 'Searching "how do I make pasta?" returns a recipe for spaghetti bolognese even if neither word appears in the query.',
  },
  'ann': {
    short: 'Approximate Nearest Neighbor — an algorithm that finds the most similar vectors very fast by trading a tiny bit of accuracy for speed.',
    example: 'Exact k-NN on 10M vectors takes minutes. ANN (HNSW, IVF) finds the same top-10 results in milliseconds.',
  },
  hnsw: {
    short: 'Hierarchical Navigable Small World — a graph-based ANN index. The most commonly used index in vector databases. Fast and accurate.',
    example: 'ChromaDB, Pinecone, and Weaviate all use HNSW internally for fast similarity search.',
  },
  'cross-encoder': {
    short: 'A model that takes a query + document pair and scores their relevance together. More accurate than embeddings alone but much slower.',
    example: 'After BM25+vector retrieval gets top 20 results, a cross-encoder re-scores them to pick the best 5.',
  },
  'tf-idf': {
    short: 'Term Frequency-Inverse Document Frequency — a classic scoring method: words common in a document but rare overall score higher.',
    example: '"neural network" in an ML paper scores high. "the" scores near zero (appears in every document).',
  },

  // ── Retrieval & RAG ──────────────────────────────────────────────────────────
  retrieval: {
    short: 'The step in RAG where relevant documents are fetched from a database before generating an answer.',
    example: 'User asks "What is our refund policy?" → retrieve the top-3 most relevant policy document chunks → pass to LLM.',
  },
  ingestion: {
    short: "The offline pipeline that loads documents, chunks them, embeds them, and stores them in a vector DB so they're ready to retrieve.",
    example: 'Run ingest.py once on your PDF library. After that, every query hits the pre-built index.',
  },
  augmentation: {
    short: 'In RAG, injecting retrieved documents into the prompt as context before generating. The "A" in RAG.',
    example: 'Prompt: "Context:\\n[retrieved chunks]\\n\\nQuestion: What is the return policy?"',
  },

  // ── Frameworks & tools ───────────────────────────────────────────────────────
  pydantic: {
    short: 'A Python library for data validation using type annotations. Parses and validates structured data (JSON → typed Python objects) with clear error messages.',
    example: 'class AgentOutput(BaseModel): answer: str; confidence: float = Field(ge=0, le=1) — validation is automatic.',
  },
  tenacity: {
    short: 'A Python library for adding retry logic with decorators. Supports exponential backoff, jitter, and custom stop conditions.',
    example: '@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2)) def call_api(): ...',
  },
  redis: {
    short: 'An in-memory key-value database. Extremely fast (sub-millisecond reads). Used for caching, session state, and rate limiting in production systems.',
    example: 'Store conversation history in Redis with a 30-minute TTL so stateless workers can retrieve it on each request.',
  },
  langfuse: {
    short: 'An open-source LLM observability platform. Records every LLM call, tool use, and agent step with timing and token counts.',
    example: 'After an agent run, open Langfuse to see: step 1 called web_search (340ms), step 2 called calculator (2ms), etc.',
  },
  opentelemetry: {
    short: 'An open standard for collecting structured traces, metrics, and logs from distributed systems. Increasingly adopted for LLM observability.',
    example: 'Emit a span for each agent step. A Jaeger backend visualizes the full trace as a waterfall diagram.',
  },
  langchain: {
    short: 'A Python/JS framework for building LLM applications. Provides components: chains, retrievers, tools, and memory modules.',
    example: 'A LangChain RAG chain: load docs → split → embed → store → retriever → LLM → answer.',
  },
  langgraph: {
    short: 'A framework (built on LangChain) for building agent workflows as explicit state machine graphs. Better for loops and conditional logic than chains.',
    example: 'Define nodes (plan, execute, validate) and edges (if score < 0.7, go back to execute). The graph runs step by step.',
  },

  // ── Infrastructure & scaling ────────────────────────────────────────────────
  'thundering herd': {
    short: 'When many clients fail simultaneously and all retry at the same moment, overloading the service further and preventing recovery.',
    example: 'API goes down for 2s. 10,000 clients all retry at t=2s, causing another 2s outage. Jitter prevents this.',
  },
  'thundering herd problem': {
    short: 'When many clients fail simultaneously and all retry at the same moment, overloading the service further.',
    example: 'Fixed by adding jitter: each client waits 2s + random(0–1s), so retries are spread out.',
  },
  jitter: {
    short: 'Random variation added to retry wait times. Prevents synchronized retries from causing a thundering herd.',
    example: 'Instead of all clients waiting exactly 4s, they wait 4s ± random(0–1s). Spreads the retry load.',
  },
  'horizontal scaling': {
    short: 'Adding more servers/instances to handle more load, rather than making one server bigger (vertical scaling).',
    example: 'Start with 2 agent workers. At 10k users, scale to 20 workers. Each handles ~500 users independently.',
  },
  'horizontally scalable': {
    short: 'A design that can handle more load by adding more identical servers, without requiring a single powerful machine.',
    example: 'Stateless REST APIs are horizontally scalable. A monolith with in-memory state is not (without sticky sessions).',
  },
  'load balancer': {
    short: 'A component that distributes incoming requests across multiple backend servers to spread the load evenly.',
    example: 'NGINX or AWS ALB routes each user request to whichever agent worker has the least traffic.',
  },
  'sticky sessions': {
    short: 'A load balancer setting that always routes a specific user to the same server — required by stateful apps that store session data in memory.',
    example: 'If agent state is in process memory, the user must hit the same server each time. Stateless designs avoid this.',
  },
  'session affinity': {
    short: 'Another term for sticky sessions — routing the same user to the same server on every request.',
    example: 'Without session affinity, stateful agents would lose conversation history on every request hitting a different worker.',
  },
  'batch api': {
    short: "An API mode that processes many requests together asynchronously rather than one at a time. Typically 10× cheaper but returns results after minutes, not seconds.",
    example: 'Evaluate 500 Q&A pairs overnight using the batch API at $0.0004/1k tokens instead of $0.004/1k tokens.',
  },
  sse: {
    short: 'Server-Sent Events — a web protocol for streaming data from server to client in real-time over HTTP. Used for streaming LLM token output.',
    example: 'Instead of waiting 3s for a full response, the browser renders each word as it is generated via SSE.',
  },
  'server-sent events': {
    short: 'A web protocol for streaming data from server to browser in real-time. Used for token-by-token streaming of LLM responses.',
    example: 'ChatGPT uses SSE to stream responses word-by-word instead of waiting until generation is complete.',
  },
  kafka: {
    short: 'A distributed message queue / event streaming platform. Used to decouple producers and consumers so they can scale independently.',
    example: 'Planner publishes a task step to a Kafka topic. Multiple executor workers consume from the topic in parallel.',
  },
  sqs: {
    short: 'Amazon Simple Queue Service — a managed message queue. Workers pull tasks from the queue independently, enabling async processing.',
    example: 'POST /research → push task to SQS → worker pulls it → runs agent → stores result in DB → webhook notifies caller.',
  },

  // ── Prompting techniques ────────────────────────────────────────────────────
  'zero-shot': {
    short: 'Prompting an LLM with just the task description and no examples. The model uses only its training knowledge.',
    example: '"Translate this to French: Hello" — no French translation examples provided.',
  },
  'few-shot': {
    short: 'Providing 2-5 examples of the task in the prompt before asking the model to do it. Dramatically improves output quality.',
    example: '"Q: 3+4? A: 7. Q: 5+6? A: 11. Q: 8+9? A:" — the model learns the format from the examples.',
  },
  'chain-of-thought': {
    short: 'Prompting technique that asks the model to reason step-by-step before giving a final answer. Reduces errors on multi-step problems.',
    example: '"Let\'s think step by step: First, 6 apples at $0.50 = $3.00. Then, 4 bananas at $0.30 = $1.20. Total = $4.20."',
  },
  cot: {
    short: 'Short for Chain-of-Thought — a prompting technique that asks the model to show its reasoning before the final answer.',
    example: 'Adding "Let\'s think step by step" to a math prompt can cut error rates by 30-50%.',
  },
  'uncertainty prompting': {
    short: 'A technique where the system prompt instructs the model to say "I don\'t know" instead of guessing when unsure.',
    example: 'System prompt: "If you are not certain about a fact, say \'I don\'t have reliable information about this.\'"',
  },
  'grounding': {
    short: 'Providing factual context in the prompt so the model generates answers based on real data, not just training knowledge.',
    example: 'Instead of asking "What is our return policy?", inject the policy text first: "Context: [policy] \\n\\nQuestion: What is the return policy?"',
  },

  // ── Evaluation ──────────────────────────────────────────────────────────────
  'golden dataset': {
    short: 'A curated set of reference question/answer pairs with known correct outputs, used to measure agent quality over time.',
    example: '50 hand-labeled Q&As. Run the agent weekly. Alert if accuracy drops below 85%.',
  },
  'a/b testing': {
    short: 'Comparing two variants (A and B) by routing some traffic to each and measuring which performs better.',
    example: 'Route 10% of traffic to a new system prompt. If evaluation scores improve, roll it out to 100%.',
  },
  'precision': {
    short: 'Of all the items your system labeled as positive, what fraction actually were positive? High precision = few false alarms.',
    example: 'Spam filter flags 100 emails as spam. 90 were actually spam. Precision = 90/100 = 90%.',
  },
  'recall': {
    short: 'Of all the items that were actually positive, what fraction did your system find? High recall = few misses.',
    example: 'There were 200 spam emails. The filter caught 90. Recall = 90/200 = 45%.',
  },
}

// Returns null if term not found
export function lookupTerm(term: string): GlossaryEntry | null {
  return glossary[term.toLowerCase()] ?? null
}
