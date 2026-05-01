"""
Golden Dataset Evaluation Harness
Runs the LLM on a fixed set of question/answer pairs and scores performance.

Golden datasets are "ground truth" examples you maintain over time.
They let you detect regressions: "did changing the prompt break anything?"

Scoring strategies:
  1. Exact match — answer must match exactly (good for factual/structured)
  2. Keyword match — answer must contain key terms (good for explanations)
  3. LLM-as-judge — another LLM grades the answer (good for free-form)

Run: python 04_resiliency/evaluation/golden_dataset.py
"""
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.messages import HumanMessage
from core.client import get_fast_llm, FAST_MODEL
from core.models import EvalResult
from core.logger import get_logger

log = get_logger(__name__)


@dataclass
class GoldenExample:
    id: str
    question: str
    expected_keywords: list[str]
    min_keyword_matches: int = 2
    expected_exact: str | None = None
    metadata: dict = field(default_factory=dict)


# ── Golden dataset ────────────────────────────────────────────────────────────

GOLDEN_DATASET: list[GoldenExample] = [
    GoldenExample(
        id="rag_definition",
        question="What does RAG stand for and what problem does it solve?",
        expected_keywords=["retrieval", "augmented", "generation", "hallucination", "knowledge", "documents"],
        min_keyword_matches=3,
    ),
    GoldenExample(
        id="react_pattern",
        question="What is the ReAct pattern in agentic AI?",
        expected_keywords=["reason", "act", "thought", "action", "observation", "tool", "loop"],
        min_keyword_matches=3,
    ),
    GoldenExample(
        id="langgraph_stategraph",
        question="What is a LangGraph StateGraph and what does it replace?",
        expected_keywords=["graph", "node", "edge", "state", "loop", "explicit"],
        min_keyword_matches=3,
    ),
    GoldenExample(
        id="chunking_tradeoff",
        question="What is the tradeoff between small and large chunk sizes in RAG?",
        expected_keywords=["precision", "recall", "context", "noise", "small", "large"],
        min_keyword_matches=3,
    ),
    GoldenExample(
        id="hallucination_cause",
        question="Why do LLMs hallucinate?",
        expected_keywords=["training", "probability", "plausible", "verify", "fact", "generate"],
        min_keyword_matches=2,
    ),
    GoldenExample(
        id="memory_types",
        question="Name the four types of memory in an AI agent.",
        expected_keywords=["short", "long", "episodic", "semantic"],
        min_keyword_matches=4,
    ),
    GoldenExample(
        id="rag_vs_finetuning",
        question="When should you use fine-tuning instead of RAG?",
        expected_keywords=["style", "format", "domain", "vocabulary", "labels", "training"],
        min_keyword_matches=2,
    ),
    GoldenExample(
        id="agent_loop",
        question="Describe the basic agent loop in one or two sentences.",
        expected_keywords=["tool", "observe", "repeat", "action", "think", "plan"],
        min_keyword_matches=2,
    ),
    GoldenExample(
        id="guardrails",
        question="What are guardrails in agentic AI systems?",
        expected_keywords=["validation", "input", "output", "safety", "schema", "sanitize", "prevent"],
        min_keyword_matches=2,
    ),
    GoldenExample(
        id="memorysaver",
        question="What is LangGraph's MemorySaver and what does it enable?",
        expected_keywords=["checkpoint", "thread", "state", "persist", "conversation", "session"],
        min_keyword_matches=2,
    ),
]


# ── Evaluation functions ──────────────────────────────────────────────────────

def keyword_score(answer: str, keywords: list[str], min_matches: int) -> tuple[bool, float]:
    lower = answer.lower()
    matches = sum(1 for kw in keywords if kw.lower() in lower)
    score = matches / len(keywords)
    passed = matches >= min_matches
    return passed, score


def llm_judge_score(question: str, answer: str, llm) -> tuple[bool, float]:
    """Use a second LLM call to judge the quality of the answer."""
    prompt = (
        f"Question: {question}\n"
        f"Answer: {answer}\n\n"
        "Rate this answer on a scale of 0-10 where:\n"
        "10 = perfect, complete, accurate\n"
        " 7 = mostly correct with minor gaps\n"
        " 4 = partially correct\n"
        " 1 = mostly wrong or missing key info\n\n"
        "Reply with ONLY a number from 0-10."
    )
    response = llm.with_config({"max_tokens": 5}).invoke([HumanMessage(content=prompt)])
    try:
        score = float(response.content.strip()) / 10.0
        return score >= 0.7, score
    except ValueError:
        return False, 0.0


def run_evaluation(
    examples: list[GoldenExample],
    use_llm_judge: bool = False,
    verbose: bool = True,
) -> list[EvalResult]:
    llm = get_fast_llm()
    results: list[EvalResult] = []

    if verbose:
        print(f"Running evaluation on {len(examples)} examples...\n")

    for ex in examples:
        response = llm.invoke([HumanMessage(content=ex.question)])
        answer = response.content.strip()

        if ex.expected_exact:
            passed = ex.expected_exact.lower() in answer.lower()
            score = 1.0 if passed else 0.0
            notes = "exact match"
        elif use_llm_judge:
            passed, score = llm_judge_score(ex.question, answer, llm)
            notes = "llm-judge"
        else:
            passed, score = keyword_score(answer, ex.expected_keywords, ex.min_keyword_matches)
            lower = answer.lower()
            found = [kw for kw in ex.expected_keywords if kw.lower() in lower]
            notes = f"keywords found: {found}"

        result = EvalResult(
            question=ex.question,
            expected=", ".join(ex.expected_keywords),
            actual=answer[:200],
            passed=passed,
            score=score,
            notes=notes,
        )
        results.append(result)

        if verbose:
            icon = "✓" if passed else "✗"
            print(f"  {icon} [{ex.id}] score={score:.2f}")
            if not passed:
                print(f"      Q: {ex.question[:60]}")
                print(f"      A: {answer[:100]}...")

    return results


def print_summary(results: list[EvalResult]) -> None:
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    avg_score = sum(r.score for r in results) / total if total else 0

    print(f"\n{'='*50}")
    print(f"EVALUATION SUMMARY")
    print(f"{'='*50}")
    print(f"  Passed:    {passed}/{total} ({passed/total*100:.0f}%)")
    print(f"  Avg score: {avg_score:.3f}")

    failures = [r for r in results if not r.passed]
    if failures:
        print(f"\n  Failed cases:")
        for r in failures:
            print(f"    • {r.question[:60]}")
            print(f"      Missing keywords from: {r.expected[:60]}")


if __name__ == "__main__":
    print("=== GOLDEN DATASET EVALUATION ===\n")
    results = run_evaluation(GOLDEN_DATASET, use_llm_judge=False)
    print_summary(results)

    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": FAST_MODEL,
        "passed": sum(1 for r in results if r.passed),
        "total": len(results),
        "results": [r.model_dump() for r in results],
    }
    out_path = _root / "04_resiliency" / "evaluation" / "last_eval.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults saved to: {out_path}")

    print("\n--- Interview Answer: 'How do you evaluate an agent?' ---")
    print("  1. Golden dataset: run on known Q/A pairs, track score over time")
    print("  2. LLM-as-judge: use a second model to grade free-form answers")
    print("  3. Step-level eval: check that tool calls match expected trace")
    print("  4. Human eval: for high-stakes or ambiguous cases")
    print("  5. Regression alerts: fail CI if score drops below baseline")
