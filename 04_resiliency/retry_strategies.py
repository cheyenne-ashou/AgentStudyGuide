"""
Retry Strategies with LangGraph Runnables
Uses .with_retry() and .with_fallbacks() instead of the tenacity decorator pattern.

Three patterns:
  1. .with_retry()     — retry N times with exponential backoff and jitter
  2. .with_fallbacks() — switch to a backup model on failure
  3. Combined          — retry, then fall back (recommended for production)

In agentic systems, you MUST have retries. External APIs fail.
LLMs return transient errors. Networks are unreliable.
LangGraph Runnables handle this composably — no decorator imports needed.

The plain Python retry loop below (Demo 1) still teaches the concept,
but for LLM calls, always prefer .with_retry() — it integrates with
the Runnable interface and applies to chains, retrievers, and tool nodes.

Run: python 04_resiliency/retry_strategies.py
"""
import sys
import time
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.messages import HumanMessage
from core.client import get_llm, get_fast_llm, MODEL, FAST_MODEL
from core.logger import get_logger

log = get_logger(__name__)


# ── 1. Plain Python retry loop (teaches the concept) ─────────────────────────

_call_count = 0

def flaky_api_call(succeed_on_attempt: int = 3) -> str:
    """Simulates a flaky external API that fails the first N-1 times."""
    global _call_count
    _call_count += 1
    print(f"  [Attempt {_call_count}]", end=" ")
    if _call_count < succeed_on_attempt:
        print("FAIL (simulated)")
        raise ConnectionError(f"Simulated API failure on attempt {_call_count}")
    print("SUCCESS")
    return "API response: data successfully retrieved"


def retry_with_backoff(fn, max_attempts: int = 5, base_delay: float = 0.1) -> str:
    """Manual exponential backoff — shows the pattern before using .with_retry()."""
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except ConnectionError as e:
            if attempt == max_attempts:
                raise
            wait = base_delay * (2 ** (attempt - 1))
            print(f"    Waiting {wait:.1f}s before retry...")
            time.sleep(wait)
    raise RuntimeError("Unreachable")


# ── 2. LangGraph .with_retry() ───────────────────────────────────────────────

def demo_with_retry() -> None:
    """
    .with_retry() wraps the LLM as a Runnable with built-in backoff.
    Replaces: @retry(retry_if_exception_type(RateLimitError), stop_after_attempt(4), ...)
    """
    print("--- Pattern 2: .with_retry() ---")
    llm = get_fast_llm().with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,  # jitter prevents thundering herd
    )
    result = llm.invoke([HumanMessage(content="In one sentence: what is exponential backoff?")])
    print(f"  Response: {result.content}")
    print("  If a transient error occurs, .with_retry() retries up to 3× automatically.")


# ── 3. .with_fallbacks() ─────────────────────────────────────────────────────

def demo_with_fallbacks() -> None:
    """
    .with_fallbacks() switches to a backup model if the primary exhausts retries.
    Replaces: hand-written ModelFallbackChain class.
    """
    print("\n--- Pattern 3: .with_fallbacks() ---")
    llm = get_llm().with_fallbacks(
        [get_fast_llm()],
        exceptions_to_handle=(Exception,),
    )
    result = llm.invoke([HumanMessage(content="In one sentence: why use a model fallback chain?")])
    print(f"  Response: {result.content}")
    print(f"  Chain: {MODEL} → {FAST_MODEL} (on failure)")


# ── 4. Combined: retry + fallback ─────────────────────────────────────────────

def demo_combined() -> None:
    """
    The recommended production pattern: retry primary, then fall back.
    The fallback model itself can also have retries.
    """
    print("\n--- Pattern 4: Combined retry + fallback (production) ---")
    resilient_llm = (
        get_llm()
        .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
        .with_fallbacks(
            [get_fast_llm().with_retry(stop_after_attempt=2)],
            exceptions_to_handle=(Exception,),
        )
    )
    result = resilient_llm.invoke(
        [HumanMessage(content="In one sentence: when should you NOT retry a failed API call?")]
    )
    print(f"  Response: {result.content}")
    print("  Behavior: retry primary 3×, then retry fallback 2×, then raise")


if __name__ == "__main__":
    print("=== RETRY STRATEGIES DEMO (LangGraph) ===\n")

    # ── Demo 1: Plain Python backoff (teaches the concept) ───────────────────
    print("--- Demo 1: Manual Exponential Backoff (conceptual) ---")
    print("API will fail 2 times before succeeding on attempt 3:\n")
    _call_count = 0
    result = retry_with_backoff(lambda: flaky_api_call(succeed_on_attempt=3))
    print(f"\nFinal result: {result}")

    # ── Demo 2-4: LangGraph Runnable patterns ────────────────────────────────
    demo_with_retry()
    demo_with_fallbacks()
    demo_combined()

    # ── Backoff schedule ─────────────────────────────────────────────────────
    print("\n--- Exponential Backoff Schedule ---")
    print("  Attempt 1: fail → wait 2s")
    print("  Attempt 2: fail → wait 4s")
    print("  Attempt 3: fail → wait 8s")
    print("  With jitter: wait(n) = 2^n * random(0.5, 1.5)  ← prevents thundering herd")

    print("\n--- .with_retry() vs tenacity @retry ---")
    print("  Old: @retry(retry_if_exception_type(anthropic.RateLimitError), stop_after_attempt(4))")
    print("  New: llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)")
    print("       Works on any Runnable: LLMs, chains, retrievers, ToolNode")

    print("\n--- When NOT to Retry ---")
    print("  400 Bad Request → your input is wrong, retrying won't help")
    print("  401 Unauthorized → wrong API key, retrying won't help")
    print("  404 Not Found → resource doesn't exist")
    print("  DO retry: 429 Rate Limit, 500/503 Server Error, network timeouts")
