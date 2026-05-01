"""
LLM Gateway Pattern (LangGraph)
Unified interface for LLM calls using LangChain's composable Runnable methods:
  - .with_retry()     — retry on transient errors with exponential backoff
  - .with_fallbacks() — try a backup model if the primary fails
  - Combined          — retry primary, then fall back, all in one chain

Why a gateway?
  - Decouples agent code from specific model names
  - Easy to swap providers in one place
  - Central place to add auth, rate limiting, caching, monitoring
  - Model fallback makes the system resilient to individual model outages

LangGraph concept: .with_retry() and .with_fallbacks() are composable Runnable
methods that wrap any Runnable — LLMs, chains, retrievers, tool nodes.
They replace the tenacity @retry decorator pattern entirely.

Run: python 03_system_design/llm_gateway.py
"""
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from core.client import get_llm, get_fast_llm, MODEL, FAST_MODEL
from core.logger import get_logger

log = get_logger(__name__)


# ── Gateway statistics (observability still requires instrumentation) ─────────

@dataclass
class GatewayStats:
    total_calls: int = 0
    total_latency_ms: float = 0.0
    fallback_count: int = 0
    error_count: int = 0

    def avg_latency(self) -> float:
        return self.total_latency_ms / self.total_calls if self.total_calls else 0.0

    def report(self) -> str:
        return (
            f"Calls: {self.total_calls}  |  "
            f"Fallbacks: {self.fallback_count}  |  "
            f"Errors: {self.error_count}  |  "
            f"Avg latency: {self.avg_latency():.0f}ms"
        )


class LLMGateway:
    """
    Unified LLM interface built on LangChain Runnable composition.

    Patterns used:
      .with_retry()      — retry on any exception with jittered exponential backoff
      .with_fallbacks()  — on exhausted retries, try the next model in chain
    """

    def __init__(self):
        primary = get_llm()
        fallback = get_fast_llm()

        # Pattern 1: retry primary before giving up
        self._llm_with_retry: Runnable = primary.with_retry(
            stop_after_attempt=3,
            wait_exponential_jitter=True,
        )

        # Pattern 2: combined retry + fallback — the recommended production pattern
        # Retry primary 3×, then fall back to fast model (also retried 3×)
        self._resilient_llm: Runnable = (
            primary
            .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
            .with_fallbacks(
                [fallback.with_retry(stop_after_attempt=2)],
                exceptions_to_handle=(Exception,),
            )
        )

        self._stats = GatewayStats()

    def complete(self, prompt: str) -> str:
        """Complete a prompt using the resilient LLM chain."""
        self._stats.total_calls += 1
        start = time.perf_counter()
        try:
            response = self._resilient_llm.invoke([HumanMessage(content=prompt)])
            latency_ms = (time.perf_counter() - start) * 1000
            self._stats.total_latency_ms += latency_ms
            log.info("gateway.complete", latency_ms=round(latency_ms))
            return response.content
        except Exception as e:
            self._stats.error_count += 1
            log.error("gateway.error", error=str(e)[:100])
            raise

    @property
    def stats(self) -> GatewayStats:
        return self._stats


# ── Standalone pattern demos ──────────────────────────────────────────────────

def demo_retry_pattern() -> None:
    """Show .with_retry() — retry on transient errors."""
    print("--- Pattern 1: .with_retry() ---")
    llm = get_fast_llm().with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,  # adds jitter to prevent thundering herd
    )
    result = llm.invoke([HumanMessage(content="In one sentence: what is exponential backoff?")])
    print(f"  Response: {result.content[:150]}")
    print("  If a transient error occurs, the call is retried up to 3× automatically.")


def demo_fallback_pattern() -> None:
    """Show .with_fallbacks() — backup model on failure."""
    print("\n--- Pattern 2: .with_fallbacks() ---")
    primary = get_llm()
    backup = get_fast_llm()
    llm_with_fallback = primary.with_fallbacks(
        [backup],
        exceptions_to_handle=(Exception,),
    )
    result = llm_with_fallback.invoke([HumanMessage(content="In one sentence: what is a model fallback chain?")])
    print(f"  Response: {result.content[:150]}")
    print(f"  Fallback chain: {MODEL} → {FAST_MODEL}")


def demo_combined_pattern() -> None:
    """Show the recommended production combination."""
    print("\n--- Pattern 3: Combined retry + fallback ---")
    resilient = (
        get_llm()
        .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
        .with_fallbacks([get_fast_llm().with_retry(stop_after_attempt=2)])
    )
    result = resilient.invoke([HumanMessage(content="Why should you use a model fallback in production?")])
    print(f"  Response: {result.content[:200]}")
    print("  Behavior: retry primary 3×, then retry fallback 2×, then raise")


if __name__ == "__main__":
    print("=== LLM GATEWAY DEMO (LangGraph Runnables) ===\n")

    demo_retry_pattern()
    demo_fallback_pattern()
    demo_combined_pattern()

    # Full gateway demo
    print("\n--- Gateway: full observability wrapper ---")
    gateway = LLMGateway()
    queries = [
        "What is the ReAct prompting pattern?",
        "Name 3 benefits of a tool abstraction layer in agentic systems.",
        "What is the difference between stateless and stateful agents?",
    ]
    for query in queries:
        response = gateway.complete(query)
        print(f"\nQ: {query}")
        print(f"A: {response[:200]}")

    print("\n--- Gateway Statistics ---")
    print(f"  {gateway.stats.report()}")

    print("\n--- .with_retry() vs old tenacity pattern ---")
    print("  Old: @retry(retry_if_exception_type(anthropic.RateLimitError), stop_after_attempt(4), ...)")
    print("  New: llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)")
    print("       Works on any Runnable: LLMs, chains, retrievers, tool nodes")

    print("\n--- Why Use a Gateway? ---")
    benefits = [
        "Swap models in one place — agents never reference model names directly",
        "Automatic fallback — system stays up when primary model has issues",
        ".with_retry() / .with_fallbacks() compose on any Runnable",
        "Central place to add auth, rate limiting, caching, monitoring",
        "Usage tracking — add instrumentation around the resilient chain",
    ]
    for b in benefits:
        print(f"  • {b}")
