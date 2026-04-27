"""
Long-Term Memory with ChromaDB
Persists memories across sessions using vector similarity search.
Memories are stored with metadata and retrieved by semantic relevance.

Key difference from short-term: survives process restarts.
Key difference from a regular DB: queried by MEANING, not exact match.

Run: python 02_agentic_core/memory/long_term.py
"""
import sys
import uuid
import shutil
from pathlib import Path
from datetime import datetime

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from core.models import MemoryEntry

PERSIST_PATH = str(_root / "tmp_long_term_memory")


class LongTermMemory:
    """Vector-backed persistent memory. Store facts, retrieve by semantic similarity."""

    def __init__(self, session_id: str = "default", persist_path: str = PERSIST_PATH):
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self._client = chromadb.PersistentClient(path=persist_path)
        self._collection = self._client.get_or_create_collection(
            f"memory_{session_id}",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

    def store(self, content: str, metadata: dict | None = None) -> str:
        """Store a memory. Returns the memory ID."""
        memory_id = str(uuid.uuid4())[:8]
        self._collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[{**(metadata or {}), "stored_at": datetime.utcnow().isoformat()}],
        )
        return memory_id

    def query(self, text: str, top_k: int = 3) -> list[MemoryEntry]:
        """Retrieve top-k memories most semantically similar to the query."""
        n = min(top_k, self.count())
        if n == 0:
            return []
        results = self._collection.query(query_texts=[text], n_results=n)
        return [
            MemoryEntry(id=id_, content=doc, metadata=meta)
            for id_, doc, meta in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
            )
        ]

    def delete(self, memory_id: str) -> None:
        self._collection.delete(ids=[memory_id])

    def count(self) -> int:
        return self._collection.count()

    def clear_all(self) -> None:
        if self.count() > 0:
            all_ids = self._collection.get()["ids"]
            self._collection.delete(ids=all_ids)


if __name__ == "__main__":
    print("=== LONG-TERM MEMORY DEMO ===\n")

    # Clean start
    shutil.rmtree(PERSIST_PATH, ignore_errors=True)
    mem = LongTermMemory(session_id="demo")

    facts = [
        ("The user prefers Python over JavaScript for backend services", {"category": "preference"}),
        ("The user's name is Alex and they work at a seed-stage startup", {"category": "identity"}),
        ("Last session: debugged a database connection timeout issue in PostgreSQL", {"category": "history"}),
        ("The project uses FastAPI, ChromaDB, and runs on AWS ECS", {"category": "tech_stack"}),
        ("The user asked about RAG chunking strategies during the last session", {"category": "history"}),
        ("The team has 3 engineers, 1 PM, and no dedicated ML infrastructure", {"category": "context"}),
        ("User prefers concise answers without long explanations", {"category": "preference"}),
        ("Interview prep timeline: 3 weeks from now", {"category": "goal"}),
        ("The codebase is ~15k lines of Python, no test coverage yet", {"category": "tech_stack"}),
        ("User is strongest in backend engineering, learning ML/AI now", {"category": "identity"}),
    ]

    print(f"Storing {len(facts)} memories...\n")
    ids = [mem.store(content, meta) for content, meta in facts]
    print(f"Total stored: {mem.count()}\n")
    print("=" * 60)

    queries = [
        "What are the user's technology preferences?",
        "What is the user working on right now?",
        "What happened in previous sessions?",
    ]

    for query in queries:
        print(f"\nQuery: \"{query}\"")
        results = mem.query(query, top_k=3)
        for entry in results:
            print(f"  [{entry.id}] ({entry.metadata.get('category', '?')}) {entry.content}")

    # Demonstrate persistence: close and reopen
    print("\n--- Persistence Test ---")
    print("Closing and reopening the memory store...")
    del mem
    mem2 = LongTermMemory(session_id="demo")
    print(f"Memories after reopen: {mem2.count()} (same as before)")

    # Cleanup
    shutil.rmtree(PERSIST_PATH, ignore_errors=True)
    print("(tmp memory cleaned up)")

    print("\n--- Interview Answer: 'How would you design memory for an agent?' ---")
    print("  Short-term: context window (current session, auto-managed)")
    print("  Long-term: vector DB like ChromaDB/Pinecone (cross-session, semantic retrieval)")
    print("  Episodic: JSON/DB log of past runs (what did I do before?)")
    print("  Semantic: key-value store for user facts (name, preferences)")
    print("  Combine: on each turn, retrieve top-k long-term memories → inject into context")
