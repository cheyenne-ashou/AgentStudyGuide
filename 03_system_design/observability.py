"""
Observability for Agentic Systems
Implements structured tracing: every agent step emits a span with timing,
inputs, outputs, and parent context.

Without observability you can't answer:
  - Why did the agent fail on this task?
  - Which tool is the bottleneck?
  - How many tokens did this workflow consume?
  - Did the agent loop infinitely?

Run: python 03_system_design/observability.py
"""
import sys
import time
import uuid
import json
from contextlib import contextmanager
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Generator

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.logger import get_logger

log = get_logger(__name__)


@dataclass
class Span:
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: str | None = None
    name: str = ""
    start_time: float = field(default_factory=time.perf_counter)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"  # ok | error

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return (time.perf_counter() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.perf_counter()
        self.status = status

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            **self.attributes,
        }


class Tracer:
    """
    Collects spans for an agent execution.
    In production this would send to OpenTelemetry, Langfuse, or similar.
    """

    def __init__(self, trace_id: str | None = None):
        self.trace_id = trace_id or str(uuid.uuid4())[:12]
        self._spans: list[Span] = []
        self._active: Span | None = None

    @contextmanager
    def span(self, name: str, **attributes) -> Generator[Span, None, None]:
        """Context manager that creates a span, times it, and logs on exit."""
        s = Span(
            name=name,
            parent_id=self._active.span_id if self._active else None,
            attributes=attributes,
        )
        prev = self._active
        self._active = s
        self._spans.append(s)

        log.info("span.start", trace=self.trace_id, span=s.span_id, name=name)
        try:
            yield s
            s.finish("ok")
        except Exception as e:
            s.finish("error")
            s.attributes["error"] = str(e)
            raise
        finally:
            self._active = prev
            log.info(
                "span.end",
                trace=self.trace_id,
                span=s.span_id,
                name=name,
                duration_ms=round(s.duration_ms),
                status=s.status,
            )

    def summary(self) -> dict:
        total_ms = sum(s.duration_ms for s in self._spans if s.parent_id is None)
        errors = [s.name for s in self._spans if s.status == "error"]
        return {
            "trace_id": self.trace_id,
            "total_spans": len(self._spans),
            "total_ms": round(total_ms, 2),
            "error_count": len(errors),
            "errors": errors,
            "spans": [s.to_dict() for s in self._spans],
        }

    def print_tree(self) -> None:
        """Print a human-readable span tree."""
        print(f"\nTrace: {self.trace_id}")
        for span in self._spans:
            indent = "  " if span.parent_id else ""
            status_icon = "✓" if span.status == "ok" else "✗"
            attrs = ""
            if span.attributes:
                attrs = "  " + " ".join(f"{k}={v}" for k, v in span.attributes.items() if k != "error")
            print(f"  {indent}{status_icon} {span.name:<30} {span.duration_ms:>7.1f}ms{attrs}")


def simulate_agent_run(tracer: Tracer) -> str:
    """Simulate a multi-step agent run with tracing."""

    with tracer.span("agent.run", query="Calculate revenue and find today's date"):

        with tracer.span("memory.retrieve", top_k=3) as s:
            time.sleep(0.015)
            s.attributes["memories_found"] = 3

        with tracer.span("llm.plan", model="claude-sonnet-4-6") as s:
            time.sleep(0.08)
            s.attributes["tokens_in"] = 142
            s.attributes["tokens_out"] = 89

        with tracer.span("tool.calculator", expression="1250000 * 1.136") as s:
            time.sleep(0.002)
            s.attributes["result"] = "1420000.0"

        with tracer.span("tool.get_datetime") as s:
            time.sleep(0.001)
            s.attributes["result"] = "Friday"

        with tracer.span("llm.synthesize", model="claude-sonnet-4-6") as s:
            time.sleep(0.06)
            s.attributes["tokens_in"] = 210
            s.attributes["tokens_out"] = 95

        with tracer.span("memory.store", key="session:last_result") as s:
            time.sleep(0.005)

    return "Revenue is $1.42M (13.6% growth). Today is Friday."


if __name__ == "__main__":
    print("=== OBSERVABILITY DEMO ===\n")

    tracer = Tracer()
    result = simulate_agent_run(tracer)

    print(f"\nAgent Result: {result}")
    tracer.print_tree()

    summary = tracer.summary()
    print(f"\n--- Summary ---")
    print(f"  Trace ID:    {summary['trace_id']}")
    print(f"  Spans:       {summary['total_spans']}")
    print(f"  Total time:  {summary['total_ms']}ms")
    print(f"  Errors:      {summary['error_count']}")

    # Show which spans were slowest
    spans_by_time = sorted(summary["spans"], key=lambda s: s["duration_ms"], reverse=True)
    print("\n--- Slowest Spans ---")
    for span in spans_by_time[:3]:
        print(f"  {span['name']:<30} {span['duration_ms']}ms")

    print("\n--- Interview Answer: 'How do you debug an agent?' ---")
    print("  1. Check span tree — which step is slowest / erroring?")
    print("  2. Check token counts — is a prompt ballooning unexpectedly?")
    print("  3. Check loop count — did the agent loop without progress?")
    print("  4. Check tool call inputs/outputs — is the agent calling tools correctly?")
    print("  5. Check memory retrieval — is relevant context being found?")
    print("  Tooling: Langfuse, OpenTelemetry + Jaeger, Arize Phoenix")
