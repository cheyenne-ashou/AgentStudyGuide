"""
Evaluation Metrics Demo
Implements precision, recall, F1, and BLEU from scratch on toy examples.
No ML libraries — just the math.

Interview context: you'll be asked "how do you evaluate an agent?"
Know these metrics and when each is appropriate.

Run: python 01_foundations/ml_concepts/evaluation_metrics.py
"""
import math
from collections import Counter


# ── Classification Metrics ──────────────────────────────────────────────────

def precision(tp: int, fp: int) -> float:
    """Of all predicted positives, what fraction were actually positive?"""
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def recall(tp: int, fn: int) -> float:
    """Of all actual positives, what fraction did we find?"""
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def f1(p: float, r: float) -> float:
    """Harmonic mean of precision and recall."""
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


# ── BLEU Score (unigram for simplicity) ─────────────────────────────────────

def bleu_1(hypothesis: str, reference: str) -> float:
    """Unigram BLEU: what fraction of hypothesis words appear in reference?"""
    hyp_tokens = hypothesis.lower().split()
    ref_tokens = reference.lower().split()
    ref_counts = Counter(ref_tokens)

    matches = 0
    for token in hyp_tokens:
        if ref_counts.get(token, 0) > 0:
            matches += 1
            ref_counts[token] -= 1

    # Brevity penalty: penalize outputs shorter than reference
    bp = 1.0 if len(hyp_tokens) >= len(ref_tokens) else math.exp(1 - len(ref_tokens) / len(hyp_tokens))
    precision_score = matches / len(hyp_tokens) if hyp_tokens else 0.0
    return bp * precision_score


# ── RAG-specific: Context Recall ─────────────────────────────────────────────

def context_recall(retrieved_chunks: list[str], relevant_chunks: list[str]) -> float:
    """What fraction of the relevant chunks did we retrieve?"""
    if not relevant_chunks:
        return 1.0
    found = sum(1 for r in relevant_chunks if r in retrieved_chunks)
    return found / len(relevant_chunks)


def context_precision(retrieved_chunks: list[str], relevant_chunks: list[str]) -> float:
    """What fraction of retrieved chunks were actually relevant?"""
    if not retrieved_chunks:
        return 0.0
    relevant_set = set(relevant_chunks)
    correct = sum(1 for c in retrieved_chunks if c in relevant_set)
    return correct / len(retrieved_chunks)


if __name__ == "__main__":
    print("=== EVALUATION METRICS DEMO ===\n")

    # ── Example 1: Document classification ──────────────────────────────────
    print("--- Classification: Spam Detection ---")
    # 100 emails: 40 spam, 60 not spam
    # Model predicted 45 as spam: 35 correct (TP), 10 wrong (FP), missed 5 spam (FN)
    TP, FP, FN = 35, 10, 5
    p = precision(TP, FP)
    r = recall(TP, FN)
    f = f1(p, r)
    print(f"  TP={TP}, FP={FP}, FN={FN}")
    print(f"  Precision = {p:.3f}  (of flagged emails, {p*100:.0f}% are actually spam)")
    print(f"  Recall    = {r:.3f}  (of all spam emails, we caught {r*100:.0f}%)")
    print(f"  F1        = {f:.3f}  (balance between the two)")

    # ── Example 2: BLEU scores ───────────────────────────────────────────────
    print("\n--- BLEU Scores (text generation quality) ---")
    reference = "The agent uses tools to complete tasks efficiently"
    candidates = [
        ("Perfect match",      "The agent uses tools to complete tasks efficiently"),
        ("Good paraphrase",    "The agent uses tools to finish tasks effectively"),
        ("Partial match",      "An agent completes tasks using various tools"),
        ("Off-topic",          "The weather today is sunny and warm"),
    ]
    for label, hypothesis in candidates:
        score = bleu_1(hypothesis, reference)
        bar = "█" * int(score * 20)
        print(f"  {label:<20} BLEU-1={score:.3f}  {bar}")
        print(f"    Ref: {reference}")
        print(f"    Hyp: {hypothesis}")

    # ── Example 3: RAG retrieval quality ────────────────────────────────────
    print("\n--- RAG Retrieval Metrics ---")
    all_chunks = [f"chunk_{i}" for i in range(10)]
    relevant = ["chunk_2", "chunk_5", "chunk_7"]
    retrieved = ["chunk_2", "chunk_3", "chunk_5", "chunk_8"]

    cr = context_recall(retrieved, relevant)
    cp = context_precision(retrieved, relevant)
    print(f"  Relevant chunks:  {relevant}")
    print(f"  Retrieved chunks: {retrieved}")
    print(f"  Context Recall    = {cr:.3f}  ({cr*100:.0f}% of relevant chunks found)")
    print(f"  Context Precision = {cp:.3f}  ({cp*100:.0f}% of retrieved chunks are relevant)")

    print("\n--- When to Use Each Metric ---")
    metrics = [
        ("Precision", "When false positives are costly (e.g., spam filter, medical alerts)"),
        ("Recall",    "When false negatives are costly (e.g., fraud detection, safety)"),
        ("F1",        "When you need to balance both (most classification tasks)"),
        ("BLEU",      "Measuring text generation quality vs. reference (NMT, summarization)"),
        ("ROUGE",     "Recall-oriented BLEU variant — better for summarization tasks"),
        ("EM (exact match)", "Strict evaluation for extraction tasks (QA benchmarks)"),
    ]
    for name, when in metrics:
        print(f"  {name:<20} {when}")

    print("\n--- Interview Answer: 'How do you evaluate an agent?' ---")
    print("  1. Task-level: did it accomplish the goal? (human eval or gold labels)")
    print("  2. Step-level: were tool calls correct? (golden trace comparison)")
    print("  3. Retrieval: context precision/recall (for RAG components)")
    print("  4. Output quality: ROUGE/BLEU or LLM-as-judge for free-form answers")
    print("  5. Latency + cost: P50/P99 per task, tokens consumed")
