"""
Project 2: RAG System — FastAPI Endpoint
Serves the RAG pipeline as a REST API.

Run: uvicorn 05_projects.project2_rag.api:app --reload
Then: curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"What is RAG?"}'

Or run directly: python 05_projects/project2_rag/api.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from rag_chain import rag_query
from core.logger import get_logger

log = get_logger(__name__)

app = FastAPI(
    title="RAG API",
    description="Document Q&A powered by hybrid retrieval + Claude",
    version="1.0.0",
)


# ── Request/Response models ───────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="The question to answer")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of chunks to retrieve")


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    retrieved_chunks: int
    tokens_used: int


class HealthResponse(BaseModel):
    status: str
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", message="RAG API is running")


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Answer a question using the RAG pipeline."""
    log.info("api.ask", question=request.question[:60])
    try:
        result = rag_query(request.question, top_k=request.top_k, verbose=False)
        return AskResponse(**result)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Document index not found. Run ingest.py first.",
        )
    except Exception as e:
        log.error("api.error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {
        "message": "RAG API",
        "endpoints": {
            "POST /ask": "Ask a question",
            "GET /health": "Health check",
            "GET /docs": "OpenAPI docs",
        },
        "example": {
            "curl": 'curl -X POST /ask -H "Content-Type: application/json" -d \'{"question":"What is RAG?"}\''
        },
    }


if __name__ == "__main__":
    print("Starting RAG API...")
    print("API docs: http://localhost:8000/docs")
    print("Ask endpoint: POST http://localhost:8000/ask")
    print("\nExample:")
    print('  curl -X POST http://localhost:8000/ask \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"question\": \"What is the ReAct pattern?\"}'")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
