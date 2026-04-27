"""
Project 2: RAG System — Full Query Pipeline
Retrieves relevant chunks → builds augmented prompt → generates grounded answer.

Run: python 05_projects/project2_rag/rag_chain.py
(requires running ingest.py first)
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

from retrieval import hybrid_search
from core.client import get_client, MODEL, cached_system
from core.logger import get_logger

log = get_logger(__name__)

RAG_SYSTEM = """You are a helpful assistant that answers questions based on provided context.
Rules:
1. Answer ONLY based on the provided context. Do not use outside knowledge.
2. If the context doesn't contain enough information, say so explicitly.
3. Cite which source document(s) you used in your answer.
4. Be concise and accurate."""


def format_context(retrieved: list[dict]) -> str:
    parts = []
    for i, r in enumerate(retrieved, 1):
        parts.append(f"[Source {i}: {r['source']}]\n{r['text']}")
    return "\n\n".join(parts)


def rag_query(question: str, top_k: int = 4, verbose: bool = True) -> dict:
    """
    Full RAG pipeline:
      1. Retrieve: hybrid search for relevant chunks
      2. Augment: build prompt with context
      3. Generate: call Claude with grounded prompt
    """
    if verbose:
        print(f"\nQ: {question}")
        print("─" * 60)

    # Step 1: Retrieve
    retrieved = hybrid_search(question, top_k=top_k)
    if verbose:
        print(f"Retrieved {len(retrieved)} chunks:")
        for r in retrieved:
            print(f"  [{r['source']}] rrf={r['rrf_score']:.4f}  {r['text'][:60]}...")

    # Step 2: Augment
    context = format_context(retrieved)
    prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    # Step 3: Generate
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=cached_system(RAG_SYSTEM),
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.content[0].text.strip()

    sources = list({r["source"] for r in retrieved})
    log.info(
        "rag.query",
        question=question[:50],
        chunks=len(retrieved),
        sources=sources,
        tokens=response.usage.input_tokens + response.usage.output_tokens,
    )

    if verbose:
        print(f"\nAnswer: {answer}")
        print(f"\nSources: {sources}")

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(retrieved),
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
    }


if __name__ == "__main__":
    print("=== RAG QUERY DEMO ===")
    print("(Run ingest.py first if you haven't)\n")

    questions = [
        "What is the ReAct pattern and how does it work?",
        "How does RAG reduce hallucinations?",
        "What are the different memory types in an agent?",
        "How do you scale an agentic system?",
    ]

    for q in questions:
        result = rag_query(q)
        print(f"\n{'='*60}")

    print("\n--- RAG Pipeline Summary ---")
    print("1. Retrieve: hybrid BM25 + vector search → top-k chunks")
    print("2. Augment:  inject chunks as context into prompt")
    print("3. Generate: Claude answers based ONLY on provided context")
    print("\nKey advantage: answer is grounded in real documents → fewer hallucinations")
    print("Key limitation: answer quality depends on retrieval quality (GIGO)")
