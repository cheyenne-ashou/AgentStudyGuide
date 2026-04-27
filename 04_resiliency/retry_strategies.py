"""
Retry Strategies with Exponential Backoff
Uses `tenacity` for retrying failed LLM/tool calls.

Three patterns:
  1. Simple retry — retry N times on any error
  2. Exponential backoff — wait longer between each retry
  3. Model fallback — if primary model fails repeatedly, use a backup

In agentic systems, you MUST have retries. External APIs fail.
LLMs return rate limit errors. Networks are unreliable.
The question is: how long do you wait before giving up?

Run: python 04_resiliency/retry_strategies.py
"""
import sys
import time
import random
from pathlib import Path
from typing import Callable, Any

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

import anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)
from core.client import get_client, MODEL, FAST_MODEL
from core.logger import get_logger

log = get_logger(__name__)


# ── 1. Simple exponential backoff decorator ───────────────────────────────────

@retry(
    retry=retry_if_exception_type(anthropic.RateLimitError),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(log, "warning"),  # type: ignore
)
def llm_call_with_backoff(messages: list[dict], model: str = MODEL, max_tokens: int = 200) -> str:
    """Any RateLimitError will be retried with exponential backoff."""
    client = get_client()
    response = client.messages.create(model=model, max_tokens=max_tokens, messages=messages)
    return response.content[0].text.strip()


# ── 2. Jittered backoff (better for distributed systems) ─────────────────────

@retry(
    retry=retry_if_exception_type(anthropic.RateLimitError),
    stop=stop_after_attempt(4),
    wait=wait_random_exponential(multiplier=1, min=1, max=20),  # adds jitter
)
def llm_call_with_jitter(messages: list[dict], model: str = MODEL) -> str:
    """Jittered backoff prevents thundering herd when many clients retry simultaneously."""
    client = get_client()
    response = client.messages.create(model=model, max_tokens=200, messages=messages)
    return response.content[0].text.strip()


# ── 3. Model fallback chain ───────────────────────────────────────────────────

class ModelFallbackChain:
    """
    Try models in order. On failure, move to next.
    Useful for: cost optimization (use cheap model when expensive one fails),
    or resilience (keep serving even if one model is down).
    """

    def __init__(self, models: list[str]):
        self._models = models
        self._client = get_client()

    def complete(self, messages: list[dict], max_tokens: int = 200) -> tuple[str, str]:
        """Returns (text, model_used)."""
        last_error = None
        for model in self._models:
            try:
                response = self._client.messages.create(
                    model=model, max_tokens=max_tokens, messages=messages
                )
                return response.content[0].text.strip(), model
            except anthropic.RateLimitError as e:
                log.warning("fallback.rate_limit", model=model)
                last_error = e
                time.sleep(1)
            except anthropic.APIStatusError as e:
                log.warning("fallback.api_error", model=model, status=e.status_code)
                last_error = e
        raise RuntimeError(f"All models failed. Last: {last_error}")


# ── 4. Simulated failure for demo ─────────────────────────────────────────────

_call_count = 0

def flaky_api_call(succeed_on_attempt: int = 3) -> str:
    """Simulates a flaky external API that fails the first N-1 times."""
    global _call_count
    _call_count += 1
    print(f"  [Attempt {_call_count}]", end=" ")
    if _call_count < succeed_on_attempt:
        print(f"FAIL (simulated)")
        raise ConnectionError(f"Simulated API failure on attempt {_call_count}")
    print(f"SUCCESS")
    return "API response: data successfully retrieved"


@retry(
    retry=retry_if_exception_type(ConnectionError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.5, min=0.1, max=2),
)
def resilient_api_call() -> str:
    return flaky_api_call(succeed_on_attempt=3)


if __name__ == "__main__":
    print("=== RETRY STRATEGIES DEMO ===\n")

    # ── Demo 1: Simulated flaky API ──────────────────────────────────────────
    print("--- Demo 1: Exponential Backoff on Flaky API ---")
    print("API will fail 2 times before succeeding on attempt 3:\n")
    _call_count = 0
    try:
        result = resilient_api_call()
        print(f"\nFinal result: {result}")
    except RetryError:
        print("\nAll retries exhausted!")

    # ── Demo 2: Model fallback chain ─────────────────────────────────────────
    print("\n--- Demo 2: Model Fallback Chain ---")
    chain = ModelFallbackChain(models=[MODEL, FAST_MODEL])
    print(f"Chain: {' → '.join(chain._models)}")

    text, used_model = chain.complete(
        messages=[{"role": "user", "content": "In one sentence: what is exponential backoff?"}]
    )
    print(f"Used model: {used_model}")
    print(f"Response: {text}")

    # ── Demo 3: Real LLM call with backoff ───────────────────────────────────
    print("\n--- Demo 3: Real LLM Call with Backoff ---")
    result = llm_call_with_backoff(
        messages=[{"role": "user", "content": "In one sentence: when should you NOT retry a failed call?"}]
    )
    print(f"Response: {result}")

    # ── Backoff schedule ─────────────────────────────────────────────────────
    print("\n--- Exponential Backoff Schedule ---")
    print("  Attempt 1: fail → wait 2s")
    print("  Attempt 2: fail → wait 4s")
    print("  Attempt 3: fail → wait 8s")
    print("  Attempt 4: fail → wait 16s (capped at max)")
    print("  With jitter: wait(n) = 2^n * random(0.5, 1.5)  ← prevents thundering herd")

    print("\n--- When NOT to Retry ---")
    print("  400 Bad Request → your input is wrong, retrying won't help")
    print("  401 Unauthorized → wrong API key, retrying won't help")
    print("  404 Not Found → resource doesn't exist")
    print("  DO retry: 429 Rate Limit, 500/503 Server Error, network timeouts")
