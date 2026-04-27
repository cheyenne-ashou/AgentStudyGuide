"""
Prompting Strategies Demo
Runs the same math word problem through four prompting styles side-by-side:
zero-shot, few-shot, chain-of-thought, and ReAct.

Key insight: CoT and ReAct consistently outperform zero-shot on multi-step problems
because they force intermediate reasoning before committing to an answer.

Run: python 01_foundations/llm_basics/prompting_strategies.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, FAST_MODEL

TASK = (
    "A store sells apples for $0.50 each and bananas for $0.30 each. "
    "I buy 6 apples and 4 bananas. How much do I spend in total?"
)


def zero_shot(client) -> str:
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": TASK}],
    )
    return response.content[0].text.strip()


def few_shot(client) -> str:
    prompt = (
        "Q: Pens cost $1.00 each. I buy 3. Total?\n"
        "A: 3 × $1.00 = $3.00\n\n"
        "Q: Oranges cost $0.75 each. I buy 4. Total?\n"
        "A: 4 × $0.75 = $3.00\n\n"
        f"Q: {TASK}\n"
        "A:"
    )
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def chain_of_thought(client) -> str:
    prompt = f"{TASK}\n\nLet's think step by step."
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def react_style(client) -> str:
    prompt = (
        f"{TASK}\n\n"
        "Use this format:\n"
        "Thought: what do I need to figure out?\n"
        "Action: [calculation]\n"
        "Observation: [result]\n"
        "(repeat Thought/Action/Observation as needed)\n"
        "Final Answer: [total with $ sign]"
    )
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


if __name__ == "__main__":
    client = get_client()

    print("=== PROMPTING STRATEGIES DEMO ===")
    print(f"\nTask: {TASK}\n")
    print("=" * 60)

    for label, fn in [
        ("ZERO-SHOT", zero_shot),
        ("FEW-SHOT", few_shot),
        ("CHAIN-OF-THOUGHT", chain_of_thought),
        ("ReAct", react_style),
    ]:
        print(f"\n--- {label} ---")
        print(fn(client))

    print("\n--- Interview Takeaway ---")
    print("CoT/ReAct force the model to show reasoning before committing.")
    print("This reduces errors on multi-step problems by ~30-50%.")
    print("ReAct is the foundation of all agentic patterns.")
