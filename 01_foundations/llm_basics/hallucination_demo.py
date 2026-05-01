"""
Hallucination Demo
Asks about a made-up company (Zylantrix Corp) three ways:
  1. No mitigation — model may confidently fabricate details
  2. Grounding — provide factual context before asking
  3. Uncertainty prompting — instruct the model to say "I don't know"
  4. RAG simulation — restrict to retrieved documents (previews Week 4 pattern)

Why LLMs hallucinate:
  - Trained to produce fluent, plausible text — not to verify facts
  - No internal "I don't know" signal — always outputs something
  - Rare or fictional entities activate nearest real-world patterns

LangGraph concept: each mitigation is an LCEL chain. The RAG simulation
previews the retriever | prompt | llm | parser pattern from Project 2.

Run: python 01_foundations/llm_basics/hallucination_demo.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from core.client import get_fast_llm

QUESTION = "What were the main products and founding year of Zylantrix Corp?"

llm = get_fast_llm()
parser = StrOutputParser()


def no_mitigation() -> str:
    chain = ChatPromptTemplate.from_messages([
        ("human", "{question}"),
    ]) | llm | parser
    return chain.invoke({"question": QUESTION})


def with_grounding() -> str:
    context = (
        "CONTEXT: Zylantrix Corp is a fictional company invented for a demo. "
        "It has no real existence, products, or history.\n\n"
    )
    chain = ChatPromptTemplate.from_messages([
        ("human", "{context}{question}"),
    ]) | llm | parser
    return chain.invoke({"context": context, "question": QUESTION})


def with_uncertainty_instruction() -> str:
    # System messages instruct the model at the persona level
    chain = ChatPromptTemplate.from_messages([
        ("system", "If you do not have reliable information about something, "
                   "say 'I don't have reliable information about this' rather than guessing."),
        ("human", "{question}"),
    ]) | llm | parser
    return chain.invoke({"question": QUESTION})


def with_rag_simulation() -> str:
    # Simulate what a real RAG chain looks like:
    # retriever → format_context → prompt | llm | parser
    # In Project 2, 'retriever' is a real ChromaDB + BM25 hybrid search.
    def mock_retriever(question: str) -> str:
        return "[Search results: No documents found matching 'Zylantrix Corp']"

    retriever = RunnableLambda(mock_retriever)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | ChatPromptTemplate.from_messages([
            ("human",
             "Answer the following question using ONLY the provided search results. "
             "If the search results don't contain the answer, say so.\n\n"
             "Search results:\n{context}\n\n"
             "Question: {question}"),
        ])
        | llm
        | parser
    )
    return chain.invoke(QUESTION)


if __name__ == "__main__":
    print("=== HALLUCINATION DEMO ===")
    print(f"\nQuestion: {QUESTION}")
    print("(Zylantrix Corp is completely fictional — watch what the model does)\n")
    print("=" * 60)

    print("\n1. NO MITIGATION — model may hallucinate:")
    print(no_mitigation())

    print("\n2. GROUNDING — provide factual context:")
    print(with_grounding())

    print("\n3. UNCERTAINTY INSTRUCTION — instruct model to admit ignorance:")
    print(with_uncertainty_instruction())

    print("\n4. RAG SIMULATION — restrict to retrieved documents:")
    print(with_rag_simulation())

    print("\n--- RAG Chain Pattern (preview of Project 2) ---")
    print("  chain = (")
    print("      {\"context\": retriever, \"question\": RunnablePassthrough()}")
    print("      | prompt")
    print("      | llm")
    print("      | StrOutputParser()")
    print("  )")

    print("\n--- Mitigation Summary ---")
    mitigations = [
        ("RAG", "Retrieve real docs before generating — grounds every claim"),
        ("Grounding", "Always inject context from trusted sources into the prompt"),
        ("Uncertainty prompting", "System message: 'say I don't know if unsure'"),
        ("Structured outputs", "Constrain output schema — model can't invent fields"),
        ("Confidence scoring", "Ask model to rate its own confidence; flag low scores"),
        ("Human review", "Required for high-stakes outputs"),
    ]
    for name, desc in mitigations:
        print(f"  {name:<25} {desc}")
