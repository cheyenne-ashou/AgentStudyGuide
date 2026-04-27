"""
Chunking Strategies Demo
Four approaches to splitting documents before embedding:
  1. Fixed-size — split every N words, no overlap
  2. Sliding window — fixed-size with overlap to preserve boundary context
  3. Sentence boundary — split on punctuation, preserves semantic units
  4. Paragraph boundary — split on blank lines, best for structured docs

No API needed — pure Python.

Key tradeoffs:
  Smaller chunks → higher precision retrieval, lose cross-sentence context
  Larger chunks  → better context per hit, more noise, higher embedding cost
  Sliding window → reduces "context cliff" at chunk edges, doubles stored chunks
  Sentence/para  → best semantic coherence, variable chunk size complicates indexing

Run: python 01_foundations/embeddings/chunking_strategies.py
"""
import re

DOCUMENT = """
Agentic AI systems represent a fundamental shift in how we design intelligent applications.
Unlike traditional chatbots that respond to single queries, agents maintain state across
multiple steps, use tools to interact with external systems, and execute long-horizon tasks.

The key components of an agent include a planner, which decides what actions to take,
an executor that carries out those actions by calling tools or APIs, and a memory system
that retains context across steps. Agents can use tools like web search, code execution,
and database access to go beyond what the base LLM can do on its own.

Memory in agents is divided into several types. Short-term memory lives in the context
window and disappears when the conversation ends. Long-term memory persists in a vector
database and can be retrieved by semantic similarity. Episodic memory records past agent
runs as a queryable history. Semantic memory stores factual key-value pairs with optional TTL.

Resiliency is critical in agentic systems because they make many non-deterministic LLM calls.
Common failure modes include hallucinations, tool call errors, infinite reasoning loops, and
latency spikes from external APIs. Good systems implement retry logic with exponential backoff,
max iteration limits, output schema validation, and human escalation paths for low-confidence situations.
""".strip()


def fixed_size(text: str, words_per_chunk: int = 40) -> list[str]:
    words = text.split()
    return [
        " ".join(words[i : i + words_per_chunk])
        for i in range(0, len(words), words_per_chunk)
        if words[i : i + words_per_chunk]
    ]


def sliding_window(text: str, chunk_words: int = 40, overlap_words: int = 10) -> list[str]:
    words = text.split()
    step = chunk_words - overlap_words
    return [
        " ".join(words[i : i + chunk_words])
        for i in range(0, len(words), step)
        if words[i : i + chunk_words]
    ]


def sentence_boundary(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def paragraph_boundary(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def print_strategy(name: str, chunks: list[str]) -> None:
    total_chars = sum(len(c) for c in chunks)
    avg_chars = total_chars / len(chunks) if chunks else 0
    print(f"\n{name}:")
    print(f"  Chunks: {len(chunks)}  |  Avg length: {avg_chars:.0f} chars")
    for i, chunk in enumerate(chunks[:2], 1):
        preview = (chunk[:90] + "...") if len(chunk) > 90 else chunk
        print(f"  [{i}] {preview}")
    if len(chunks) > 2:
        print(f"  ... ({len(chunks) - 2} more)")


if __name__ == "__main__":
    doc_words = len(DOCUMENT.split())
    print("=== CHUNKING STRATEGIES DEMO ===")
    print(f"\nDocument: {len(DOCUMENT)} chars, {doc_words} words\n")
    print("=" * 60)

    strategies = [
        ("Fixed-size (40 words)", fixed_size(DOCUMENT, 40)),
        ("Sliding window (40w, 10w overlap)", sliding_window(DOCUMENT, 40, 10)),
        ("Sentence boundary", sentence_boundary(DOCUMENT)),
        ("Paragraph boundary", paragraph_boundary(DOCUMENT)),
    ]

    for name, chunks in strategies:
        print_strategy(name, chunks)

    print("\n--- Tradeoff Summary ---")
    rows = [
        ("Fixed-size", "Simple, predictable", "Cuts mid-sentence, loses context"),
        ("Sliding window", "Reduces boundary problem", "~2x more chunks to store/search"),
        ("Sentence boundary", "Semantically coherent", "Variable size, harder to batch"),
        ("Paragraph boundary", "Best for structured docs", "Chunks can be very large"),
    ]
    for name, pro, con in rows:
        print(f"  {name:<20} Pro: {pro}")
        print(f"  {'':<20} Con: {con}")

    print("\nInterview answer: 'It depends on the document type and retrieval precision needed.'")
    print("For most RAG: sentence chunks with 10-15% overlap is a solid default.")
