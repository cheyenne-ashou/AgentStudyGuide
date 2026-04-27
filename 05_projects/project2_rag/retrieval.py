"""
Project 2: RAG System — Hybrid Retrieval
Combines BM25 keyword search with vector similarity search,
then merges results using Reciprocal Rank Fusion (RRF).

Why hybrid?
  BM25 (keyword): great for exact term matches, fails on synonyms
  Vector: great for semantic similarity, misses rare exact terms
  Combined: beats either alone on most benchmarks

Run: python 05_projects/project2_rag/retrieval.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from rank_bm25 import BM25Okapi
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from core.logger import get_logger

log = get_logger(__name__)

CHROMA_PATH = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "rag_docs"
RRF_K = 60  # RRF constant — higher K = less weight on rank position


def load_collection() -> chromadb.Collection:
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(COLLECTION_NAME, embedding_function=ef)


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    """
    Merge multiple ranked lists using RRF.
    Score(d) = sum over all rankings: 1 / (k + rank(d))
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Hybrid retrieval:
      1. BM25 keyword search over all chunks
      2. Vector similarity search via ChromaDB
      3. RRF to merge and re-rank
    Returns top_k results with source metadata.
    """
    collection = load_collection()

    # Load all documents for BM25 (in production: cache this)
    all_data = collection.get()
    all_ids = all_data["ids"]
    all_docs = all_data["documents"]
    all_metas = all_data["metadatas"]

    if not all_docs:
        raise ValueError("Collection is empty. Run ingest.py first.")

    # ── BM25 search ──────────────────────────────────────────────────────────
    tokenized_corpus = [doc.lower().split() for doc in all_docs]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(query.lower().split())

    # Rank by BM25 score (descending)
    bm25_ranked = [
        all_ids[i]
        for i in sorted(range(len(bm25_scores)), key=lambda x: bm25_scores[x], reverse=True)
    ]

    # ── Vector search ─────────────────────────────────────────────────────────
    n_results = min(top_k * 2, len(all_ids))
    vector_results = collection.query(query_texts=[query], n_results=n_results)
    vector_ranked = vector_results["ids"][0]

    # ── RRF fusion ───────────────────────────────────────────────────────────
    fused = reciprocal_rank_fusion(
        [bm25_ranked[:top_k * 2], vector_ranked],
        k=RRF_K,
    )

    # Fetch top_k results with metadata
    id_to_doc = dict(zip(all_ids, all_docs))
    id_to_meta = dict(zip(all_ids, all_metas))

    results = []
    for doc_id, rrf_score in fused[:top_k]:
        results.append({
            "id": doc_id,
            "text": id_to_doc[doc_id],
            "source": id_to_meta[doc_id].get("source", "unknown"),
            "rrf_score": rrf_score,
            "bm25_rank": bm25_ranked.index(doc_id) + 1 if doc_id in bm25_ranked else 999,
            "vector_rank": vector_ranked.index(doc_id) + 1 if doc_id in vector_ranked else 999,
        })

    log.info("retrieval.hybrid", query=query[:50], results=len(results))
    return results


if __name__ == "__main__":
    print("=== HYBRID RETRIEVAL DEMO ===\n")

    test_queries = [
        "How do AI agents use tools?",
        "What is RAG and how does it work?",
        "How do you prevent LLM hallucinations?",
        "What are the components of an agentic system?",
    ]

    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        print(f"{'Score':>7}  {'BM25':>5}  {'Vec':>4}  Source  Text")
        print("-" * 70)

        results = hybrid_search(query, top_k=3)
        for r in results:
            text_preview = r["text"][:50].replace("\n", " ")
            print(
                f"  {r['rrf_score']:.4f}  "
                f"#{r['bm25_rank']:<4}  "
                f"#{r['vector_rank']:<3}  "
                f"{r['source']:<12}  "
                f"{text_preview}..."
            )

    print("\n--- RRF Explained ---")
    print("  Score = sum(1 / (60 + rank)) across BM25 and vector rankings")
    print("  A document ranked #1 in both gets: 1/61 + 1/61 = 0.0328")
    print("  A document ranked #1 in only BM25: 1/61 = 0.0164")
    print("  Docs that appear in both lists are boosted — reduces both false positives")
