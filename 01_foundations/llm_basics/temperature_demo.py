"""
Temperature Demo
Runs the same creative prompt at temperature 0, 0.7, and 1.0.
Run it twice to see t=0 is perfectly deterministic; t=1.0 varies every time.

Temperature controls the probability distribution over next tokens:
  t=0   → always pick the highest-probability token (greedy, deterministic)
  t=0.7 → balanced creativity (default for most chat use cases)
  t=1.0 → flat distribution, maximum variety (good for brainstorming)

Run: python 01_foundations/llm_basics/temperature_demo.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, FAST_MODEL

PROMPT = "Write a one-sentence tagline for a coffee shop called 'The Daily Grind'."


def generate(client, temperature: float) -> str:
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=80,
        temperature=temperature,
        messages=[{"role": "user", "content": PROMPT}],
    )
    return response.content[0].text.strip()


if __name__ == "__main__":
    client = get_client()

    print("=== TEMPERATURE DEMO ===")
    print(f"\nPrompt: {PROMPT}\n")
    print("Running each temperature twice to show (non-)determinism.\n")
    print("=" * 60)

    for temp in [0.0, 0.7, 1.0]:
        r1 = generate(client, temp)
        r2 = generate(client, temp)
        same = r1 == r2
        print(f"\nTemperature = {temp}:")
        print(f"  Run 1: {r1}")
        print(f"  Run 2: {r2}")
        print(f"  Identical: {'YES — deterministic' if same else 'NO — stochastic'}")

    print("\n--- Interview Takeaway ---")
    print("Use t=0 for: evals, structured extraction, tool calling (you want consistency)")
    print("Use t=0.7 for: conversation, explanations")
    print("Use t=1.0 for: brainstorming, creative generation")
    print("In agentic systems: keep tool-calling turns at t=0 to avoid hallucinated tool names.")
