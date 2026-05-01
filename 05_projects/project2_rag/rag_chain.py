"""
Project 2: RAG System — Full Query Pipeline (LCEL)
Retrieves relevant chunks → builds augmented prompt → generates grounded answer.

Pipeline: retriever | format_context | prompt | llm | parser

The LCEL (LangChain Expression Language) chain composes the three RAG phases
as Runnables connected by the | operator:
  1. Retrieve:  RunnableLambda(hybrid_search) → list of chunks
  2. Augment:   format_context + ChatPromptTemplate → augmented prompt
  3. Generate:  ChatAnthropic | StrOutputParser → grounded answer

Run: python 05_projects/project2_rag/rag_chain.py
(requires running ingest.py first)
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from retrieval import hybrid_search
from core.client import get_llm
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


def build_rag_chain(top_k: int = 4):
    """
    Build the LCEL RAG chain.

    The chain structure:
      {
        "context": retriever | format_context,  ← Step 1+2: retrieve & format
        "question": RunnablePassthrough()        ← pass the question through
      }
      | prompt_template                          ← Step 2: augment
      | llm                                      ← Step 3: generate
      | StrOutputParser()                        ← extract string from AIMessage
    """
    retriever = RunnableLambda(lambda q: hybrid_search(q, top_k=top_k))

    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM),
        ("human", "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"),
    ])

    return (
        {"context": retriever | format_context, "question": RunnablePassthrough()}
        | prompt
        | get_llm()
        | StrOutputParser()
    )


def rag_query(question: str, top_k: int = 4, verbose: bool = True) -> dict:
    """
    Full RAG pipeline via LCEL chain.
    Returns answer dict with sources and metadata.
    """
    if verbose:
        print(f"\nQ: {question}")
        print("─" * 60)

    # Step 1: Retrieve (for logging — the chain does this internally too)
    retrieved = hybrid_search(question, top_k=top_k)
    if verbose:
        print(f"Retrieved {len(retrieved)} chunks:")
        for r in retrieved:
            print(f"  [{r['source']}] rrf={r['rrf_score']:.4f}  {r['text'][:60]}...")

    # Step 2+3: Augment + Generate via LCEL chain
    chain = build_rag_chain(top_k=top_k)
    answer = chain.invoke(question)

    sources = list({r["source"] for r in retrieved})
    log.info(
        "rag.query",
        question=question[:50],
        chunks=len(retrieved),
        sources=sources,
    )

    if verbose:
        print(f"\nAnswer: {answer}")
        print(f"\nSources: {sources}")

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(retrieved),
    }


if __name__ == "__main__":
    print("=== RAG QUERY DEMO (LCEL Chain) ===")
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

    print("\n--- LCEL RAG Chain Pattern ---")
    print("  chain = (")
    print("      {\"context\": retriever | format_context, \"question\": RunnablePassthrough()}")
    print("      | ChatPromptTemplate.from_messages([...])")
    print("      | get_llm()")
    print("      | StrOutputParser()")
    print("  )")
    print("  answer = chain.invoke(question)")

    print("\n--- Three-Phase RAG Summary ---")
    print("1. Retrieve: hybrid BM25 + vector search → top-k chunks")
    print("2. Augment:  inject chunks as context via ChatPromptTemplate")
    print("3. Generate: LLM answers based ONLY on provided context")
    print("\nKey advantage: answer is grounded in real documents → fewer hallucinations")
    print("Key limitation: answer quality depends on retrieval quality (GIGO)")
