"""
Temperature Demo
Runs the same creative prompt at temperature 0, 0.7, and 1.0.
Run it twice to see t=0 is perfectly deterministic; t=1.0 varies every time.

Temperature controls the probability distribution over next tokens:
  t=0   → always pick the highest-probability token (greedy, deterministic)
  t=0.7 → balanced creativity (default for most chat use cases)
  t=1.0 → flat distribution, maximum variety (good for brainstorming)

LangGraph concept: ChatAnthropic accepts temperature at construction time.
Use llm.with_config({"temperature": 0.7}) to change temperature per-call
without rebuilding the chain.

Run: python 01_foundations/llm_basics/temperature_demo.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from core.client import FAST_MODEL

PROMPT = "Write a one-sentence tagline for a coffee shop called 'The Daily Grind'."


def generate(temperature: float) -> str:
    # Instantiate with explicit temperature to show how it's configured
    llm = ChatAnthropic(model=FAST_MODEL, temperature=temperature)
    response = llm.invoke([HumanMessage(content=PROMPT)])
    return response.content


if __name__ == "__main__":
    print("=== TEMPERATURE DEMO ===")
    print(f"\nPrompt: {PROMPT}\n")
    print("Running each temperature twice to show (non-)determinism.\n")
    print("=" * 60)

    for temp in [0.0, 0.7, 1.0]:
        r1 = generate(temp)
        r2 = generate(temp)
        same = r1 == r2
        print(f"\nTemperature = {temp}:")
        print(f"  Run 1: {r1}")
        print(f"  Run 2: {r2}")
        print(f"  Identical: {'YES — deterministic' if same else 'NO — stochastic'}")

    print("\n--- with_config() alternative ---")
    print("  # Change temperature per-call without rebuilding the chain:")
    print("  chain.invoke({'task': '...'}, config={'temperature': 0.9})")

    print("\n--- Interview Takeaway ---")
    print("Use t=0 for: evals, structured extraction, tool calling (you want consistency)")
    print("Use t=0.7 for: conversation, explanations")
    print("Use t=1.0 for: brainstorming, creative generation")
    print("In agentic systems: keep tool-calling turns at t=0 to avoid hallucinated tool names.")
