"""
LLM Gateway Pattern
Unified interface for LLM calls with:
  - Model fallback chain (if primary model fails, try next)
  - Request/response logging
  - Usage tracking (tokens consumed)
  - Configurable timeout

Why a gateway?
  - Decouples agent code from specific model names
  - Easy to swap providers (Anthropic → OpenAI) in one place
  - Central place to add auth, rate limiting, caching, monitoring
  - Model fallback makes the system resilient to individual model outages

Run: python 03_system_design/llm_gateway.py
"""
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.client import get_client, MODEL, FAST_MODEL
from core.logger import get_logger

log = get_logger(__name__)


@dataclass
class LLMResponse:
    text: str
    model_used: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    fallback_used: bool = False


@dataclass
class GatewayStats:
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    fallback_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0

    def avg_latency(self) -> float:
        return self.total_latency_ms / self.total_calls if self.total_calls else 0.0

    def report(self) -> str:
        return (
            f"Calls: {self.total_calls}  |  "
            f"Tokens in/out: {self.total_input_tokens}/{self.total_output_tokens}  |  "
            f"Fallbacks: {self.fallback_count}  |  "
            f"Errors: {self.error_count}  |  "
            f"Avg latency: {self.avg_latency():.0f}ms"
        )


class LLMGateway:
    """
    Unified LLM interface with fallback chain and observability.
    Primary model → fallback model 1 → fallback model 2 → raise
    """

    def __init__(self, models: list[str] | None = None):
        self._models = models or [MODEL, FAST_MODEL]
        self._client = get_client()
        self._stats = GatewayStats()

    @retry(
        retry=retry_if_exception_type(anthropic.RateLimitError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _call_model(self, model: str, messages: list[dict], system: str, max_tokens: int) -> anthropic.types.Message:
        return self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system if system else anthropic.NOT_GIVEN,
            messages=messages,
        )

    def complete(
        self,
        messages: list[dict],
        system: str = "",
        max_tokens: int = 512,
    ) -> LLMResponse:
        """
        Try each model in the fallback chain.
        Returns on first success.
        """
        self._stats.total_calls += 1
        last_error = None

        for i, model in enumerate(self._models):
            start = time.perf_counter()
            try:
                response = self._call_model(model, messages, system, max_tokens)
                latency_ms = (time.perf_counter() - start) * 1000

                text = next(b.text for b in response.content if b.type == "text")
                in_tok = response.usage.input_tokens
                out_tok = response.usage.output_tokens
                fallback_used = i > 0

                self._stats.total_input_tokens += in_tok
                self._stats.total_output_tokens += out_tok
                self._stats.total_latency_ms += latency_ms
                if fallback_used:
                    self._stats.fallback_count += 1

                log.info(
                    "gateway.complete",
                    model=model,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    latency_ms=round(latency_ms),
                    fallback=fallback_used,
                )

                return LLMResponse(
                    text=text,
                    model_used=model,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    latency_ms=latency_ms,
                    fallback_used=fallback_used,
                )

            except anthropic.RateLimitError:
                raise  # tenacity will retry this
            except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                last_error = e
                log.warning("gateway.model_failed", model=model, error=str(e)[:100])
                if i < len(self._models) - 1:
                    print(f"  [Gateway] {model} failed, trying fallback...")
                continue

        self._stats.error_count += 1
        raise RuntimeError(f"All models failed. Last error: {last_error}")

    @property
    def stats(self) -> GatewayStats:
        return self._stats


if __name__ == "__main__":
    print("=== LLM GATEWAY DEMO ===\n")

    # Normal operation
    gateway = LLMGateway(models=[MODEL, FAST_MODEL])
    print(f"Fallback chain: {' → '.join(gateway._models)}\n")

    queries = [
        "What is the ReAct prompting pattern?",
        "Name 3 benefits of a tool abstraction layer in agentic systems.",
        "What is the difference between stateless and stateful agents?",
    ]

    for query in queries:
        response = gateway.complete(
            messages=[{"role": "user", "content": query}],
            max_tokens=150,
        )
        print(f"Q: {query}")
        print(f"A: {response.text[:200]}")
        print(f"  [model={response.model_used}, tokens={response.input_tokens}+{response.output_tokens}]")
        print()

    print("--- Gateway Statistics ---")
    print(f"  {gateway.stats.report()}")

    print("\n--- Why Use a Gateway? ---")
    benefits = [
        "Swap models in one place — agents never reference model names directly",
        "Automatic fallback — system stays up when primary model has issues",
        "Usage tracking — know your token spend per feature",
        "Rate limit handling — retry logic centralized, not in every agent",
        "Auth management — API keys in one place",
        "A/B testing — route % of traffic to different models",
    ]
    for b in benefits:
        print(f"  • {b}")
