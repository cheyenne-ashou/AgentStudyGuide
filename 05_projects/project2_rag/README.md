# Project 2: RAG System

A complete Retrieval-Augmented Generation system with hybrid search and FastAPI.

## Run it

```bash
# Step 1: Index documents
python 05_projects/project2_rag/ingest.py

# Step 2: Query the CLI
python 05_projects/project2_rag/rag_chain.py

# Step 3: Start the API
uvicorn 05_projects.project2_rag.api:app --reload

# Step 4: Query the API
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the ReAct pattern?"}'
```

## Pipeline

```
User Question
      ↓
  Retrieval (retrieval.py)
  ├── BM25 keyword search
  ├── Vector similarity search (ChromaDB)
  └── RRF fusion → top-k chunks
      ↓
  Augmentation (rag_chain.py)
  └── Build prompt: context + question
      ↓
  Generation (Claude via core/client.py)
  └── Answer grounded in retrieved context
      ↓
  Response: {answer, sources, tokens}
```

## Files

| File | Purpose |
|---|---|
| `ingest.py` | Load docs, chunk, embed, store in ChromaDB |
| `retrieval.py` | Hybrid BM25 + vector search with RRF |
| `rag_chain.py` | Full RAG pipeline (retrieve → augment → generate) |
| `api.py` | FastAPI REST endpoint |
| `sample_docs/` | Three demo documents on agentic AI topics |

## What makes this production-worthy

1. **Hybrid search**: BM25 + vector outperforms either alone
2. **RRF re-ranking**: proven fusion algorithm, no ML needed
3. **Source citations**: every answer includes source documents
4. **Schema validation**: request/response validated with Pydantic
5. **Prompt caching**: system prompt cached across requests (5-min TTL)
6. **Error handling**: graceful errors if index doesn't exist
