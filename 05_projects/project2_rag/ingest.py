"""
Project 2: RAG System — Document Ingestion
Loads .txt files from sample_docs/, chunks them, embeds with sentence-transformers,
and stores in ChromaDB. Run this once before querying.

Run: python 05_projects/project2_rag/ingest.py
"""
import sys
import re
import shutil
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from core.logger import get_logger

log = get_logger(__name__)

DOCS_DIR = Path(__file__).parent / "sample_docs"
CHROMA_PATH = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "rag_docs"

# Chunking config
CHUNK_SIZE_WORDS = 80
CHUNK_OVERLAP_WORDS = 15


def load_documents(docs_dir: Path) -> list[tuple[str, str]]:
    """Load all .txt files. Returns list of (filename, content)."""
    docs = []
    for path in sorted(docs_dir.glob("*.txt")):
        content = path.read_text(encoding="utf-8").strip()
        docs.append((path.stem, content))
        log.info("ingest.loaded", file=path.name, chars=len(content))
    return docs


def sliding_window_chunks(text: str, chunk_words: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    """Split text into overlapping word-count chunks."""
    words = text.split()
    step = chunk_words - overlap
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_words])
        if chunk:
            chunks.append(chunk)
    return chunks


def build_collection(reset: bool = False) -> chromadb.Collection:
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            log.info("ingest.collection_reset")
        except Exception:
            pass

    return client.get_or_create_collection(
        COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def ingest(reset: bool = True) -> dict:
    collection = build_collection(reset=reset)

    if not reset and collection.count() > 0:
        print(f"Collection already has {collection.count()} chunks. Use reset=True to re-index.")
        return {"chunks": collection.count(), "skipped": True}

    docs = load_documents(DOCS_DIR)
    if not docs:
        raise FileNotFoundError(f"No .txt files found in {DOCS_DIR}")

    all_ids, all_texts, all_metas = [], [], []
    for doc_name, content in docs:
        chunks = sliding_window_chunks(content)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_name}_chunk_{i:03d}"
            all_ids.append(chunk_id)
            all_texts.append(chunk)
            all_metas.append({
                "source": doc_name,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "word_count": len(chunk.split()),
            })

    # Batch insert (ChromaDB handles up to 5461 items per batch)
    batch_size = 100
    for i in range(0, len(all_ids), batch_size):
        collection.add(
            ids=all_ids[i : i + batch_size],
            documents=all_texts[i : i + batch_size],
            metadatas=all_metas[i : i + batch_size],
        )

    log.info(
        "ingest.complete",
        documents=len(docs),
        chunks=len(all_ids),
        avg_chunks_per_doc=len(all_ids) / len(docs),
    )
    return {"documents": len(docs), "chunks": len(all_ids)}


if __name__ == "__main__":
    print("=== RAG INGESTION ===\n")
    print(f"Source: {DOCS_DIR}")
    print(f"Target: {CHROMA_PATH}\n")

    stats = ingest(reset=True)
    print(f"Indexed {stats['documents']} documents → {stats['chunks']} chunks")

    # Verify
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    col = client.get_collection(COLLECTION_NAME, embedding_function=ef)

    print(f"\nVerification: collection has {col.count()} chunks")
    sample = col.get(limit=2)
    for doc, meta in zip(sample["documents"], sample["metadatas"]):
        print(f"  [{meta['source']}] {doc[:80]}...")

    print(f"\nChunking config: {CHUNK_SIZE_WORDS} words/chunk, {CHUNK_OVERLAP_WORDS} overlap")
    print("Run rag_chain.py or api.py to query the system.")
