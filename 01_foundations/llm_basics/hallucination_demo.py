"""
Hallucination Demo
Asks about a made-up company (Zylantrix Corp) three ways:
  1. No mitigation — model may confidently fabricate details
  2. Grounding — provide factual context before asking
  3. Uncertainty prompting — instruct the model to say "I don't know"

Why LLMs hallucinate:
  - Trained to produce fluent, plausible text — not to verify facts
  - No internal "I don't know" signal — always outputs something
  - Rare or fictional entities activate nearest real-world patterns

Run: python 01_foundations/llm_basics/hallucination_demo.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, FAST_MODEL

QUESTION = "What were the main products and founding year of Zylantrix Corp?"


def no_mitigation(client) -> str:
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": QUESTION}],
    )
    return response.content[0].text.strip()


def with_grounding(client) -> str:
    context = (
        "CONTEXT: Zylantrix Corp is a fictional company invented for a demo. "
        "It has no real existence, products, or history.\n\n"
    )
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": context + QUESTION}],
    )
    return response.content[0].text.strip()


def with_uncertainty_instruction(client) -> str:
    system = "If you do not have reliable information about something, say 'I don't have reliable information about this' rather than guessing."
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=200,
        system=system,
        messages=[{"role": "user", "content": QUESTION}],
    )
    return response.content[0].text.strip()


def with_rag_simulation(client) -> str:
    retrieved_docs = "[Search results: No documents found matching 'Zylantrix Corp']"
    prompt = (
        f"Answer the following question using ONLY the provided search results. "
        f"If the search results don't contain the answer, say so.\n\n"
        f"Search results:\n{retrieved_docs}\n\n"
        f"Question: {QUESTION}"
    )
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


if __name__ == "__main__":
    client = get_client()

    print("=== HALLUCINATION DEMO ===")
    print(f"\nQuestion: {QUESTION}")
    print("(Zylantrix Corp is completely fictional — watch what the model does)\n")
    print("=" * 60)

    print("\n1. NO MITIGATION — model may hallucinate:")
    print(no_mitigation(client))

    print("\n2. GROUNDING — provide factual context:")
    print(with_grounding(client))

    print("\n3. UNCERTAINTY INSTRUCTION — instruct model to admit ignorance:")
    print(with_uncertainty_instruction(client))

    print("\n4. RAG SIMULATION — restrict to retrieved documents:")
    print(with_rag_simulation(client))

    print("\n--- Mitigation Summary ---")
    mitigations = [
        ("RAG", "Retrieve real docs before generating — grounds every claim"),
        ("Grounding", "Always inject context from trusted sources into the prompt"),
        ("Uncertainty prompting", "System prompt: 'say I don't know if unsure'"),
        ("Structured outputs", "Constrain output schema — model can't invent fields"),
        ("Confidence scoring", "Ask model to rate its own confidence; flag low scores"),
        ("Human review", "Required for high-stakes outputs"),
    ]
    for name, desc in mitigations:
        print(f"  {name:<25} {desc}")
