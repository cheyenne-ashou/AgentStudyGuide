"""
RAG vs Fine-tuning vs Prompting
Prints a decision framework and asks Claude to explain the tradeoffs.
Know this cold — it comes up in every agentic AI interview.

Run: python 01_foundations/ml_concepts/rag_vs_finetuning.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, FAST_MODEL, cached_system

DECISION_TABLE = """
┌─────────────────────┬─────────────────┬──────────────────┬──────────────────┐
│                     │   Prompting     │      RAG         │   Fine-tuning    │
├─────────────────────┼─────────────────┼──────────────────┼──────────────────┤
│ Knowledge freshness │ Static (cutoff) │ Real-time        │ Static (cutoff)  │
│ Knowledge source    │ Training data   │ External docs    │ Training data    │
│ Cost per query      │ Low             │ Medium (+search) │ Low (after train)│
│ Upfront cost        │ None            │ Indexing only    │ High (GPU time)  │
│ Transparency        │ None            │ Citations        │ None             │
│ Hallucination risk  │ High            │ Lower (grounded) │ Medium           │
│ Domain adaptation   │ Via prompt      │ Via docs         │ Deep adaptation  │
│ Latency             │ Fast            │ Slower (+search) │ Fast             │
│ Data needed         │ None            │ Documents        │ Labeled examples │
└─────────────────────┴─────────────────┴──────────────────┴──────────────────┘
"""

DECISION_TREE = """
Decision Tree: Which approach to use?

Use PROMPTING when:
  → Task needs no external knowledge
  → Knowledge is already in training data
  → You need the fastest/cheapest solution

Use RAG when:
  → Knowledge changes frequently (prices, docs, news)
  → You need citations / source attribution
  → Private/proprietary data that wasn't in training
  → Reducing hallucinations is critical

Use FINE-TUNING when:
  → You need a specific output format/style
  → Domain vocabulary is highly specialized (medical, legal)
  → You have thousands of labeled examples
  → Prompt engineering has hit a ceiling
  → Latency/cost is critical at scale (smaller fine-tuned model)

Use RAG + FINE-TUNING when:
  → You need both dynamic knowledge AND style adaptation
  → Example: customer support bot with company docs + formal tone
"""


def get_claude_explanation(client) -> str:
    system = cached_system(
        "You are an AI systems expert preparing a candidate for a senior engineering interview. "
        "Give concise, technically precise answers with real-world examples."
    )
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=500,
        system=system,
        messages=[{
            "role": "user",
            "content": (
                "In 4-5 sentences, explain when you would choose RAG over fine-tuning "
                "for an enterprise AI assistant. Give a concrete example."
            ),
        }],
    )
    return response.content[0].text.strip()


if __name__ == "__main__":
    print("=== RAG vs FINE-TUNING vs PROMPTING ===\n")
    print(DECISION_TABLE)
    print(DECISION_TREE)

    print("--- Claude's Interview-Ready Explanation ---")
    client = get_client()
    print(get_claude_explanation(client))

    print("\n--- One-Line Interview Answer ---")
    print("'RAG for dynamic knowledge with citations; fine-tuning for style/format adaptation.")
    print(" Most production systems use both together.'")
