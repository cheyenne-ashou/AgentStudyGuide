export type Snippet = {
  code: string
  label?: string // small label shown above the snippet
}

export type Concept = {
  title: string
  body: string // plain text, will be annotated
  snippet?: Snippet
}

export type Lesson = {
  id: string        // matches home page item id (e.g. 'w1-1')
  slug: string      // URL slug
  title: string
  file?: string     // path relative to agentic/ root — read from disk at request time
  weekLabel: string
  noApi: boolean
  intro: string
  concepts: Concept[]
  interviewTips: string[]
  gotchas: string[]
  relatedIds: string[]
}

export const lessons: Lesson[] = [
  // ── Week 1 — Foundations ────────────────────────────────────────────────────

  {
    id: 'w1-1',
    slug: 'prompting-strategies',
    title: 'Prompting Strategies',
    file: '01_foundations/llm_basics/prompting_strategies.py',
    weekLabel: 'Week 1 — Foundations',
    noApi: false,
    intro:
      'How you phrase a question to an LLM dramatically changes the quality of its answer. Four prompting strategies represent increasing levels of guidance, each suited to different tasks. Understanding these is the baseline skill for everything else in agentic AI.',
    concepts: [
      {
        title: 'Zero-shot',
        body: 'You ask the model directly with no examples and no special instructions. Simple and fast, but unreliable on multi-step or ambiguous tasks because the model has to infer your intent from scratch. Best for: simple factual questions, straightforward rewrites, tasks the model does well natively.',
        snippet: {
          label: 'Zero-shot — LCEL chain',
          code: `from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# chain = prompt_template | llm | parser
chain = ChatPromptTemplate.from_messages([
    ("human", "{task}"),
]) | get_fast_llm() | StrOutputParser()

result = chain.invoke({"task": task})
# No examples, no format hints — model guesses your intent`,
        },
      },
      {
        title: 'Few-shot',
        body: 'You provide 2-5 worked examples in the prompt before asking your question. The model learns the pattern (format, reasoning style, output structure) from your examples and applies it to the new input. Dramatically improves consistency on tasks with a specific format. Best for: classification, structured extraction, format-sensitive generation.',
        snippet: {
          label: 'Few-shot — examples before the question',
          code: `prompt = (
    "Q: Pens cost $1 each. I buy 3. Total?\\n"
    "A: 3 × $1 = $3.00\\n\\n"
    "Q: Oranges at $0.75, I buy 4. Total?\\n"
    "A: 4 × $0.75 = $3.00\\n\\n"
    f"Q: {task}\\n"
    "A:"  # model continues the pattern
)`,
        },
      },
      {
        title: 'Chain-of-Thought (CoT)',
        body: 'Ask the model to reason step-by-step before giving a final answer. Adding "Let\'s think step by step" or "Think through this carefully" forces the model to decompose the problem before committing to an answer. Research shows CoT reduces errors on multi-step reasoning tasks by 30-50%. Why? Because the model can\'t take shortcuts — it has to show its work.',
        snippet: {
          label: 'CoT — force intermediate reasoning',
          code: `prompt = f"{task}\\n\\nLet's think step by step."
# Model now outputs reasoning first, THEN the answer
# This single phrase reliably improves math, logic, planning tasks`,
        },
      },
      {
        title: 'ReAct (Reason + Act)',
        body: 'ReAct interleaves reasoning (Thought) with actions (Action/tool calls) and observations (results). Unlike CoT which is pure reasoning, ReAct allows the model to gather information mid-reasoning by calling tools. This is the foundation of all agentic AI — every agent framework implements a variation of this loop. The model thinks, acts, sees the result, thinks again, acts again, until done.',
        snippet: {
          label: 'ReAct — LangGraph StateGraph',
          code: `from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, create_react_agent

# The graph IS the ReAct loop
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)     # Thought: call LLM
workflow.add_node("tools", ToolNode(tools)) # Action: execute tool
workflow.add_conditional_edges("agent",    # Observation: route
    lambda s: "tools" if s["messages"][-1].tool_calls else END
)
workflow.add_edge("tools", "agent")        # repeat
agent = workflow.compile()

# Or the one-liner shorthand:
agent = create_react_agent(get_llm(), tools=[calculator, web_search])`,
        },
      },
      {
        title: 'Which strategy to use?',
        body: 'Zero-shot for simple tasks. Few-shot when you need specific output format or style consistency. CoT for multi-step reasoning (math, logic, planning) without tools. ReAct whenever the model needs to interact with external data or systems. In practice, most production agents use ReAct with a system prompt that also uses CoT-style reasoning.',
      },
    ],
    interviewTips: [
      '"Why does chain-of-thought work?" — It forces intermediate reasoning steps before committing. The model can\'t take shortcuts. Research shows it reduces errors by 30-50% on complex reasoning tasks.',
      '"What\'s the difference between CoT and ReAct?" — CoT is pure reasoning in the prompt. ReAct allows the model to take real actions (call tools, get results) between reasoning steps.',
      '"When would you use few-shot over zero-shot?" — Anytime you need a consistent output format, specific style, or the zero-shot result is unreliable. Examples are cheap to add.',
      '"What prompting strategy do agents use?" — ReAct. The Thought/Action/Observation loop IS the agent loop.',
    ],
    gotchas: [
      "Don't use CoT for simple tasks (\"what's 2+2?\") — it adds tokens without helping and sometimes makes the model second-guess correct answers.",
      "Few-shot examples must match your actual use case. Wrong examples mislead the model more than no examples.",
      "ReAct in LangGraph uses @tool functions + ToolNode — not text Thought/Action/Observation formatting. The text format is conceptual; the graph edges are the real loop.",
    ],
    relatedIds: ['w1-2', 'w1-3', 'w2-8'],
  },

  {
    id: 'w1-2',
    slug: 'temperature-demo',
    title: 'Temperature & Determinism',
    file: '01_foundations/llm_basics/temperature_demo.py',
    weekLabel: 'Week 1 — Foundations',
    noApi: false,
    intro:
      'Temperature controls the randomness of LLM outputs by reshaping the probability distribution over possible next tokens. Understanding this is essential: the wrong temperature setting is a subtle bug that produces inconsistent or hallucinated outputs.',
    concepts: [
      {
        title: 'How temperature works',
        body: 'At each step, the model assigns a probability to every possible next token. Temperature is a divisor applied before sampling: high temperature flattens the distribution (more random), low temperature sharpens it (more deterministic). At exactly t=0, the model always picks the single highest-probability token — this is called greedy decoding and is perfectly reproducible.',
        snippet: {
          label: 'Setting temperature with ChatAnthropic',
          code: `from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

# Instantiate with explicit temperature
llm = ChatAnthropic(model=FAST_MODEL, temperature=0.0)
response = llm.invoke([HumanMessage(content=PROMPT)])
# response.content is the string output

# Or change temperature per-call without rebuilding:
result = llm.with_config({"temperature": 0.7}).invoke([...])`,
        },
      },
      {
        title: 't=0 — Deterministic (Greedy)',
        body: 'Always picks the highest-probability next token. Given identical input, produces identical output every time. This is what you want for: structured extraction, tool calling, JSON generation, evaluation runs, anything where you need reproducibility. A subtle bug: if your agent uses t=0.7 for tool calls, sometimes it hallucinates tool names or generates invalid JSON arguments.',
      },
      {
        title: 't=0.7 — Balanced (Default)',
        body: 'The sweet spot for most conversational use cases. Tokens are sampled proportionally to their probability, with a slight sharpening effect. Produces natural variation without being erratic. This is the default in most LLM APIs. Use for: chat, explanations, brainstorming, creative writing assistance.',
      },
      {
        title: 't=1.0 — Maximum Randomness',
        body: 'Samples directly from the raw probability distribution with no sharpening. Produces the most varied output — every run is different. Use for: creative writing, generating diverse options, data augmentation. Avoid for anything where correctness matters, since the model is equally likely to pick unlikely tokens.',
      },
      {
        title: 'Temperature in agentic systems',
        body: 'The best practice in production agents is to use t=0 for any tool-calling turn (the model decides which tool to call with what arguments) and t=0.7 for synthesis turns (the model writes a human-readable answer). This reduces tool call errors while keeping responses natural. Some teams use a lower temperature (0.2–0.4) for synthesis to reduce hallucination risk.',
      },
    ],
    interviewTips: [
      '"What temperature do you use for tool calling?" — Always t=0. You want deterministic, valid JSON arguments. Higher temperatures increase the chance of malformed tool inputs.',
      '"How do you make agent runs reproducible?" — Use t=0 throughout the agent loop. Log the full messages array (input + output) so you can replay it exactly.',
      '"What\'s top-p sampling?" — An alternative to temperature that truncates the distribution to the top tokens until their cumulative probability reaches p. Similar effect to temperature but approaches it differently. Usually you only need one or the other.',
    ],
    gotchas: [
      'Some models clamp temperature=0 to a minimum internally — always verify reproducibility by running the same prompt twice and comparing outputs.',
      'Temperature only affects sampling. If the model\'s training strongly favors one answer, even t=1.0 will mostly produce that answer.',
      "Don't confuse temperature (randomness) with quality. Lower temperature ≠ better answer. It just means more predictable answer.",
    ],
    relatedIds: ['w1-1', 'w1-3', 'w2-8'],
  },

  {
    id: 'w1-3',
    slug: 'hallucination-demo',
    title: 'Hallucinations & Mitigations',
    file: '01_foundations/llm_basics/hallucination_demo.py',
    weekLabel: 'Week 1 — Foundations',
    noApi: false,
    intro:
      'Hallucination is the #1 reliability problem in production LLM systems. The model generates fluent, confident-sounding text that is factually wrong. Understanding why it happens and how to reduce it is a core interview topic.',
    concepts: [
      {
        title: 'Why LLMs hallucinate',
        body: 'LLMs are trained to predict the most likely next token — not to be factually accurate. They learned patterns from text, so they produce text that looks like what comes after the previous words. When asked about something rare (like a fictional company), the model generates plausible-sounding details by pattern-matching to similar real entities. There is no internal "I don\'t know" signal — the model always outputs something.',
      },
      {
        title: 'Mitigation 1: RAG (Retrieval-Augmented Generation)',
        body: 'The most effective mitigation for factual questions. Instead of relying on training knowledge, retrieve real documents and inject them as context before generating. The model is instructed to answer only from the provided context. If the context doesn\'t contain the answer, the model (correctly) says so. This is why RAG is so widely used — it grounds every answer in real, verifiable sources.',
        snippet: {
          label: 'RAG: constrain model to retrieved context',
          code: `prompt = (
    "Answer ONLY based on the provided context.\\n"
    "If the context doesn't contain the answer, say so.\\n\\n"
    f"Context:\\n{retrieved_docs}\\n\\n"
    f"Question: {question}"
)`,
        },
      },
      {
        title: 'Mitigation 2: Uncertainty prompting',
        body: 'Explicitly instruct the model in the system prompt to express uncertainty rather than guess. Add: "If you are not certain about a fact, say \'I don\'t have reliable information about this.\'" This exploits the model\'s instruction-following to self-censor low-confidence claims. Less reliable than RAG but useful as an additional layer.',
        snippet: {
          label: 'Uncertainty instruction in system prompt',
          code: `system = (
    "If you do not have reliable information about something, "
    "say 'I don't have reliable information about this' "
    "rather than guessing."
)`,
        },
      },
      {
        title: 'Mitigation 3: Structured outputs',
        body: 'If you force the model to answer in a strict JSON schema, it cannot freely invent details — it can only fill in the defined fields. A field like {"confidence": 0-1} gives you a signal to threshold on. Combined with Pydantic validation, invalid outputs are caught and re-prompted.',
      },
      {
        title: 'Mitigation 4: Temperature 0 + grounding',
        body: 'Lower temperature reduces creative confabulation but doesn\'t eliminate hallucination on unknown facts. Grounding (providing real context) is the only reliable approach. Think of temperature as reducing the spread of hallucination, while RAG reduces the probability.',
      },
    ],
    interviewTips: [
      '"Why do LLMs hallucinate?" — They\'re trained to generate plausible next tokens, not to verify facts. There\'s no internal uncertainty signal. The model interpolates between training examples when it encounters unfamiliar inputs.',
      '"How do you reduce hallucinations in production?" — Layer multiple mitigations: RAG to ground factual answers, structured outputs to constrain what the model can say, uncertainty prompting as a fallback, and human review for high-stakes outputs.',
      '"Is RAG always the answer?" — RAG helps with factual grounding. For hallucinations caused by bad reasoning (not wrong facts), CoT prompting and structured outputs are more useful.',
    ],
    gotchas: [
      "Don't rely on a single mitigation. Layers are essential because each mitigation has failure modes.",
      'Models can hallucinate even with RAG context if the retrieved docs are misleading or the model misreads them. Always cite sources so users can verify.',
      'Asking the model to rate its own confidence is unreliable — models are often confidently wrong. Use cross-referencing or human review for high stakes.',
    ],
    relatedIds: ['w1-1', 'w1-7', 'w3-5'],
  },

  {
    id: 'w1-4',
    slug: 'cosine-similarity',
    title: 'Cosine Similarity & Vectors',
    file: '01_foundations/embeddings/cosine_similarity.py',
    weekLabel: 'Week 1 — Foundations',
    noApi: true,
    intro:
      'Embeddings represent the meaning of text as a point in high-dimensional space. Cosine similarity measures how close two points are — and therefore how semantically similar two texts are. This math underlies all of semantic search, RAG, and vector databases.',
    concepts: [
      {
        title: 'What is an embedding?',
        body: 'An embedding model converts text into a list of numbers (a vector) where semantically similar texts produce numerically similar vectors. The dimensions don\'t have interpretable meaning individually — they collectively encode "what this text is about." Modern embeddings typically have 768–3072 dimensions. The key property: you can compute semantic similarity by comparing vectors, without any understanding of language.',
        snippet: {
          label: 'Conceptual: text → numbers',
          code: `# These are hand-crafted 4D vectors for illustration
# Real embeddings have 768-3072 dimensions
CONCEPTS = {
    "dog":      [0.9, 0.85, 0.0, 0.0],  # animal, domestic, not-software
    "cat":      [0.85, 0.9, 0.0, 0.0],  # similar to dog
    "python_lang": [0.0, 0.0, 0.9, 0.8],  # very different from dog
}`,
        },
      },
      {
        title: 'The cosine similarity formula',
        body: 'cosine_similarity(A, B) = dot_product(A, B) / (magnitude(A) × magnitude(B)). The result is between -1 and 1: 1 means identical direction (same concept), 0 means orthogonal (unrelated), -1 means opposite. The magnitude normalization is the key insight: it makes the measure scale-invariant. A short document and a long document about the same topic score the same.',
        snippet: {
          label: 'Cosine similarity from scratch',
          code: `import math

def dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))

def magnitude(v):
    return math.sqrt(sum(x**2 for x in v))

def cosine_similarity(a, b):
    mag = magnitude(a) * magnitude(b)
    return 0.0 if mag == 0 else dot_product(a, b) / mag

# dog vs cat → ~0.99 (very similar)
# dog vs python_lang → ~0.0 (unrelated)`,
        },
      },
      {
        title: 'Why cosine over Euclidean distance?',
        body: 'Euclidean distance measures the absolute distance between two points. Cosine similarity measures the angle between them. The difference matters because a short document and a long document about the same topic have vectors pointing in the same direction, but the long document\'s vector is larger in magnitude. Euclidean distance would say they\'re far apart; cosine similarity correctly says they\'re the same topic.',
        snippet: {
          label: 'Why magnitude-invariance matters',
          code: `short_dog = [0.9, 0.85, 0.0, 0.0]   # same direction as dog
long_dog  = [9.0, 8.5, 0.0, 0.0]    # 10× larger, same direction

cosine_similarity(CONCEPTS["dog"], short_dog)  # → 1.000 ✓
cosine_similarity(CONCEPTS["dog"], long_dog)   # → 1.000 ✓

# Euclidean would be very different:
euclidean(short_dog, long_dog)  # → large number (far apart) ✗`,
        },
      },
      {
        title: 'Practical range',
        body: 'In practice, embeddings of natural text rarely produce negative cosine similarity. You\'ll typically see: 0.9–1.0 for nearly identical sentences, 0.7–0.9 for same topic/concept, 0.5–0.7 for related but different, 0.0–0.5 for unrelated. Different embedding models have different score ranges — always calibrate thresholds against your specific model and dataset.',
      },
    ],
    interviewTips: [
      '"Why do we use cosine similarity instead of Euclidean distance for embeddings?" — Cosine is magnitude-invariant. Long and short texts about the same topic get the same similarity score. Euclidean would penalize longer documents.',
      '"What does a cosine similarity of 0.85 mean?" — The two vectors point in roughly the same direction. In practice, this usually means the texts are about the same topic with different wording.',
      '"How do you find the most similar document to a query?" — Embed both, compute cosine similarity against all stored embeddings, return the top-k highest scores. In production, use ANN (approximate nearest neighbor) indexes like HNSW for speed.',
    ],
    gotchas: [
      'Cosine similarity is not a probability — 0.85 does not mean "85% chance they\'re related". It\'s a relative score. Use it for ranking, not thresholding without calibration.',
      'Different embedding models are not comparable. A score of 0.7 from model A ≠ 0.7 from model B.',
      'Always use the same embedding model for both documents and queries. Mixing models produces meaningless scores.',
    ],
    relatedIds: ['w1-5', 'w1-6', 'w2-5'],
  },

  {
    id: 'w1-5',
    slug: 'chunking-strategies',
    title: 'Chunking Strategies',
    file: '01_foundations/embeddings/chunking_strategies.py',
    weekLabel: 'Week 1 — Foundations',
    noApi: true,
    intro:
      'Before you can embed and search documents, you must split them into chunks. Chunking strategy is the #1 tuning knob in RAG systems. Getting it wrong produces irrelevant retrieval results, which produces bad answers — even with a great LLM.',
    concepts: [
      {
        title: 'Why chunking matters',
        body: 'You can\'t embed an entire book as one vector — a 50,000-word document would average out to a semantically meaningless vector, and the retrieved context would be too long to process. You need pieces small enough to be precise in retrieval, but large enough to contain full context. The tradeoff: smaller chunks = higher retrieval precision but lose context; larger chunks = better context but add noise.',
      },
      {
        title: 'Strategy 1: Fixed-size',
        body: 'Split every N words regardless of sentence/paragraph boundaries. Simple and predictable but often cuts mid-sentence, losing context across the boundary. Use when: you have unstructured text with no clear structure, simplicity matters more than quality, or you\'re prototyping.',
        snippet: {
          label: 'Fixed-size chunking',
          code: `def fixed_size(text, words_per_chunk=40):
    words = text.split()
    return [
        " ".join(words[i:i+words_per_chunk])
        for i in range(0, len(words), words_per_chunk)
    ]
# Pro: simple, predictable
# Con: cuts mid-sentence, loses cross-boundary context`,
        },
      },
      {
        title: 'Strategy 2: Sliding window (with overlap)',
        body: 'Like fixed-size but each chunk overlaps the previous by N words. This ensures that context around chunk boundaries is captured in at least one chunk. The cost: roughly (1 + overlap/chunk_size)× more chunks to store and search. A 15% overlap is a common default. This is the best general-purpose strategy.',
        snippet: {
          label: 'Sliding window with overlap',
          code: `def sliding_window(text, chunk_words=40, overlap=10):
    words = text.split()
    step = chunk_words - overlap  # move forward by (chunk - overlap)
    return [
        " ".join(words[i:i+chunk_words])
        for i in range(0, len(words), step)
    ]
# 10-word overlap on 40-word chunks = 25% overlap, ~1.3× more chunks`,
        },
      },
      {
        title: 'Strategy 3: Sentence boundary',
        body: 'Split on punctuation (., !, ?) to preserve semantic units. Each chunk contains complete sentences, which tend to embed better than sentence fragments. Variable chunk sizes can complicate batching, but the semantic coherence gain is worth it for most use cases.',
      },
      {
        title: 'Strategy 4: Paragraph/section boundary',
        body: 'Split on blank lines or section headers. Best for structured documents (product docs, API references, legal text). Produces the most semantically coherent chunks because paragraphs are written to express one idea. Chunks can be large (500+ words), which may reduce retrieval precision.',
      },
      {
        title: 'Choosing chunk size',
        body: 'Rule of thumb: 80-150 words with 10-15% overlap is a solid general default. Smaller (50-80 words) for precision-critical retrieval (e.g., finding specific facts). Larger (200-400 words) when the query needs broader context (e.g., summarization-based RAG). Always benchmark on your actual queries and documents — there is no universally optimal size.',
      },
    ],
    interviewTips: [
      '"What chunking strategy would you use for a RAG system over technical documentation?" — Sentence-aware chunking with 100-150 word chunks and 15% overlap. Sentence boundaries preserve semantic units; overlap prevents boundary artifacts.',
      '"What happens if your chunk size is too small?" — Higher retrieval precision but you lose cross-sentence context. The retrieved chunk may not have enough information to answer the question.',
      '"What happens if your chunk size is too large?" — Each chunk covers too many topics, so the embedding is diluted. The LLM gets more text but most of it is irrelevant to the query.',
    ],
    gotchas: [
      "Chunking strategy and retrieval quality are tightly coupled. Don't tune one without re-evaluating the other.",
      "Overlapping chunks increase your vector DB size and search time linearly with the overlap ratio. 50% overlap doubles your storage.",
      "Metadata matters. Always store {source, chunk_index, total_chunks} so you can display citations and re-assemble context when needed.",
    ],
    relatedIds: ['w1-4', 'w1-6', 'w4-4'],
  },

  {
    id: 'w1-6',
    slug: 'vector-search-demo',
    title: 'Vector Search with ChromaDB',
    file: '01_foundations/embeddings/vector_search_demo.py',
    weekLabel: 'Week 1 — Foundations',
    noApi: true,
    intro:
      'Vector search finds documents by semantic similarity rather than exact keyword matching. ChromaDB provides a local, in-process vector database — no infrastructure needed for development. This demo shows the full search cycle: embed, store, query, score.',
    concepts: [
      {
        title: 'How vector search works',
        body: 'You provide a query string. The embedding model converts it to a vector. The vector database computes cosine similarity (or L2 distance) between your query vector and every stored document vector, then returns the top-k most similar. The key insight: the query and the document don\'t share any words — they just need to be semantically close.',
      },
      {
        title: 'ChromaDB setup',
        body: 'ChromaDB has two modes: EphemeralClient (in-memory, lost on restart) for demos, and PersistentClient (stored on disk) for real projects. Collections are like tables. You choose an embedding function when creating a collection. Using SentenceTransformerEmbeddingFunction with "all-MiniLM-L6-v2" gives fast, free, local embeddings with no API key.',
        snippet: {
          label: 'Create a ChromaDB collection',
          code: `import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
client = chromadb.EphemeralClient()  # in-memory

collection = client.create_collection(
    "my_docs",
    embedding_function=ef,
    metadata={"hnsw:space": "cosine"},  # use cosine similarity
)`,
        },
      },
      {
        title: 'Ingest and query',
        body: 'Add documents with unique IDs. ChromaDB automatically embeds them using your configured embedding function. Querying returns documents, distances (or similarities), and metadata. With cosine space, distance ≈ 1 - similarity, so a distance of 0.1 means 0.9 similarity.',
        snippet: {
          label: 'Add documents and search',
          code: `# Ingest
collection.add(
    ids=["doc1", "doc2", "doc3"],
    documents=["Agents use tools...", "RAG retrieves docs...", "..."],
)

# Query — no exact keywords needed
results = collection.query(
    query_texts=["How do AI agents interact with external services?"],
    n_results=3,
)
# Returns: documents, distances, ids, metadatas`,
        },
      },
      {
        title: 'Score interpretation',
        body: 'The returned distances in cosine space range from 0 (identical) to 2 (opposite). Convert to similarity: similarity = 1 - distance. In practice, top results from a good query typically score 0.7-0.95. Results below 0.5 are usually not relevant. Set a minimum similarity threshold (e.g., 0.6) to avoid returning unrelated chunks.',
      },
      {
        title: 'From ChromaDB to production',
        body: 'ChromaDB is excellent for development. Production systems typically use: Pinecone (managed, fast, expensive), Weaviate (open-source, hybrid search built-in), pgvector (PostgreSQL extension, if you\'re already using Postgres), or Qdrant (fast, open-source). The concepts are identical — collection, embed, store, query. Just the infrastructure changes.',
      },
    ],
    interviewTips: [
      '"What embedding model do you use?" — For production: voyage-3 (Anthropic/Voyage) or text-embedding-3-large (OpenAI) for quality. For development: all-MiniLM-L6-v2 (local, free, fast).',
      '"How do you set a relevance threshold?" — Compute similarity on a sample of known-relevant and known-irrelevant queries. Find the score that separates them. Typical cutoff: 0.5-0.7 depending on the domain.',
      '"How does ChromaDB store embeddings on disk?" — It uses SQLite for metadata and a file-based HNSW index for vectors. PersistentClient writes both to a directory.',
    ],
    gotchas: [
      'EphemeralClient loses data on process restart. Use PersistentClient for any real project.',
      "The embedding function must be the same for both ingestion and querying. Switching models requires re-embedding everything.",
      'ChromaDB is single-process. For multi-worker production deployments, use a managed vector DB or a server-mode database.',
    ],
    relatedIds: ['w1-4', 'w1-5', 'w2-5'],
  },

  {
    id: 'w1-7',
    slug: 'rag-vs-finetuning',
    title: 'RAG vs Fine-tuning vs Prompting',
    file: '01_foundations/ml_concepts/rag_vs_finetuning.py',
    weekLabel: 'Week 1 — Foundations',
    noApi: false,
    intro:
      '"RAG vs fine-tuning" is a guaranteed interview question. Understanding when to use each — and why — demonstrates that you\'re thinking about real system constraints, not just plugging in the newest model.',
    concepts: [
      {
        title: 'Prompting (baseline)',
        body: 'Just write a good prompt and call the LLM. No special data pipeline, no training. The model uses only its training knowledge. Works for: general tasks well-covered by training data, tasks where exact format doesn\'t matter, prototyping. Fails for: private data, knowledge cutoff issues, highly specific formats.',
        snippet: {
          label: 'Prompting — LCEL chain',
          code: `from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# No data pipeline needed, no training cost
chain = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
]) | get_llm() | StrOutputParser()

answer = chain.invoke({"question": question})
# Cheap, fast, but limited to training knowledge`,
        },
      },
      {
        title: 'RAG (Retrieval-Augmented Generation)',
        body: 'Build an index of your documents, retrieve the relevant ones at query time, inject them as context. Best when: knowledge changes frequently (prices, documentation, news), you need citations/source attribution, you have private data not in training, reducing hallucinations is critical. Cost: retrieval latency (50-200ms), storage for embeddings, embedding compute.',
      },
      {
        title: 'Fine-tuning',
        body: 'Train the model further on your domain-specific data to change its behavior, vocabulary, or output style. Best when: specific output format the model doesn\'t naturally produce, highly specialized vocabulary (medical, legal, financial), you have thousands of labeled examples, and prompt engineering has hit a ceiling. Cost: GPU compute ($100s-$1000s), data labeling, slower iteration.',
      },
      {
        title: 'Decision framework',
        body: 'Start with prompting. If outputs are inconsistent in format → try few-shot or fine-tuning. If outputs hallucinate due to missing knowledge → use RAG. If both are problems → combine RAG + fine-tuning. If latency/cost at scale is the issue → fine-tune a smaller model and use it instead of the large one. Fine-tuning a 7B model can match GPT-4 on specific tasks at 100× lower inference cost.',
      },
      {
        title: 'Combining RAG + fine-tuning',
        body: 'Not mutually exclusive. Fine-tune for output format and domain tone; use RAG for dynamic knowledge injection. Example: a customer support bot fine-tuned on your brand voice + RAG over your product documentation. This is the production setup at most mature AI companies.',
      },
    ],
    interviewTips: [
      '"RAG vs fine-tuning, what do you choose?" — RAG for dynamic knowledge, citations, private data. Fine-tuning for output format, style, specialized vocabulary. In practice, most systems use both.',
      '"When does fine-tuning make sense over prompt engineering?" — When you need consistent output format, domain vocabulary, or specific behavior that you can\'t achieve reliably with prompts — and you have enough labeled data (typically 500-5000 examples).',
      '"What are the risks of fine-tuning?" — Knowledge cutoff moves to when you fine-tuned. Catastrophic forgetting (model loses general capability). Hard to update without retraining. Overfitting to your dataset.',
    ],
    gotchas: [
      "Fine-tuning is not magic. If your base model doesn't understand your domain at all, fine-tuning won't fix it — you might need a domain-specific pretrained model.",
      "RAG precision depends entirely on your chunking and retrieval quality. Poor retrieval → bad answers, regardless of how good the LLM is.",
      'Many teams reach for fine-tuning too early. Exhausting prompt engineering and few-shot examples first is almost always worth it — it\'s faster and cheaper.',
    ],
    relatedIds: ['w1-1', 'w1-3', 'w1-6'],
  },

  {
    id: 'w1-8',
    slug: 'evaluation-metrics',
    title: 'Evaluation Metrics',
    file: '01_foundations/ml_concepts/evaluation_metrics.py',
    weekLabel: 'Week 1 — Foundations',
    noApi: true,
    intro:
      'You can\'t improve what you can\'t measure. Evaluation metrics let you objectively compare different prompts, models, or system configurations. Know these cold — they appear in every "how do you evaluate your agent?" question.',
    concepts: [
      {
        title: 'Precision and Recall',
        body: 'The two fundamental metrics for any retrieval or classification task. Precision = of everything you returned, what fraction was relevant? Recall = of everything that was relevant, what fraction did you find? They pull against each other — optimizing for recall (find everything) usually hurts precision (introduce false positives) and vice versa.',
        snippet: {
          label: 'Precision and Recall formulas',
          code: `# TP = true positive, FP = false positive, FN = false negative
def precision(tp, fp):
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0

def recall(tp, fn):
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0

def f1(precision, recall):
    return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0`,
        },
      },
      {
        title: 'F1 Score',
        body: 'The harmonic mean of precision and recall. Use it when you want to balance both. The harmonic mean penalizes large gaps between precision and recall — a system with 100% precision but 1% recall gets F1 ≈ 0.02, not 0.5.',
      },
      {
        title: 'BLEU Score',
        body: 'Measures text generation quality by comparing n-gram overlap between a generated text and a reference. BLEU-1 looks at unigrams (individual words), BLEU-4 looks at 4-word sequences. Originally designed for machine translation. Rough but fast. Key limitation: doesn\'t measure meaning, only surface overlap — "The cat sat" and "A feline rested" score low even though they mean the same thing.',
        snippet: {
          label: 'BLEU-1 (unigram overlap)',
          code: `def bleu_1(hypothesis, reference):
    hyp_tokens = hypothesis.lower().split()
    ref_counts = Counter(reference.lower().split())
    matches = 0
    for token in hyp_tokens:
        if ref_counts.get(token, 0) > 0:
            matches += 1
            ref_counts[token] -= 1  # clip to reference count
    precision = matches / len(hyp_tokens) if hyp_tokens else 0
    # Apply brevity penalty for short outputs
    bp = 1.0 if len(hyp_tokens) >= len(reference.split()) else ...
    return bp * precision`,
        },
      },
      {
        title: 'RAG-specific metrics: Context Recall and Precision',
        body: 'For RAG systems, you need to evaluate the retrieval step separately from generation. Context recall = of all truly relevant chunks, what fraction did you retrieve? Context precision = of all retrieved chunks, what fraction were actually relevant? Low context recall means your agent is missing important information. Low context precision means it\'s receiving noise that confuses the LLM.',
      },
      {
        title: 'LLM-as-judge',
        body: 'Use a second LLM call to grade the quality of the first LLM\'s output: "Rate this answer 0-10 on these criteria." More nuanced than keyword matching or BLEU, handles paraphrase and semantic equivalence. The main risk: the judge model has biases. Calibrate by checking agreement with human judgments. This is now the standard approach for evaluating free-form LLM outputs.',
      },
    ],
    interviewTips: [
      '"How do you evaluate a RAG pipeline?" — Separately evaluate retrieval (context recall/precision) and generation (LLM-as-judge or human eval). A bad retrieval step poisons the generation regardless of model quality.',
      '"When do you use precision vs recall?" — Precision when false positives are costly (spam filter, medical alerts). Recall when false negatives are costly (fraud detection, safety systems).',
      '"What\'s wrong with BLEU for evaluating LLM outputs?" — It measures surface overlap, not meaning. Two semantically identical sentences with different words score 0. Use LLM-as-judge for semantic evaluation.',
    ],
    gotchas: [
      "Don't compare absolute metric values across different test sets. Always track delta (did your change improve metrics?) on the same held-out set.",
      'ROUGE is similar to BLEU but recall-oriented. Better for summarization evaluation. Know BLEU for generation, ROUGE for summarization.',
      "LLM-as-judge costs money and adds latency to your eval pipeline. Cache judgments and only re-evaluate on changed questions.",
    ],
    relatedIds: ['w1-7', 'w4-1', 'w4-2'],
  },

  // ── Week 2 — Agentic Core ──────────────────────────────────────────────────

  {
    id: 'w2-1',
    slug: 'tool-registry',
    title: 'The @tool Decorator Pattern',
    file: '02_agentic_core/tool_use/tool_registry.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: true,
    intro:
      'LangGraph tools are plain Python functions decorated with @tool. The decorator reads the docstring and function signature to build the JSON schema automatically — no hand-written schemas needed. ToolNode dispatches calls at runtime. Understanding this pattern is foundational for every LangGraph agent.',
    concepts: [
      {
        title: 'The @tool decorator',
        body: 'Decorate any Python function with @tool. LangChain reads the docstring (becomes the tool description) and type annotations (become the JSON schema). The result is a BaseTool that bind_tools() can attach to any LLM. Zero boilerplate — just write the function.',
        snippet: {
          label: '@tool — docstring becomes description, signature becomes schema',
          code: `from langchain_core.tools import tool
import math

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Supports +, -, *, /, **, sqrt, log."""
    try:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return str(result)
    except Exception as e:
        return f"Error: {e}"

@tool
def get_datetime() -> str:
    """Get the current UTC date, time, and day of week."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M:%S UTC")`,
        },
      },
      {
        title: 'bind_tools() — attach tools to the LLM',
        body: 'Call llm.bind_tools(tools) to return a new LLM Runnable that knows about the tool schemas. When invoked, the LLM can produce AIMessages with a .tool_calls list. This is how the agent "knows" which tools exist.',
        snippet: {
          label: 'bind_tools — attach schemas to the LLM',
          code: `tools = [calculator, get_datetime, web_search]

# Returns a new Runnable — does not mutate the original llm
llm_with_tools = get_llm().bind_tools(tools)

# When invoked, response.tool_calls may be non-empty
response = llm_with_tools.invoke([HumanMessage(content="What is 25 * 47?")])
print(response.tool_calls)
# [{"name": "calculator", "args": {"expression": "25 * 47"}, "id": "..."}]`,
        },
      },
      {
        title: 'ToolNode — automatic dispatch',
        body: 'ToolNode is a pre-built LangGraph node. It reads response.tool_calls from the last AIMessage, calls the matching tool function, and returns a list of ToolMessages. Plug it into a StateGraph as the "tools" node — it replaces the entire manual dispatch loop.',
        snippet: {
          label: 'ToolNode — one line replaces the dispatch loop',
          code: `from langgraph.prebuilt import ToolNode

tool_node = ToolNode(tools)  # knows about all @tool functions

# In a StateGraph:
workflow.add_node("tools", tool_node)
# On each invocation, ToolNode reads tool_calls from the last AIMessage,
# executes each tool, and returns ToolMessages with the results`,
        },
      },
      {
        title: 'Manual ABC registry vs @tool (reference)',
        body: 'The tool_registry.py file still shows the manual ABC pattern (Tool class + ToolRegistry) for reference. It demonstrates what @tool automates: name property → function name, description property → docstring, input_schema → type annotations, run() method → function body, to_claude_tools() → bind_tools(). Understanding the manual version helps you debug schema issues.',
        snippet: {
          label: 'What @tool replaces',
          code: `# OLD: hand-written ABC (still in tool_registry.py for reference)
class CalculatorTool(Tool):
    @property
    def name(self): return "calculator"
    @property
    def description(self): return "Evaluate a math expression."
    @property
    def input_schema(self): return {"type":"object","properties":{"expression":{"type":"string"}},"required":["expression"]}
    def run(self, expression): ...

# NEW: @tool decorator (everything above is auto-generated)
@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    ...`,
        },
      },
    ],
    interviewTips: [
      '"How do tools work in LangGraph?" — Decorate Python functions with @tool. Call llm.bind_tools(tools) to attach schemas. ToolNode in the StateGraph dispatches calls automatically.',
      '"How do you add a new tool without changing agent code?" — Add a new @tool function to the tools list. rebind with bind_tools() and rebuild ToolNode. The StateGraph logic is unchanged.',
      '"How do you mock tools in tests?" — Swap the @tool function for a mock that returns deterministic values. Pass the mock list to ToolNode.',
    ],
    gotchas: [
      'The @tool docstring IS the description the LLM reads. A vague docstring → the LLM calls the tool incorrectly. Be specific.',
      'All parameters need type annotations. Missing types mean the JSON schema is incomplete, which causes the LLM to omit required arguments.',
      "Don't return complex objects from @tool — return strings. ToolNode passes the return value as a ToolMessage content string.",
    ],
    relatedIds: ['w2-2', 'w2-3', 'w2-8', 'w3-3'],
  },

  {
    id: 'w2-2',
    slug: 'sample-tools',
    title: 'Building Concrete Tools',
    file: '02_agentic_core/tool_use/sample_tools.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: true,
    intro:
      'Good tools are the difference between a useful agent and a useless one. This module shows how to build production-quality tools with input validation, safe evaluation, and clear error messages.',
    concepts: [
      {
        title: 'Safe expression evaluation',
        body: 'The naive eval(expression) approach executes arbitrary Python code — a huge security risk. Safe evaluation restricts available builtins to just the math module. No file access, no imports, no os commands. This is the right pattern for any tool that evaluates user-controlled expressions.',
        snippet: {
          label: 'Safe math evaluation',
          code: `import math

def run(self, expression: str) -> str:
    safe_globals = {"__builtins__": {}}  # no builtins = no os, no import
    safe_locals = {k: v for k, v in vars(math).items()
                   if not k.startswith("_")}
    try:
        result = eval(expression, safe_globals, safe_locals)
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as e:
        return f"Error: {e}"`,
        },
      },
      {
        title: 'Returning structured results',
        body: '@tool functions should return strings. ToolNode wraps the return value as a ToolMessage.content string. For structured data, serialize to JSON so the LLM can parse the individual values in its next reasoning step. Always return an error string (not raise an exception) if something goes wrong — let the agent decide what to do with the error.',
        snippet: {
          label: 'Return JSON string from a @tool function',
          code: `@tool
def word_count(text: str) -> str:
    """Count words, characters, and sentences in a text string."""
    import re, json
    words = len(text.split())
    chars = len(text)
    sentences = len(re.split(r"[.!?]+", text.strip())) - 1
    return json.dumps({"words": words, "characters": chars, "sentences": sentences})
# The LLM reads this JSON string and can reference individual fields`,
        },
      },
      {
        title: 'Unit conversion tool pattern',
        body: 'Tools with fixed mappings (unit conversion, currency, lookup tables) are the cleanest type to implement. Keep the mapping table in the class. Handle edge cases (temperature requires formulas, not simple multiplication). Always validate inputs before performing computation.',
      },
      {
        title: 'Mock tools for testing',
        body: 'For tools that call external APIs (web search, databases), always create mock versions for testing. The mock returns realistic-looking but controlled output. This lets you run your full agent loop in tests without external dependencies or API costs.',
        snippet: {
          label: 'Mock web search for testing',
          code: `class MockWebSearchTool(Tool):
    def run(self, query: str) -> str:
        # Realistic-looking stub output
        mock_db = {
            "python": "Python 3.13 is latest. Popular for ML/AI.",
            "fastapi": "FastAPI 0.115 — async web framework.",
        }
        for key, result in mock_db.items():
            if key in query.lower():
                return f"[Search: {query}] {result}"
        return f"[Search: {query}] 3 results found about {query}."`,
        },
      },
    ],
    interviewTips: [
      '"How do you handle tool errors in an agent?" — @tool functions return error strings, not raise exceptions. ToolNode passes the error string back as a ToolMessage, and the agent can retry with different inputs or try a different approach.',
      '"How do you prevent prompt injection through tool results?" — Validate and sanitize tool outputs before returning them. Truncate excessively long results. Consider a secondary validation prompt for high-risk tools.',
    ],
    gotchas: [
      'Never use bare eval() in a tool. Always restrict __builtins__ to prevent arbitrary code execution.',
      "@tool functions should be stateless between calls (except explicit memory tools). Shared module-level state causes bugs in multi-turn conversations.",
      "Always truncate tool output to a reasonable length. A web search tool returning 100,000 characters of HTML will overflow the context window.",
    ],
    relatedIds: ['w2-1', 'w2-3', 'w2-8'],
  },

  {
    id: 'w2-3',
    slug: 'function-calling',
    title: 'Function Calling End-to-End',
    file: '02_agentic_core/tool_use/function_calling.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: false,
    intro:
      'Function calling is the mechanism that gives agents their power. In LangGraph, it flows through three objects: bind_tools() tells the LLM what tools exist, AIMessage.tool_calls captures the model\'s request, and ToolNode executes it. Understanding this cycle is essential — StateGraph builds on top of it.',
    concepts: [
      {
        title: 'The 4-step LangGraph tool call cycle',
        body: '1. llm.bind_tools(tools) attaches schemas so the LLM knows what\'s available. 2. llm.invoke([message]) returns an AIMessage — if .tool_calls is non-empty, the model wants to call a tool. 3. ToolNode executes every tool in .tool_calls and returns ToolMessages. 4. Append both the AIMessage and the ToolMessages, then invoke the LLM again. Repeat until tool_calls is empty.',
      },
      {
        title: 'AIMessage.tool_calls — the routing signal',
        body: 'When the LLM decides to use a tool, it returns an AIMessage with .tool_calls populated. Each entry is a dict with name (which tool), args (the arguments), and id (unique call ID). The presence of .tool_calls is what the should_continue conditional edge in a StateGraph checks.',
        snippet: {
          label: 'Inspecting tool_calls on the response',
          code: `from langchain_core.messages import HumanMessage

llm_with_tools = get_llm().bind_tools([calculator, get_datetime])
response = llm_with_tools.invoke([HumanMessage(content="What is 847 ÷ 7?")])

print(response.tool_calls)
# [{"name": "calculator", "args": {"expression": "847 / 7"}, "id": "call_abc"}]

# No tool_calls means the LLM answered directly
if not response.tool_calls:
    print(response.content)  # final answer string`,
        },
      },
      {
        title: 'ToolNode — execute and return ToolMessages',
        body: 'ToolNode reads all entries in response.tool_calls, calls the matching @tool function for each, and returns a list of ToolMessages (one per call). Append both the AIMessage and the ToolMessages to the conversation, then call the LLM again.',
        snippet: {
          label: 'ToolNode executes all tool calls at once',
          code: `from langgraph.prebuilt import ToolNode

tool_node = ToolNode([calculator, get_datetime, unit_converter])

# tool_node.invoke([response]) returns a list of ToolMessages
tool_messages = tool_node.invoke([response])
for tm in tool_messages:
    print(f"{tm.name}: {tm.content}")
# calculator: 847 / 7 = 121.0

# Append both AIMessage and ToolMessages, then call LLM again
messages = [HumanMessage("..."), response] + tool_messages
final = llm_with_tools.invoke(messages)`,
        },
      },
      {
        title: 'Multi-turn loop (explicit)',
        body: 'String together multiple rounds until tool_calls is empty. This is the same logic that a LangGraph StateGraph encodes as nodes and edges — but written explicitly so you can see exactly what the graph is doing under the hood.',
        snippet: {
          label: 'Explicit multi-turn tool loop',
          code: `messages = [HumanMessage(content=query)]

for _ in range(MAX_STEPS):
    response = llm_with_tools.invoke(messages)
    messages.append(response)

    if not response.tool_calls:
        return response.content  # done!

    # Execute all tool calls in parallel via ToolNode
    tool_messages = tool_node.invoke([response])
    messages.extend(tool_messages)

# This is exactly what the StateGraph in react_agent.py encodes:
# agent node → should_continue edge → tools node → back to agent`,
        },
      },
    ],
    interviewTips: [
      '"Walk me through how function calling works in LangGraph." — bind_tools() attaches schemas. LLM returns AIMessage with .tool_calls. ToolNode executes each call and returns ToolMessages. Append both, call LLM again. Loop until tool_calls is empty.',
      '"What happens if the LLM calls a tool that doesn\'t exist?" — ToolNode raises a KeyError. Return an error ToolMessage. The agent usually tries a different approach.',
      '"Can the LLM call multiple tools at once?" — Yes. .tool_calls is a list. ToolNode executes all of them in one pass and returns one ToolMessage per call.',
    ],
    gotchas: [
      'Always append the AIMessage to messages BEFORE appending ToolMessages. The conversation structure requires: HumanMessage → AIMessage → ToolMessages → AIMessage → ...',
      'ToolNode matches tool calls by name to the @tool functions you passed. If the name doesn\'t match, it raises an error. Keep tool names consistent.',
      'The LLM can return text AND tool_calls in the same AIMessage. Both .content and .tool_calls can be non-empty — read both.',
    ],
    relatedIds: ['w2-1', 'w2-2', 'w2-8'],
  },

  {
    id: 'w2-4',
    slug: 'short-term-memory',
    title: 'Short-Term Memory & MemorySaver',
    file: '02_agentic_core/memory/short_term.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: false,
    intro:
      'Short-term memory in LangGraph is the messages list in AgentState. MemorySaver persists it across invocations keyed by thread_id — no manual list management needed. Understanding the underlying rolling window and summarization strategies helps you build custom memory nodes when the defaults aren\'t enough.',
    concepts: [
      {
        title: 'MemorySaver + thread_id',
        body: 'LangGraph\'s MemorySaver checkpointer saves the full AgentState (including all messages) after every node. Calling the same graph with the same thread_id automatically continues the conversation from where it left off. This replaces all manual message list management.',
        snippet: {
          label: 'MemorySaver — persistent conversation by thread_id',
          code: `from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

memory = MemorySaver()
agent = create_react_agent(get_llm(), tools=[], checkpointer=memory)

config = {"configurable": {"thread_id": "session-alex"}}

# Turn 1
agent.invoke({"messages": [HumanMessage("My name is Alex.")]}, config)

# Turn 2 — MemorySaver automatically supplies the prior history
result = agent.invoke({"messages": [HumanMessage("What's my name?")]}, config)
# Agent knows it's Alex — no manual messages list needed`,
        },
      },
      {
        title: 'Inspecting state',
        body: 'Call agent.get_state(config) to see the full message history at any point. This is useful for debugging: you can see exactly what the agent "remembers" for a given thread_id.',
        snippet: {
          label: 'Inspect MemorySaver state',
          code: `state = agent.get_state(config)
print(f"Total messages: {len(state.values['messages'])}")
for msg in state.values['messages']:
    print(f"  {type(msg).__name__}: {msg.content[:80]}")`,
        },
      },
      {
        title: 'Rolling window (conceptual)',
        body: 'When a conversation exceeds the context window, drop the oldest message pairs from the front. Fast and O(1). Cost: early context is permanently lost. In LangGraph, implement this as a custom node that calls trim_messages() on the state before passing to the agent node.',
        snippet: {
          label: 'Rolling window concept — trim before calling agent',
          code: `from langchain_core.messages import trim_messages

def trim_node(state: AgentState) -> dict:
    # Keep only the last 3000 tokens worth of messages
    trimmed = trim_messages(state["messages"], max_tokens=3000,
                            strategy="last", token_counter=len)
    return {"messages": trimmed}

workflow.add_node("trim", trim_node)
workflow.add_edge("trim", "agent")  # trim → agent → tools → agent → ...`,
        },
      },
      {
        title: 'Summarization (conceptual)',
        body: 'When the window fills up, ask the LLM to summarize the oldest half of the conversation into a single summary message, then drop the originals. Preserves meaning at lower token cost. Implement as a conditional node that fires when len(messages) > threshold.',
        snippet: {
          label: 'Summarization node pattern',
          code: `from langchain_core.messages import HumanMessage, SystemMessage

def summarize_node(state: AgentState) -> dict:
    history = "\\n".join(m.content for m in state["messages"][:-2])
    summary = get_fast_llm().invoke([
        HumanMessage(f"Summarize this conversation in 2-3 sentences:\\n{history}")
    ]).content
    # Replace old messages with a summary + keep last 2
    return {"messages": [SystemMessage(f"Summary: {summary}")] + state["messages"][-2:]}`,
        },
      },
    ],
    interviewTips: [
      '"How does memory work in LangGraph?" — MemorySaver persists AgentState keyed by thread_id. Every invocation with the same thread_id resumes from the last checkpoint automatically.',
      '"How do you handle a conversation that exceeds the context window?" — Add a trim_messages() node before the agent (rolling window), or a summarization node that fires when len(messages) > threshold.',
      '"What\'s the production equivalent of MemorySaver?" — SqliteSaver (persistent file) or RedisSaver (multi-worker). Same API, different backend.',
    ],
    gotchas: [
      "Rolling window drops early context silently. If the user said 'my name is Alex' 20 turns ago and you trimmed it, the agent will forget their name.",
      "System messages count toward the context window too. Long system prompts + long conversations overflow faster than expected.",
      "Summarization requires an extra LLM call, adding latency to that turn. Fire it in a background step or make it conditional on len(messages) > N.",
    ],
    relatedIds: ['w2-5', 'w2-6', 'w2-7'],
  },

  {
    id: 'w2-5',
    slug: 'long-term-memory',
    title: 'Long-Term Memory',
    file: '02_agentic_core/memory/long_term.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: true,
    intro:
      'Long-term memory persists across sessions using a vector database. It lets agents remember facts, preferences, and history even after the process restarts. This is the capability that turns a one-time chatbot into an agent that improves over time.',
    concepts: [
      {
        title: 'Long-term vs short-term memory',
        body: 'Short-term: the messages array, exists only for the current session, queried implicitly (it\'s all in context). Long-term: stored in a vector DB on disk or in the cloud, persists indefinitely, queried explicitly by semantic similarity before each turn. You retrieve the most relevant memories and inject them into the system prompt.',
      },
      {
        title: 'Implementation with ChromaDB',
        body: 'Create a persistent ChromaDB collection per agent session (or per user). Call store() to save a memory, query() to retrieve the top-k most relevant ones. Each memory gets a UUID, a content string, and optional metadata (category, timestamp).',
        snippet: {
          label: 'Long-term memory with ChromaDB',
          code: `class LongTermMemory:
    def __init__(self, session_id, persist_path):
        ef = SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path=persist_path)
        self._collection = client.get_or_create_collection(
            f"memory_{session_id}", embedding_function=ef,
            metadata={"hnsw:space": "cosine"}
        )

    def store(self, content: str, metadata=None) -> str:
        memory_id = str(uuid.uuid4())[:8]
        self._collection.add(ids=[memory_id], documents=[content],
                             metadatas=[metadata or {}])
        return memory_id

    def query(self, text: str, top_k=3) -> list[MemoryEntry]:
        results = self._collection.query(query_texts=[text], n_results=top_k)
        return [MemoryEntry(id=id_, content=doc, metadata=meta)
                for id_, doc, meta in zip(results["ids"][0],
                                          results["documents"][0],
                                          results["metadatas"][0])]`,
        },
      },
      {
        title: 'Memory injection pattern',
        body: 'On each agent turn: embed the user query, retrieve top-3 most relevant memories, format them into a context block, prepend to the system prompt. The agent now "knows" about past conversations even though they\'re from different sessions.',
        snippet: {
          label: 'Inject memories into system prompt',
          code: `def build_system_prompt(query: str, memory: LongTermMemory) -> str:
    relevant = memory.query(query, top_k=3)
    if not relevant:
        return BASE_SYSTEM_PROMPT

    memory_context = "\\n".join(
        f"- {entry.content}" for entry in relevant
    )
    return f"{BASE_SYSTEM_PROMPT}\\n\\nRelevant memories:\\n{memory_context}"`,
        },
      },
      {
        title: 'Persistence across restarts',
        body: 'This is the critical feature. ChromaDB PersistentClient writes to disk. Restarting the process and reopening the collection brings back all stored memories. This is how production agents "remember" users across conversations, sessions, and deployments.',
      },
    ],
    interviewTips: [
      '"How would you add memory to a chatbot?" — Short-term: keep the last N message pairs. Long-term: on each turn, query a vector DB for relevant past facts and inject them into the system prompt.',
      '"What is the query strategy for long-term memory?" — Embed the user query, retrieve top-k by cosine similarity. This ensures you get memories relevant to what the user is currently asking, not just the most recent memories.',
    ],
    gotchas: [
      'Long-term memory retrieval adds 50-150ms latency per turn. Run it async while the user message is being validated.',
      'Memory pollution: if you store every message, irrelevant content clutters retrieval. Be selective about what you store — store conclusions, preferences, and significant events, not every word.',
      "You need a memory eviction policy. Vector DBs grow indefinitely. Old memories become irrelevant. Consider TTL-based deletion or periodic pruning.",
    ],
    relatedIds: ['w2-4', 'w2-6', 'w2-7', 'w1-6'],
  },

  {
    id: 'w2-6',
    slug: 'episodic-memory',
    title: 'Episodic Memory',
    file: '02_agentic_core/memory/episodic.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: true,
    intro:
      'Episodic memory stores a structured log of past agent runs — what task was attempted, what steps were taken, what succeeded, what failed. It answers: "What did I do last time I saw this?" Crucial for agents that improve over time.',
    concepts: [
      {
        title: 'What episodic memory stores',
        body: 'Each episode is a record of one agent run: the task, the sequence of steps (tool calls, results), the final outcome, whether it succeeded, how long it took, and any metadata. Unlike long-term semantic memory (which stores facts), episodic memory stores sequences of events — a diary of the agent\'s actions.',
        snippet: {
          label: 'Episode data structure',
          code: `@dataclass
class Episode:
    id: str           # timestamp-based
    task: str         # what was asked
    steps: list[dict] # [{tool, input, result}, ...]
    outcome: str      # what happened
    success: bool
    duration_seconds: float
    metadata: dict    # domain, user, etc.`,
        },
      },
      {
        title: 'JSON-based storage',
        body: 'Episodic memory is commonly stored as a JSON file or a lightweight database. Each episode is appended. The file can be queried by recency, keyword, domain, or success status. For production systems, use a proper database with indexes on task, timestamp, and success status.',
      },
      {
        title: 'Querying episodes',
        body: 'The most common queries: "What did I do last time?" (most recent N episodes), "What happened when I tried X?" (keyword search in tasks/outcomes), "What approaches failed for domain Y?" (failure episodes by metadata). These queries inform how the agent should behave differently this time.',
      },
      {
        title: 'Learning from failures',
        body: 'The real power of episodic memory: you can inject failure records into the agent\'s context. "Last time you tried to search for company X, the tool returned an error. Use the web_search tool with a different query." The agent learns not from model fine-tuning but from its own history.',
        snippet: {
          label: 'Inject past failures into agent context',
          code: `failures = memory.get_failures()
recent_failures = [f for f in failures if f["task"][:50] in current_task[:50]]

if recent_failures:
    failure_ctx = "\\n".join(
        f"- Attempted: {f['task'][:100]} → Failed: {f['outcome'][:100]}"
        for f in recent_failures[-3:]
    )
    system += f"\\n\\nPrevious failures on similar tasks:\\n{failure_ctx}"`,
        },
      },
    ],
    interviewTips: [
      '"What\'s the difference between episodic and semantic memory?" — Episodic stores sequences of events (what the agent did). Semantic stores discrete facts (what the agent knows). Episodic is like a diary; semantic is like a fact database.',
      '"How does episodic memory improve agent reliability?" — By informing the agent what approaches failed before. "That search query returned empty results last time — try rephrasing it."',
    ],
    gotchas: [
      "Episode logs grow indefinitely. Implement a max size (e.g., last 1000 episodes) or archive old ones.",
      "Don't store sensitive data (PII, credentials) in episode logs. They may persist longer than expected.",
      'Keyword search over episodes is too slow at scale. For large episode stores, use a proper search index.',
    ],
    relatedIds: ['w2-4', 'w2-5', 'w2-7'],
  },

  {
    id: 'w2-7',
    slug: 'semantic-memory',
    title: 'Semantic Memory',
    file: '02_agentic_core/memory/semantic.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: true,
    intro:
      'Semantic memory is a structured key-value store for facts the agent should know: user preferences, entity attributes, configuration, cached results. Unlike long-term memory (which uses semantic similarity), you retrieve semantic memory by exact key lookup.',
    concepts: [
      {
        title: 'Key-value namespacing',
        body: 'Organize facts with a colon-separated namespace: user:name, user:preferences, session:current_task, entity:company_name. The namespace makes it easy to bulk-retrieve all facts about a subject: get_namespace("user:") returns everything the agent knows about the user.',
        snippet: {
          label: 'Namespaced key-value store',
          code: `mem = SemanticMemory()
mem.store("user:name", "Alex")
mem.store("user:preferred_language", "Python")
mem.store("session:current_task", "Interview prep", ttl_seconds=3600)

# Bulk retrieve by namespace
user_facts = mem.get_namespace("user:")
# → {"user:name": "Alex", "user:preferred_language": "Python"}`,
        },
      },
      {
        title: 'TTL (Time-to-Live)',
        body: 'Facts can have an expiration time. Useful for: rate limit counters, cached API results, session state, any fact that becomes stale. A TTL of 3600 means the fact is automatically removed after 1 hour. Without TTL, semantic memory grows indefinitely with stale data.',
        snippet: {
          label: 'TTL for expiring facts',
          code: `# Cache a web search result for 5 minutes
mem.store("cache:weather_nyc", "72°F, partly cloudy", ttl_seconds=300)

# Store session state for 1 hour
mem.store("session:last_topic", "vector databases", ttl_seconds=3600)

# When you retrieve, expired entries return the default
result = mem.get("cache:weather_nyc", default="[expired]")`,
        },
      },
      {
        title: 'Injection into system prompt',
        body: 'Semantic memory facts are injected directly into the system prompt as context. Since they\'re exact-key retrievals, there\'s no embedding/retrieval step — they\'re always fast. Load all user facts at the start of each session.',
        snippet: {
          label: 'Inject semantic facts into the system prompt',
          code: `user_facts = mem.get_namespace("user:")
if user_facts:
    facts_str = "\\n".join(f"  {k}: {v}" for k, v in user_facts.items())
    system_prompt = f"User context:\\n{facts_str}\\n\\n{BASE_SYSTEM}"`,
        },
      },
    ],
    interviewTips: [
      '"How is semantic memory different from long-term vector memory?" — Semantic memory uses exact key lookup (fast, no embedding needed). Long-term memory uses semantic similarity search (slower, more flexible). Use semantic memory for structured facts you know the key for; long-term memory for unstructured knowledge you search by meaning.',
    ],
    gotchas: [
      "Key collisions: if two parts of your system write to the same key, one overwrites the other. Use namespacing to prevent this.",
      'TTL granularity: implement TTL checking on every get(), not just on write(). Otherwise, expired entries linger until someone reads them.',
    ],
    relatedIds: ['w2-4', 'w2-5', 'w2-6'],
  },

  {
    id: 'w2-8',
    slug: 'react-agent',
    title: 'The ReAct Agent (StateGraph)',
    file: '02_agentic_core/patterns/react_agent.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: false,
    intro:
      'The ReAct agent is the most important pattern in this repo. In LangGraph, it is a StateGraph with two nodes (agent and tools) connected by a conditional edge. Every agent framework — LangGraph, AutoGen, CrewAI — implements a variation of this graph. Understand the explicit version first, then use create_react_agent() for production.',
    concepts: [
      {
        title: 'The graph IS the loop',
        body: 'The ReAct loop is expressed as a directed graph: agent node calls the LLM, conditional edge checks if tool_calls is non-empty, tools node executes them via ToolNode, edge back to agent. The graph engine runs this until the conditional edge routes to END. No hand-written while loop needed.',
        snippet: {
          label: 'Explicit ReAct StateGraph',
          code: `from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from core.models import AgentState

llm = get_llm().bind_tools(tools)

def call_model(state: AgentState) -> dict:
    """Agent node: call LLM, return new AIMessage."""
    return {"messages": [llm.invoke(state["messages"])]}

def should_continue(state: AgentState) -> str:
    """Router: tool_calls? → tools. Done? → END."""
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)       # Reason: call LLM
workflow.add_node("tools", ToolNode(tools))  # Act: execute tool calls
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")          # Observe: loop back
agent = workflow.compile()`,
        },
      },
      {
        title: 'How it maps to "Reason + Act"',
        body: 'Reason = call_model node: the LLM reads the full message history and produces either an answer (no tool_calls) or a decision to call tools (non-empty tool_calls). Act = ToolNode: executes every tool call in the AIMessage and appends ToolMessages. Observe = the edge back to agent: the LLM sees the tool results on the next invocation. This loop continues until the LLM produces no tool_calls.',
      },
      {
        title: 'AgentState with add_messages',
        body: 'AgentState is a TypedDict with a single field: messages annotated with add_messages. This reducer appends new messages rather than overwriting. Every time call_model returns {"messages": [new_ai_message]}, it is appended to the list — the full conversation history stays intact automatically.',
        snippet: {
          label: 'AgentState — automatic message accumulation',
          code: `from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    # add_messages appends each new message to the list
    # so {"messages": [new_msg]} appends, not overwrites`,
        },
      },
      {
        title: 'System prompt injection',
        body: 'Prepend a SystemMessage in call_model to set the agent\'s persona and instructions. Because the messages list is typed (LangChain message objects), you can filter with isinstance — only inject if no SystemMessage already exists.',
        snippet: {
          label: 'Inject SystemMessage in the agent node',
          code: `from langchain_core.messages import SystemMessage

SYSTEM_PROMPT = """You are a helpful assistant with access to tools.
Use tools to gather information, then give a clear final answer."""

def call_model(state: AgentState) -> dict:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    return {"messages": [llm.invoke(messages)]}`,
        },
      },
      {
        title: 'Max steps — recursion_limit',
        body: 'Pass recursion_limit in the config to cap the number of node visits. Prevents infinite loops. 15 is a reasonable default for most tasks. The graph raises a GraphRecursionError when the limit is hit, which you can catch in the calling code.',
        snippet: {
          label: 'Cap agent steps with recursion_limit',
          code: `result = agent.invoke(
    {"messages": [HumanMessage(content=query)]},
    config={"recursion_limit": 15},  # max 15 node visits
)
# GraphRecursionError is raised if the limit is exceeded`,
        },
      },
      {
        title: 'create_react_agent() shorthand',
        body: 'Once you understand the explicit graph, collapse it to one line: create_react_agent(llm, tools) builds the same two-node graph. Pass checkpointer=MemorySaver() for persistence, and prompt= for the system message. Use this in production.',
        snippet: {
          label: 'Production shorthand',
          code: `from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

agent = create_react_agent(
    get_llm(),
    tools=[calculator, get_datetime, web_search],
    checkpointer=MemorySaver(),     # persist per thread_id
    prompt=SYSTEM_PROMPT,           # injects as SystemMessage
)
result = agent.invoke(
    {"messages": [HumanMessage(content="What is 25 * 47?")]},
    config={"configurable": {"thread_id": "session-1"}, "recursion_limit": 15},
)`,
        },
      },
    ],
    interviewTips: [
      '"Explain the ReAct loop in LangGraph." — StateGraph with agent node (calls LLM) and tools node (ToolNode). Conditional edge: tool_calls non-empty → tools; else → END. Edge from tools back to agent. Runs until END.',
      '"How does the agent know when to stop?" — should_continue checks if the last AIMessage has non-empty .tool_calls. If empty, it returns END. You can also add stopping instructions to the system prompt.',
      '"What do you log in a LangGraph agent?" — Every node invocation emits events. Use agent.stream() with stream_mode="values" to observe each state transition. Log tool names, args, results, and message counts per step.',
    ],
    gotchas: [
      'add_messages appends — it does NOT overwrite. Returning {"messages": [new_msg]} appends new_msg to the list. Returning {"messages": state["messages"] + [new_msg]} would duplicate history.',
      'recursion_limit counts node visits, not LLM calls. An agent + tools round trip = 2 visits. A limit of 15 allows ~7 tool-calling rounds.',
      'MemorySaver is in-memory and dies with the process. For production, use SqliteSaver or RedisSaver with the same interface.',
    ],
    relatedIds: ['w2-1', 'w2-3', 'w2-9', 'w3-1'],
  },

  {
    id: 'w2-9',
    slug: 'plan-and-execute',
    title: 'Plan-and-Execute Agent',
    file: '02_agentic_core/patterns/plan_and_execute.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: false,
    intro:
      'Plan-and-execute separates the "what to do" (planning) from "doing it" (execution). The agent first produces a full structured plan, then executes each step. This makes long tasks more predictable, allows human review of the plan, and simplifies debugging.',
    concepts: [
      {
        title: 'Phase 1: Planning with .with_structured_output()',
        body: 'The planner node uses .with_structured_output(TaskPlan) to ask the LLM for a typed, validated plan object directly. No JSON extraction, no re-prompting loop needed. The result is a Pydantic TaskPlan with a list of TaskStep objects stored in PlanExecuteState["plan"].',
        snippet: {
          label: 'Planner node with .with_structured_output()',
          code: `from pydantic import BaseModel

class TaskStep(BaseModel):
    step_number: int
    description: str
    tool: str  # "calculator" | "web_search" | "get_datetime" | "none"

class TaskPlan(BaseModel):
    task: str
    steps: list[TaskStep]

def planner_node(state: PlanExecuteState) -> dict:
    task = state["messages"][-1].content
    # .with_structured_output() handles schema injection + parsing
    plan: TaskPlan = get_llm().with_structured_output(TaskPlan).invoke([
        SystemMessage(content="Decompose the task into sequential steps."),
        HumanMessage(content=f"Task: {task}"),
    ])
    return {"plan": [f"[{s.tool}] {s.description}" for s in plan.steps]}`,
        },
      },
      {
        title: 'Phase 2: Execution via conditional edges',
        body: 'The executor node pops the first step from state["plan"], executes it (using ToolNode if it needs a tool, or the LLM directly), and appends the result to state["past_steps"]. A conditional edge checks if state["plan"] is empty — if yes, go to the responder; if no, loop back to executor.',
        snippet: {
          label: 'Executor node + conditional edge',
          code: `def executor_node(state: PlanExecuteState) -> dict:
    current_step = state["plan"][0]
    remaining = state["plan"][1:]
    result = run_step(current_step, state["past_steps"])
    return {
        "plan": remaining,
        "past_steps": [(current_step, result)],  # operator.add accumulates
    }

def route_after_execute(state: PlanExecuteState) -> str:
    return "respond" if not state["plan"] else "execute"

workflow.add_conditional_edges("executor", route_after_execute, {
    "execute": "executor",  # more steps remain
    "respond": "responder", # plan exhausted
})`,
        },
      },
      {
        title: 'PlanExecuteState — operator.add on past_steps',
        body: 'PlanExecuteState uses operator.add as the reducer for past_steps. This means each executor invocation appends its (step, result) pair to the list rather than overwriting it. The full execution history is available to the responder for synthesis.',
        snippet: {
          label: 'PlanExecuteState TypedDict',
          code: `import operator
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class PlanExecuteState(TypedDict):
    messages: Annotated[list, add_messages]  # append-only
    plan: list[str]                           # shrinks as steps are executed
    past_steps: Annotated[list, operator.add] # grows as steps complete
    response: str | None                      # set by responder node`,
        },
      },
      {
        title: 'When to use plan-and-execute vs ReAct',
        body: 'Use plan-and-execute for: long-horizon tasks (>5 steps), tasks where you want human review of the plan before execution, tasks with parallelizable steps. Use ReAct for: short tasks, tasks that need dynamic adaptation (new information changes the approach), tasks where the path is unknown in advance.',
      },
    ],
    interviewTips: [
      '"What\'s the main benefit of plan-and-execute over ReAct?" — The plan is visible in PlanExecuteState and can be reviewed before execution. Failures are easier to pinpoint (which step number failed?). Steps can be parallelized.',
      '"What\'s the main drawback?" — Inflexible. If mid-execution conditions change (the search returns no results), the agent can\'t adapt without re-planning. ReAct adapts naturally; plan-and-execute does not.',
    ],
    gotchas: [
      "LLM-generated plans can have logical errors. Add a validation step after the planner node that checks the plan before executing. .with_structured_output() validates schema but not business logic.",
      "operator.add on past_steps accumulates ALL invocations. Each executor call appends — it does not replace. Don't pass past_steps back into the plan unchanged.",
    ],
    relatedIds: ['w2-8', 'w2-10', 'w3-1'],
  },

  {
    id: 'w2-10',
    slug: 'human-in-the-loop',
    title: 'Human-in-the-Loop (interrupt + Command)',
    file: '02_agentic_core/patterns/human_in_loop.py',
    weekLabel: 'Week 2 — Agentic Core',
    noApi: false,
    intro:
      'LangGraph has native human-in-the-loop support via interrupt() and Command(resume=...). interrupt() pauses graph execution at any node, surfaces data to the caller, and waits. The graph resumes when Command(resume=<human_response>) is passed — even hours later, with state preserved in the checkpointer.',
    concepts: [
      {
        title: 'interrupt() — pause at any node',
        body: 'Call interrupt(data) inside any node to pause graph execution. The data dict is surfaced to the caller (e.g., a web API endpoint). The graph state is saved in the checkpointer. Nothing else executes until a resume comes in. This is how you implement approval gates, review steps, and human feedback without blocking threads.',
        snippet: {
          label: 'interrupt() pauses execution in-place',
          code: `from langgraph.types import interrupt

def approval_gate_node(state: AgentState) -> dict:
    proposed_action = state["messages"][-1].content
    # Pause here — surface the action to a human reviewer
    human_response = interrupt({
        "question": "Approve this action?",
        "proposed_action": proposed_action,
    })
    # Execution continues here only after Command(resume=...) is called
    if human_response == "approved":
        return {"messages": [AIMessage(content="Action executed.")]}
    return {"messages": [AIMessage(content="Action rejected.")]}`,
        },
      },
      {
        title: 'Command(resume=...) — resume from pause',
        body: 'After interrupt() fires, the caller receives the data dict. Once the human has responded, pass Command(resume=<value>) to agent.invoke(). The graph picks up exactly where it paused — the human_response variable inside the node receives the value.',
        snippet: {
          label: 'Resuming a paused graph',
          code: `from langgraph.types import Command

config = {"configurable": {"thread_id": "task-1"}}

# First call: runs until interrupt() fires
agent.invoke({"messages": [HumanMessage(content=task)]}, config)

# Later — human reviews and approves
result = agent.invoke(Command(resume="approved"), config)
# OR rejects:
result = agent.invoke(Command(resume="rejected: too risky"), config)`,
        },
      },
      {
        title: 'Feedback loop with interrupt()',
        body: 'For iterative review (draft → feedback → revise → approve), call interrupt() after each draft. The caller shows the draft to the human and calls resume with their feedback. An empty string signals approval. A conditional edge routes back to the writer node if feedback is non-empty.',
        snippet: {
          label: 'Feedback loop via interrupt()',
          code: `def review_node(state: AgentState) -> dict:
    draft = state["messages"][-1].content
    feedback = interrupt({"question": "Any changes needed? (empty = approve)", "draft": draft})

    if not feedback:
        return {"messages": [AIMessage(content="[APPROVED] " + draft)]}
    # Non-empty feedback → inject as HumanMessage → writer revises
    return {"messages": [HumanMessage(content=f"Revise: {feedback}")]}

def route_after_review(state):
    return "writer" if isinstance(state["messages"][-1], HumanMessage) else END`,
        },
      },
      {
        title: 'When to require human oversight',
        body: 'Always require approval for: irreversible actions (delete, send, deploy), actions visible to others, first time an agent takes a new action type, outputs below a confidence threshold. Progressively relax requirements as the agent builds trust — similar to how a new employee gets more autonomy over time.',
      },
    ],
    interviewTips: [
      '"How does LangGraph implement human-in-the-loop?" — interrupt() pauses the graph and saves state in the checkpointer. The human responds via Command(resume=...). The graph resumes exactly where it paused.',
      '"What\'s the advantage over a blocking input() call?" — State is persisted. The human can respond hours later. Multiple agents can be paused simultaneously. Works across HTTP request boundaries.',
    ],
    gotchas: [
      'interrupt() requires a checkpointer on the compiled graph (MemorySaver or RedisSaver). Without one, there is no state to resume from.',
      'Too many approval gates kill UX. Every interrupt breaks flow. Only gate actions that are truly risky or irreversible.',
      'Async approval (pause the graph, notify via webhook, resume when approved) is more scalable than synchronous blocking.',
    ],
    relatedIds: ['w2-8', 'w2-9', 'w3-5'],
  },

  // ── Week 3 — System Design + Resiliency ────────────────────────────────────

  {
    id: 'w3-1',
    slug: 'orchestrator-pattern',
    title: 'The Supervisor Pattern',
    file: '03_system_design/orchestrator.py',
    weekLabel: 'Week 3 — System Design',
    noApi: false,
    intro:
      'The Supervisor pattern uses a central coordinator node to route tasks to specialist sub-agent nodes using Command(goto=...). Each specialist returns Command(goto="supervisor") when done. The graph encodes the routing logic explicitly — no hand-written if/elif chains needed.',
    concepts: [
      {
        title: 'Command(goto=...) — the routing primitive',
        body: 'Supervisor nodes return Command objects rather than plain dicts. Command(goto="researcher") routes execution to the researcher node next. Command(goto=END) finishes the graph. Specialist nodes return Command(goto="supervisor") to report back. The routing is declared in the return value, not in edge conditions.',
        snippet: {
          label: 'Supervisor node with Command(goto=...)',
          code: `from langgraph.types import Command
from langgraph.graph import END

MEMBERS = ["researcher", "calculator", "summarizer"]

def supervisor_node(state: SupervisorState) -> Command:
    # LLM decides who should act next
    decision = get_fast_llm().invoke([
        SystemMessage(f"Route to one of: {', '.join(MEMBERS)}, or FINISH"),
        *state["messages"],
    ]).content.strip()

    if decision == "FINISH":
        return Command(goto=END)
    return Command(goto=decision, update={"next_agent": decision})`,
        },
      },
      {
        title: 'Specialist nodes return to supervisor',
        body: 'Each specialist does one thing and returns Command(goto="supervisor") so the supervisor can decide what comes next. The update dict in Command lets the specialist append its result to the shared messages state.',
        snippet: {
          label: 'Specialist node returns to supervisor',
          code: `from langchain_core.messages import AIMessage

def researcher_node(state: SupervisorState) -> Command:
    task = state["messages"][-1].content
    result = get_fast_llm().invoke([
        SystemMessage("You are a research agent. Be concise."),
        HumanMessage(f"Research: {task}"),
    ]).content
    return Command(
        goto="supervisor",
        update={"messages": [AIMessage(content=result, name="researcher")]},
    )`,
        },
      },
      {
        title: 'Graph structure — hub and spoke',
        body: 'All specialist nodes have an implicit edge back to supervisor (via Command(goto="supervisor")). The supervisor has conditional routes to each specialist and to END. This hub-and-spoke pattern means you add new specialists by writing one new node function — no edge table to update.',
        snippet: {
          label: 'Building the supervisor graph',
          code: `workflow = StateGraph(SupervisorState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("calculator", calculator_node)
workflow.add_node("summarizer", summarizer_node)

workflow.set_entry_point("supervisor")
# No add_edge needed — Command(goto=...) handles all routing
agent = workflow.compile()`,
        },
      },
      {
        title: 'Supervisor vs swarm',
        body: 'Supervisor: central controller routes tasks. Easy to reason about and debug. Single coordinator node. Swarm: agents self-organize peer-to-peer, no central control. More parallel and resilient. Harder to debug and predict. For most production systems, the supervisor pattern is preferred because predictability > raw performance.',
      },
    ],
    interviewTips: [
      '"Design a multi-agent system for research." — Supervisor routes to Researcher (web search), Calculator (compute), Summarizer (synthesis). Each returns Command(goto="supervisor"). Supervisor routes to END when done.',
      '"What\'s the bottleneck in the supervisor pattern?" — The supervisor itself. If it\'s overloaded, the whole system stalls. Mitigate with stateless workers and horizontal scaling (RedisSaver for state).',
    ],
    gotchas: [
      "Don't put business logic in the supervisor. It routes and coordinates — logic belongs in specialist nodes.",
      "Command(goto=...) routes to exactly one node. If you need to fan out to multiple specialists in parallel, use subgraphs or parallel branches instead.",
    ],
    relatedIds: ['w2-8', 'w2-9', 'w3-2', 'w3-4'],
  },

  {
    id: 'w3-2',
    slug: 'llm-gateway',
    title: 'LLM Gateway Pattern',
    file: '03_system_design/llm_gateway.py',
    weekLabel: 'Week 3 — System Design',
    noApi: false,
    intro:
      'The LLM Gateway wraps get_llm() with .with_retry() and .with_fallbacks() to produce a resilient Runnable used by all agents. Agents never reference model names or error types directly — they call the gateway Runnable and get consistent behavior.',
    concepts: [
      {
        title: 'Why a gateway?',
        body: 'Without a gateway, model names and API patterns are scattered across all your agent code. When Anthropic deprecates a model, you update one file. With a gateway, agents are portable between providers. The gateway also centralizes retry logic, rate limiting, and usage metrics.',
      },
      {
        title: 'Model fallback chain with .with_fallbacks()',
        body: 'Primary model fails (rate limit, outage) → automatically tries fallback. This is the difference between a 5-second outage and a 30-minute outage. .with_fallbacks() is a composable Runnable method — apply it to any LLM, chain, or retriever. No custom class needed.',
        snippet: {
          label: '.with_fallbacks() — composable fallback chain',
          code: `# Pattern 1: simple fallback
llm_with_fallback = get_llm().with_fallbacks(
    [get_fast_llm()],
    exceptions_to_handle=(Exception,),  # trigger on any error
)

# Pattern 2: retry primary first, then fall back
resilient_llm = (
    get_llm()
    .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
    .with_fallbacks([get_fast_llm().with_retry(stop_after_attempt=2)])
)

# Same interface regardless of which model actually responds
result = resilient_llm.invoke([HumanMessage(content=query)])`,
        },
      },
      {
        title: 'Usage tracking',
        body: 'The gateway tracks: total calls, total input/output tokens, fallback count, average latency, error count. This data is used for cost attribution (which feature spends the most tokens?), performance monitoring (is latency increasing?), and capacity planning (are we approaching rate limits?).',
      },
    ],
    interviewTips: [
      '"How do you handle model deprecations?" — All agents call get_llm() or the resilient_llm gateway Runnable. Swap the model in one place (core/client.py MODEL constant) — no agent code changes.',
      '"How do you A/B test models?" — Wrap both models in the gateway with a routing function. Route X% of calls to model A, (100-X)% to model B. Track eval metrics per model. Roll out the winner.',
    ],
    gotchas: [
      '.with_fallbacks() is composable but not a circuit breaker. It retries on every call. For true circuit-breaker behavior, track consecutive failures externally.',
      "Don't add business logic to the gateway Runnable. It's infrastructure. Prompt engineering belongs in the agent nodes.",
    ],
    relatedIds: ['w3-1', 'w3-3', 'w3-4', 'w4-6'],
  },

  {
    id: 'w3-3',
    slug: 'tool-registry-advanced',
    title: 'Advanced Tool Registry',
    file: '03_system_design/tool_registry.py',
    weekLabel: 'Week 3 — System Design',
    noApi: true,
    intro:
      'The system-design level tool registry adds versioning, access control, usage metrics, and discoverability to the basic pattern. This is what tool registries look like in production.',
    concepts: [
      {
        title: 'Tool versioning',
        body: 'Register both CalculatorV1 and CalculatorV2. Agents can request "latest" (default) or a specific version. This enables gradual rollouts: deploy V2 and route 10% of traffic to it, verify it\'s better, then make it the default.',
      },
      {
        title: 'Access control',
        body: 'Tools can require a permission level. A public caller cannot invoke admin_report. A user caller cannot invoke payment_processing. The registry enforces this before executing the tool, preventing privilege escalation.',
      },
      {
        title: 'Dynamic discovery',
        body: 'The discover() method lets agents find tools by category or tag at runtime. A research agent might call discover(category="search") to find all available search tools, rather than having them hardcoded.',
      },
    ],
    interviewTips: [
      '"How do you add a tool without changing agent code?" — Add a @tool-decorated function to the tools list, rebuild ToolNode. Agents pick it up automatically via bind_tools() on the next initialization.',
      '"How do you version a tool?" — Register the new version with a different version string. Default to "latest" which auto-selects the highest version. Old callers can pin to a version string.',
    ],
    gotchas: [
      "Tool schemas are part of the prompt. Every tool you register adds tokens to every LLM call. Only register tools the agent actually needs for the current task.",
    ],
    relatedIds: ['w2-1', 'w3-1', 'w3-2'],
  },

  {
    id: 'w3-4',
    slug: 'observability',
    title: 'Observability & Tracing',
    file: '03_system_design/observability.py',
    weekLabel: 'Week 3 — System Design',
    noApi: true,
    intro:
      'You cannot debug what you cannot see. Observability in agentic systems means structured traces — a span for every agent step with timing, inputs, outputs, and token counts. This is how you answer "why did this task fail?" in production.',
    concepts: [
      {
        title: 'Spans and traces',
        body: 'A trace is the complete record of one agent run. A span is one step within a trace (one LLM call, one tool call, one memory query). Spans are nested: the trace contains agent.run, which contains llm.plan, tool.calculator, llm.synthesize, etc. Each span has a start time, end time, status (ok/error), and attributes.',
        snippet: {
          label: 'Span as a context manager',
          code: `class Tracer:
    @contextmanager
    def span(self, name: str, **attributes):
        s = Span(name=name, attributes=attributes)
        try:
            yield s
            s.finish("ok")
        except Exception as e:
            s.finish("error")
            s.attributes["error"] = str(e)
            raise
        finally:
            log.info("span.end", name=name, duration_ms=s.duration_ms, status=s.status)

# Usage:
with tracer.span("tool.calculator", expression="25*47") as s:
    result = calculator.run("25*47")
    s.attributes["result"] = result`,
        },
      },
      {
        title: 'What to capture per span',
        body: 'Minimum: name, start time, duration, status. For LLM spans: model, input tokens, output tokens. For tool spans: tool name, input arguments, output (truncated). For memory spans: operation, key/query, results count. For the root span: full task description, user ID, total tokens.',
      },
      {
        title: 'Debugging with traces',
        body: 'When an agent task fails, open the trace and look for: which span has status=error, which tool is slowest (often the network call), whether the agent is calling the same tool repeatedly (stuck loop), whether token counts are spiking unexpectedly.',
      },
      {
        title: 'Production tooling',
        body: 'Langfuse (open-source, easy to deploy) is the most popular LLM-specific observability tool. Arize Phoenix is good for RAG evaluation. For general distributed tracing, use OpenTelemetry with Jaeger or Datadog. All accept spans in the same format.',
      },
    ],
    interviewTips: [
      '"How do you debug an agent that\'s producing wrong answers?" — Check the trace. Which step produced unexpected output? Was retrieval returning the wrong chunks? Did a tool call fail silently? Is the same tool being called 5 times?',
      '"What do you monitor in production?" — P50/P95 latency per task type, token cost per task, error rate by tool, LLM call count per task (proxy for loop efficiency).',
    ],
    gotchas: [
      "Sampling: don't capture 100% of traces in high-traffic production. Sample 1-5% for metrics, capture 100% on errors.",
      'Truncate tool outputs in spans. A web search returning 10KB of HTML in every span will bloat your trace storage.',
    ],
    relatedIds: ['w3-1', 'w4-1', 'w4-2'],
  },

  {
    id: 'w3-5',
    slug: 'guardrails',
    title: 'Guardrails & Validation',
    file: '04_resiliency/guardrails.py',
    weekLabel: 'Week 3 — Resiliency',
    noApi: true,
    intro:
      'Guardrails validate inputs before they reach the LLM and outputs before they reach the user. They\'re the first and last line of defense — catching injection attacks, malformed data, PII leakage, and unsafe content at the system boundary.',
    concepts: [
      {
        title: 'Input guardrails',
        body: 'Validate user input before processing: check length (reject oversized queries), detect prompt injection patterns (regex on known attack strings), scan for PII (SSNs, credit cards, email addresses). Use Pydantic models as the schema — they provide validation + clear error messages for free.',
        snippet: {
          label: 'Input validation with Pydantic',
          code: `class AgentInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{3,50}$")

    @field_validator("query")
    @classmethod
    def no_injection(cls, v):
        patterns = [r"ignore (all |previous )?instructions", r"you are now"]
        for pattern in patterns:
            if re.search(pattern, v.lower()):
                raise ValueError("Potential injection detected")
        return v.strip()`,
        },
      },
      {
        title: 'Output guardrails',
        body: 'Validate the LLM\'s response before returning it to the user: check response schema (is it valid JSON if expected?), check for harmful content, flag low confidence scores for human review. Low-confidence outputs should be held for review rather than silently returned.',
      },
      {
        title: 'Where to validate',
        body: 'Always validate at system boundaries: incoming requests from external users, outgoing responses to external systems, tool call inputs and outputs. Do NOT validate data you control internally — trust your own code and add assertions only where bugs would be silent.',
      },
    ],
    interviewTips: [
      '"What are guardrails?" — Validation layers at system boundaries. Input guardrails: sanitize and validate user input. Output guardrails: validate LLM response schema and content before acting on it.',
      '"How do you detect prompt injection?" — Basic: regex on known attack patterns. Advanced: a classifier model trained to detect injection attempts. Always combine with least-privilege (the agent can only call the tools it needs for this task).',
    ],
    gotchas: [
      "Guardrails add latency. Keep them fast — regex is fine, a classifier model adds 50-200ms.",
      "Don't try to be exhaustive with regex-based injection detection. There are infinite injection variants. Use it as a first filter, not a complete defense.",
    ],
    relatedIds: ['w3-8', 'w4-1', 'w2-10'],
  },

  {
    id: 'w3-6',
    slug: 'retry-strategies',
    title: 'Retry Strategies (.with_retry)',
    file: '04_resiliency/retry_strategies.py',
    weekLabel: 'Week 3 — Resiliency',
    noApi: false,
    intro:
      'External APIs fail. Rate limits hit. Networks hiccup. Retry logic is non-negotiable in production agents. In LangGraph, .with_retry() and .with_fallbacks() are composable Runnable methods that apply to any LLM, chain, retriever, or ToolNode — no decorator needed.',
    concepts: [
      {
        title: '.with_retry() — exponential backoff with jitter',
        body: 'Call llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True) to wrap any Runnable with automatic retry logic. Jitter adds randomness to prevent thundering herd — all clients won\'t retry at the same millisecond. Returns a new Runnable with the same interface.',
        snippet: {
          label: '.with_retry() — composable retry on any Runnable',
          code: `from core.client import get_llm, get_fast_llm

# Wrap the LLM with retry — same .invoke() interface
llm_with_retry = get_llm().with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True,  # jitter prevents thundering herd
)

result = llm_with_retry.invoke([HumanMessage(content=query)])
# If a transient error occurs, retries automatically up to 3×`,
        },
      },
      {
        title: 'Jitter — prevents thundering herd',
        body: 'Without jitter, all clients that fail at the same moment retry at the same moment — overloading the recovering service again. With jitter: wait = exponential_wait × random(0.5, 1.5). wait_exponential_jitter=True in .with_retry() enables this automatically.',
      },
      {
        title: '.with_fallbacks() — escalate to a different model',
        body: 'If retries exhaust on the primary model, .with_fallbacks() automatically tries the next model in the list. This is different from retrying — it\'s switching to an alternative. The fallback model gives worse but functional results while the primary recovers.',
        snippet: {
          label: '.with_fallbacks() — automatic model escalation',
          code: `# Primary retries 3×, then falls back to fast model (also retried 2×)
resilient_llm = (
    get_llm()
    .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
    .with_fallbacks(
        [get_fast_llm().with_retry(stop_after_attempt=2)],
        exceptions_to_handle=(Exception,),
    )
)
# Same interface — callers don't know which model responded`,
        },
      },
      {
        title: 'When NOT to retry',
        body: '400 Bad Request: your input is malformed — retrying won\'t help, fix the input. 401 Unauthorized: wrong API key. 404 Not Found: resource doesn\'t exist. DO retry: 429 Rate Limit, 500/503 Server Error, network timeouts. .with_retry() retries on all exceptions by default; pass retry_if_exception_type to be selective.',
      },
    ],
    interviewTips: [
      '"How do you handle LLM rate limits in LangGraph?" — .with_retry(stop_after_attempt=3, wait_exponential_jitter=True) on the LLM. .with_fallbacks([backup_llm]) as the final escalation.',
      '"When should you not retry?" — 4xx errors (bad request, auth error, not found) are not transient. Pass retry_if_exception_type to exclude them. Only retry 5xx and rate limits.',
    ],
    gotchas: [
      ".with_retry() retries ALL exceptions by default — including 400 Bad Request. Pass retry_if_exception_type=(RateLimitError, ConnectionError) to be precise.",
      'Set a total retry budget (stop_after_attempt=3-4). Never retry indefinitely — an outage could cause your agent to hang for hours.',
    ],
    relatedIds: ['w3-7', 'w3-2', 'w4-3'],
  },

  {
    id: 'w3-7',
    slug: 'loop-control',
    title: 'Loop Control',
    file: '04_resiliency/loop_control.py',
    weekLabel: 'Week 3 — Resiliency',
    noApi: true,
    intro:
      'Infinite loops are the most dangerous failure mode in agentic systems — they run silently, consume your entire API budget, and never return. Max iterations, timeouts, and stuck-loop detection are your three defenses.',
    concepts: [
      {
        title: 'Max iterations',
        body: 'Every agent loop MUST have a hard limit on the number of steps. Without it, a bug in tool execution or an ambiguous task runs forever. Set MAX_STEPS = 10-15 for most agents. When the limit is reached, raise MaxIterationsError and return the best partial result.',
        snippet: {
          label: 'MaxIterationsError and check',
          code: `class MaxIterationsError(Exception):
    def __init__(self, max_iter, last_action=""):
        super().__init__(f"Exceeded {max_iter} iterations. Last action: {last_action!r}")

# In the agent loop:
for step in range(MAX_STEPS):
    ...
raise MaxIterationsError(MAX_STEPS, last_action=last_tool_called)`,
        },
      },
      {
        title: 'Stuck-loop detection',
        body: 'The agent calls web_search 5 times in a row with the same query, getting the same empty result, and never makes progress. Max iterations catches this eventually, but stuck-loop detection catches it immediately. Track the last N actions; if they\'re all the same, raise StuckLoopError.',
        snippet: {
          label: 'Stuck-loop detection',
          code: `class LoopController:
    def tick(self, action: str):
        self._iterations += 1
        if self._iterations > self.max_iterations:
            raise MaxIterationsError(self.max_iterations, action)
        self._history.append(action)
        # Same action N times in a row = stuck
        if len(self._history) >= self.stuck_threshold:
            recent = self._history[-self.stuck_threshold:]
            if len(set(recent)) == 1:
                raise StuckLoopError(action, self.stuck_threshold)`,
        },
      },
      {
        title: 'Circuit breaker',
        body: 'After N consecutive failures on a specific tool or service, stop calling it and return an immediate error. This prevents the agent from wasting 30s on a tool that\'s clearly down. The circuit reopens after a timeout (e.g., 30s), allowing one test call.',
      },
      {
        title: 'Wall-clock timeout',
        body: 'Even with max iterations, an agent that takes 2 minutes per tool call could run for 30 minutes before hitting the step limit. Set an absolute wall-clock timeout (60s for interactive, 10 minutes for batch). On Unix systems, use signal.alarm; on Windows, use threading.Timer.',
      },
    ],
    interviewTips: [
      '"How do you prevent infinite loops in agents?" — Three layers: max_steps (hard limit on iterations), stuck-loop detection (same action repeated), and wall-clock timeout. Circuit breakers for failing dependencies.',
      '"What do you do when max_steps is reached?" — Return the best partial result with a note that the task wasn\'t completed. Log the failure, record it in episodic memory, and surface it in observability dashboards.',
    ],
    gotchas: [
      "Max iterations without stuck-loop detection means you burn all your iterations before detecting you're stuck. Combine both.",
      "Don't set MAX_STEPS too low. A task that legitimately needs 8 steps fails if you cap at 5.",
    ],
    relatedIds: ['w3-6', 'w3-5', 'w2-8'],
  },

  {
    id: 'w3-8',
    slug: 'structured-outputs',
    title: 'Structured Outputs (.with_structured_output)',
    file: '04_resiliency/structured_outputs.py',
    weekLabel: 'Week 3 — Resiliency',
    noApi: false,
    intro:
      'LLMs naturally produce prose. Agents need machine-readable Python objects. .with_structured_output(MyModel) handles schema injection, JSON parsing, and Pydantic validation in one method call — returning a typed instance directly. No extract_json(), no re-prompting loop needed.',
    concepts: [
      {
        title: 'The problem with free-form output',
        body: 'Without structure, the same question returns "The total is $4.20", "$4.20", "Total: 4.2 dollars", etc. Parsing this with regex is fragile and breaks whenever the model changes phrasing. Pydantic schemas define exactly what fields you expect and validate them automatically.',
      },
      {
        title: '.with_structured_output() — one line, typed result',
        body: 'Call llm.with_structured_output(MyModel) to get a new Runnable. Invoking it returns a validated MyModel instance — not a string. LangChain injects the JSON schema, parses the response, and validates it. If validation fails internally, it retries automatically.',
        snippet: {
          label: '.with_structured_output() — typed result in one call',
          code: `from pydantic import BaseModel, Field

class TaskPlan(BaseModel):
    title: str
    steps: list[str] = Field(..., min_length=1, max_length=10)
    estimated_minutes: int = Field(..., ge=1, le=480)
    confidence: float = Field(..., ge=0.0, le=1.0)

# One line — schema injection + parsing + validation all handled internally
structured_llm = get_fast_llm().with_structured_output(TaskPlan)
plan: TaskPlan = structured_llm.invoke("Create a plan to build a RAG system.")

# plan is already a validated TaskPlan instance
print(plan.title)          # str
print(plan.steps)          # list[str]
print(plan.confidence)     # float, validated 0.0–1.0`,
        },
      },
      {
        title: 'Using it inside a StateGraph node',
        body: '.with_structured_output() returns a Runnable, so it composes with the rest of LangGraph naturally. Call it inside any node function to get typed, validated output from the LLM as part of your graph.',
        snippet: {
          label: '.with_structured_output() inside a graph node',
          code: `class ValidationReport(BaseModel):
    overall_score: float
    approved: bool
    summary: str

def validator_node(state: PlanExecuteState) -> dict:
    task = state["messages"][0].content
    results = state["past_steps"]

    report: ValidationReport = (
        get_fast_llm()
        .with_structured_output(ValidationReport)
        .invoke([
            SystemMessage("You are a quality validator."),
            HumanMessage(f"Task: {task}\\n\\nResults: {results}\\n\\nValidate."),
        ])
    )
    return {"past_steps": [("__validation__", str(report.model_dump()))]}`,
        },
      },
      {
        title: 'When .with_structured_output() is not enough',
        body: 'For very complex nested schemas with cross-field dependencies, the LLM sometimes fails validation repeatedly. In those cases, use a manual re-prompting loop: inject the Pydantic validation error back into the conversation and ask the LLM to fix it. This is the pattern shown in the reference file.',
      },
    ],
    interviewTips: [
      '"How do you make LLM output reliable in LangGraph?" — llm.with_structured_output(MyModel) handles schema injection, parsing, and Pydantic validation in one call. Returns a typed Python object.',
      '"When would you still use a manual re-prompting loop?" — When .with_structured_output() fails repeatedly on a complex schema, or when you need to log each failed attempt for debugging.',
    ],
    gotchas: [
      ".with_structured_output() retries internally, but you don't control how many times. For mission-critical extraction, wrap it in .with_retry() or add a manual fallback.",
      "Large Pydantic schemas with many interdependent fields can still fail. Split complex extractions into two smaller schemas with separate LLM calls.",
    ],
    relatedIds: ['w3-5', 'w4-2', 'w2-9'],
  },

  // ── Week 4 — Projects ────────────────────────────────────────────────────────

  {
    id: 'w4-1',
    slug: 'prompt-unit-tests',
    title: 'Prompt Unit Testing',
    file: '04_resiliency/evaluation/prompt_unit_tests.py',
    weekLabel: 'Week 4 — Projects',
    noApi: false,
    intro:
      'You can\'t unit test the LLM itself, but you can write assertions about its behavior on known inputs. These tests catch regressions when you change the system prompt, switch models, or update your tools.',
    concepts: [
      {
        title: 'What to assert',
        body: 'Keywords present in the response, response length within bounds, structured outputs parse correctly, agent selects the right tool for a given query type, uncertainty phrases appear for unknown entities. Think of these as contract tests: "given this input, the output must have these properties."',
        snippet: {
          label: 'pytest assertions on LLM behavior',
          code: `@pytest.fixture(scope="module")
def client():
    return get_client()

def test_rag_definition_contains_retrieval(client):
    response = ask(client, "In one sentence, what is RAG?")
    assert any(kw in response.lower()
               for kw in ["retrieval", "retrieve", "retrieved"])

def test_admits_uncertainty_for_unknown_entity(client):
    response = ask(client, "What are the products of Zylantrix Corp? "
                           "Say so if you don't know.")
    uncertainty_phrases = ["don't know", "not aware", "no information",
                            "cannot find", "fictional", "doesn't exist"]
    assert any(p in response.lower() for p in uncertainty_phrases)`,
        },
      },
      {
        title: 'LLM-as-judge tests',
        body: 'For free-form outputs, use a second LLM call to grade whether the answer addresses the question: "Rate this answer yes or no: does it directly address the question?" This is slower and costs extra tokens but is more nuanced than keyword matching.',
      },
      {
        title: 'Running in CI',
        body: 'Add these tests to CI (GitHub Actions, etc.) so that prompt changes are automatically tested. Gate deployment on test passage. Track test scores over time — a score drop of >10% should block the release.',
      },
    ],
    interviewTips: [
      '"How do you test a prompt change before deploying?" — Run your golden dataset tests against the new prompt. Compare pass rates. If they improve or hold steady, the change is safe.',
    ],
    gotchas: [
      'LLM tests are non-deterministic at temperature > 0. Run tests at temperature=0 for consistency, or run them 3× and take the majority vote.',
      'These tests call the real API and cost tokens. Keep them focused on high-value assertions. Run the full suite weekly; run a fast subset in CI.',
    ],
    relatedIds: ['w1-8', 'w4-2', 'w3-5'],
  },

  {
    id: 'w4-2',
    slug: 'golden-dataset',
    title: 'Golden Dataset Evaluation',
    file: '04_resiliency/evaluation/golden_dataset.py',
    weekLabel: 'Week 4 — Projects',
    noApi: false,
    intro:
      'A golden dataset is a curated set of question/answer pairs with known correct outputs. Run your agent against it periodically to measure quality over time and catch regressions before they reach users.',
    concepts: [
      {
        title: 'Building the golden dataset',
        body: 'Start with 20-50 representative questions across all query types your agent handles. For each, write: the question, the expected keywords in a good answer, and minimum keyword match count. These should cover edge cases, known hard queries, and common use cases. Review and update it quarterly.',
      },
      {
        title: 'Scoring strategies',
        body: 'Keyword match: fast, cheap, brittle. LLM-as-judge: flexible, handles paraphrase, costs extra tokens, has its own biases. Exact match: best for structured outputs (JSON, numbers). In practice, use keyword match for quick regression checks and LLM-as-judge for quarterly quality reviews.',
      },
      {
        title: 'Tracking over time',
        body: 'Save eval results with timestamps. Track: overall pass rate, pass rate by category, average LLM-as-judge score. When you update your prompt or model, run the eval before and after. If scores drop, investigate before deploying.',
      },
    ],
    interviewTips: [
      '"How do you know if your agent got better or worse after a change?" — Run the same golden dataset before and after. Compare pass rates by category. Use statistical significance testing if the change is small.',
    ],
    gotchas: [
      'Test set contamination: if you tune your prompt to pass the test set, you\'re overfitting. Keep a held-out test set separate from your development eval set.',
    ],
    relatedIds: ['w4-1', 'w1-8', 'w3-4'],
  },

  {
    id: 'w4-3',
    slug: 'project1-tool-agent',
    title: 'Project 1: Tool-Using Agent',
    file: '05_projects/project1_tool_agent/agent.py',
    weekLabel: 'Week 4 — Projects',
    noApi: false,
    intro:
      'Project 1 is the capstone ReAct agent. It combines everything from Week 2: 4 real tools, long-term memory (notes), retry logic, loop control, and structured logging. This is your "I built something" demo for interviews.',
    concepts: [
      {
        title: 'What this project demonstrates',
        body: 'A complete tool-using agent with: calculator (safe eval), datetime, mock web search, and a note-taking tool that acts as working memory within a run. Tenacity backoff on rate limit errors. MAX_STEPS=15 hard limit. structlog event on every step. Prompt caching on the system prompt.',
      },
      {
        title: 'The note-taking tool as memory',
        body: 'The note-taking tool gives the agent memory within a single run. "Search for information about X, save key facts as notes, then summarize what you found." The agent can save intermediate results and retrieve them later without relying on context window management.',
      },
      {
        title: 'Key patterns to study',
        body: 'The _call_claude() function with @retry decorator. The main run_agent() loop. How tool results are returned and appended. How structlog.info is called after each step. How the final answer is extracted from response.content.',
      },
    ],
    interviewTips: [
      '"Tell me about a project you built with LLMs." — "I built a tool-using agent that combines calculator, web search, and note-taking with retry logic and structured tracing. Each step logs the tool called, inputs, outputs, and token counts to structlog."',
    ],
    gotchas: [
      "The note-taking tool's state (_notes dict) is module-level and resets on each run. For persistence across runs, write it to a file or database.",
    ],
    relatedIds: ['w2-8', 'w2-1', 'w3-6', 'w3-4'],
  },

  {
    id: 'w4-4',
    slug: 'project2-rag-ingest',
    title: 'Project 2: RAG Ingestion',
    file: '05_projects/project2_rag/ingest.py',
    weekLabel: 'Week 4 — Projects',
    noApi: true,
    intro:
      'The ingestion pipeline is the offline half of RAG. Run it once to build your index. It loads documents, chunks them with sliding window, embeds with sentence-transformers, and stores in ChromaDB. Run this before running rag_chain.py or api.py.',
    concepts: [
      {
        title: 'Pipeline stages',
        body: 'load_documents() → sliding_window_chunks() → collection.add(). ChromaDB handles the embedding call internally (via the configured SentenceTransformerEmbeddingFunction). The collection persists to disk at CHROMA_PATH.',
      },
      {
        title: 'Chunking config',
        body: 'CHUNK_SIZE_WORDS=80, CHUNK_OVERLAP_WORDS=15 (19% overlap). These are reasonable defaults for technical documentation. Adjust based on your document type and query patterns.',
      },
      {
        title: 'Metadata per chunk',
        body: 'Each chunk stores: source filename, chunk_index, total_chunks, word_count. This lets you display citations (which document did this come from?) and detect when a chunk is the only piece of a document.',
      },
    ],
    interviewTips: [
      '"Walk me through how you would build a RAG system." — Start with ingest.py: load docs, chunk with sliding window (80 words, 15 overlap), embed with sentence-transformers, store in ChromaDB. Query with hybrid search (BM25 + vector). Augment prompt. Generate.',
    ],
    gotchas: [
      'Re-running ingest with reset=False when chunks already exist will add duplicates. Always use reset=True or check collection.count() first.',
    ],
    relatedIds: ['w4-5', 'w4-6', 'w1-5', 'w1-6'],
  },

  {
    id: 'w4-5',
    slug: 'project2-rag-query',
    title: 'Project 2: RAG Query',
    file: '05_projects/project2_rag/rag_chain.py',
    weekLabel: 'Week 4 — Projects',
    noApi: false,
    intro:
      'The query pipeline is the online half of RAG. For each user question: run hybrid retrieval (BM25 + vector), build the augmented prompt, call Claude, return the answer with source citations.',
    concepts: [
      {
        title: 'Hybrid retrieval',
        body: 'retrieval.py runs BM25 and vector search in parallel, then merges results with RRF. The merged top-k chunks are passed to rag_chain.py for augmentation.',
      },
      {
        title: 'Prompt augmentation',
        body: 'Format each retrieved chunk as "[Source N: filename]\\n{chunk_text}" and inject all chunks into the prompt before the question. The system prompt instructs Claude to answer ONLY from the provided context and cite sources.',
      },
      {
        title: 'Source citations',
        body: 'Every response includes the list of source documents used. This is the primary trust feature of RAG — users can verify the answer against the original documents.',
      },
    ],
    interviewTips: [
      '"How do you handle the case where no relevant documents are found?" — Set a minimum similarity threshold. If all retrieved chunks score below 0.5, return "I couldn\'t find relevant information in the knowledge base" rather than hallucinating an answer.',
    ],
    gotchas: [
      'Token count: 4 chunks × 80 words × 1.3 tokens/word ≈ 416 tokens for context. With a system prompt and question, you\'re at 600-800 tokens before the answer. Budget for this.',
    ],
    relatedIds: ['w4-4', 'w4-6', 'w1-7'],
  },

  {
    id: 'w4-6',
    slug: 'project2-rag-api',
    title: 'Project 2: RAG API',
    file: '05_projects/project2_rag/api.py',
    weekLabel: 'Week 4 — Projects',
    noApi: false,
    intro:
      'api.py wraps the RAG pipeline in a FastAPI endpoint. POST /ask → {answer, sources, tokens_used}. This is the production deployment pattern: the RAG logic is unchanged, just exposed via REST.',
    concepts: [
      {
        title: 'FastAPI setup',
        body: 'FastAPI auto-generates OpenAPI docs at /docs. Request and response are Pydantic models — validation is automatic. Error handling returns proper HTTP status codes (503 when the index isn\'t built, 500 for unexpected errors).',
        snippet: {
          label: 'FastAPI endpoint structure',
          code: `@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        result = rag_query(request.question, top_k=request.top_k, verbose=False)
        return AskResponse(**result)
    except FileNotFoundError:
        raise HTTPException(503, "Index not found. Run ingest.py first.")
    except Exception as e:
        raise HTTPException(500, str(e))`,
        },
      },
      {
        title: 'Running the API',
        body: 'uvicorn 05_projects.project2_rag.api:app --reload. Visit http://localhost:8000/docs for the interactive API explorer. The --reload flag auto-restarts on code changes (development only).',
      },
    ],
    interviewTips: [
      '"How would you productionize this RAG API?" — Add auth (API key or OAuth), rate limiting per user, async endpoint (the rag_query is blocking), request/response logging, and horizontal scaling (multiple uvicorn workers).',
    ],
    gotchas: [
      'The current api.py is synchronous. In production, use async def ask() and async chromadb/LLM calls to handle concurrent requests without blocking.',
    ],
    relatedIds: ['w4-4', 'w4-5', 'w3-2'],
  },

  {
    id: 'w4-7',
    slug: 'project3-multi-agent',
    title: 'Project 3: Multi-Agent Workflow',
    file: '05_projects/project3_multi_agent/workflow.py',
    weekLabel: 'Week 4 — Projects',
    noApi: false,
    intro:
      'Project 3 is the most complex pattern in this repo. Planner decomposes the task → Executor runs each step → Validator quality-gates → Synthesizer combines. With structured JSON between agents, retries on validation failure, and full observability.',
    concepts: [
      {
        title: 'Agent communication protocol',
        body: 'All agents exchange Pydantic-validated JSON. The Planner returns TaskPlan (list of TaskStep). The Executor returns dict[int, str] (step number → result). The Validator returns ValidationReport (score + per-step verdicts). This structured communication is what makes the pipeline debuggable.',
      },
      {
        title: 'The validation retry loop',
        body: 'If the Validator scores below 0.7, re-run the Executor. Try up to MAX_RETRIES times. After max retries, proceed with best available results and flag for human review. The Validator is the quality gate that prevents bad results from silently propagating.',
      },
      {
        title: 'How this maps to LangGraph',
        body: 'Each agent is a node. Edges connect nodes (planner → executor → validator → synthesizer). The conditional edge from validator ("if score < 0.7, go back to executor") is the retry logic. This is exactly the pattern LangGraph is designed to express.',
      },
    ],
    interviewTips: [
      '"Design a multi-agent system for research + report writing." — Planner decomposes the task. Researcher, Analyzer, Writer execute in sequence. Validator quality-gates. Synthesizer combines. All communicate via structured JSON.',
    ],
    gotchas: [
      'The Validator itself can hallucinate scores. Validate the ValidationReport schema (score must be 0-1) just like any other structured output.',
    ],
    relatedIds: ['w3-1', 'w2-9', 'w3-8', 'w3-6'],
  },
]

// Lookup map for fast access
export const lessonsBySlug = Object.fromEntries(lessons.map((l) => [l.slug, l]))
export const lessonsById = Object.fromEntries(lessons.map((l) => [l.id, l]))
