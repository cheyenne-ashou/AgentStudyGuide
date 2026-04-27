"""
Vector Search with ChromaDB
Ingests 8 documents, runs 3 queries, shows similarity scores as bars.
Uses sentence-transformers for local embeddings — no API key needed.

ChromaDB returns L2 (Euclidean) distances by default; we convert to similarity.
For cosine similarity, configure the collection with cosine metric.

Run: python 01_foundations/embeddings/vector_search_demo.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

DOCUMENTS = [
    ("doc1", "Agents use tools like web search, code execution, and API calls to complete tasks."),
    ("doc2", "Vector databases store embeddings and support fast similarity search at scale."),
    ("doc3", "RAG retrieves relevant documents before generating an answer to ground the output."),
    ("doc4", "Hallucinations occur when LLMs generate plausible-sounding but false information."),
    ("doc5", "Prompt caching reduces latency and cost by reusing cached system prompt prefixes."),
    ("doc6", "Exponential backoff retries failed API calls with increasing wait times."),
    ("doc7", "The ReAct pattern interleaves reasoning and acting: Thought → Action → Observation."),
    ("doc8", "Chunking strategy affects retrieval precision: smaller chunks = higher precision."),
]

QUERIES = [
    "How do AI agents interact with external services?",
    "What is retrieval augmented generation?",
    "How do I make my agent more reliable?",
]


def run_demo():
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.EphemeralClient()

    # cosine metric gives similarity scores in [0, 1]
    collection = client.create_collection(
        "demo",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    ids, docs = zip(*DOCUMENTS)
    collection.add(ids=list(ids), documents=list(docs))
    print(f"Ingested {len(DOCUMENTS)} documents into ChromaDB (in-memory)\n")
    print("=" * 60)

    for query in QUERIES:
        results = collection.query(query_texts=[query], n_results=3)
        print(f"\nQuery: \"{query}\"")
        print(f"{'Score':>7}  Document")
        for doc, dist in zip(results["documents"][0], results["distances"][0]):
            score = 1 - dist  # cosine distance → similarity
            bar = "█" * int(max(0, score) * 25)
            print(f"  {score:.3f}  {bar}")
            print(f"         {doc[:75]}")


if __name__ == "__main__":
    print("=== VECTOR SEARCH DEMO ===\n")
    run_demo()

    print("\n--- Key Insights ---")
    print("Semantic search finds relevant docs even when exact words don't match.")
    print("'external services' matches 'API calls' — same concept, different words.")
    print("\nIn production:")
    print("  - Use Pinecone, Weaviate, or pgvector for persistence + scale")
    print("  - ChromaDB is great for local dev and prototyping")
    print("  - Hybrid search (BM25 + vector) beats either alone (see project2_rag/)")
