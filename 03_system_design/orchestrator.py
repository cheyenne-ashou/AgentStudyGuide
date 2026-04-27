"""
Orchestrator Pattern
Central brain that routes tasks to specialized sub-agents and aggregates results.

The orchestrator doesn't do the work — it decides WHO does the work.
Each sub-agent is specialized (researcher, calculator, writer).
The orchestrator coordinates them and synthesizes a final response.

Architecture:
  User → Orchestrator → [SubAgent1, SubAgent2, SubAgent3] → Aggregate → Response

Run: python 03_system_design/orchestrator.py
"""
import sys
import time
from pathlib import Path
from typing import Callable, Any

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, MODEL, FAST_MODEL, cached_system
from core.logger import get_logger

log = get_logger(__name__)


class AgentResult:
    def __init__(self, agent_name: str, result: Any, duration_ms: float):
        self.agent_name = agent_name
        self.result = result
        self.duration_ms = duration_ms
        self.success = not isinstance(result, Exception)

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"AgentResult({self.agent_name}, {status}, {self.duration_ms:.0f}ms)"


AgentFn = Callable[[str], str]


class Orchestrator:
    """
    Routes tasks to registered sub-agents.
    Each agent is a function: (task: str) -> str
    """

    def __init__(self):
        self._agents: dict[str, tuple[AgentFn, str]] = {}
        self._client = get_client()

    def register(self, name: str, fn: AgentFn, description: str = "") -> "Orchestrator":
        self._agents[name] = (fn, description)
        log.info("orchestrator.register", agent=name)
        return self

    def run_agent(self, name: str, task: str) -> AgentResult:
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not registered. Available: {list(self._agents)}")
        fn, _ = self._agents[name]
        start = time.perf_counter()
        try:
            result = fn(task)
            return AgentResult(name, result, (time.perf_counter() - start) * 1000)
        except Exception as e:
            log.error("orchestrator.agent_error", agent=name, error=str(e))
            return AgentResult(name, e, (time.perf_counter() - start) * 1000)

    def route(self, user_request: str) -> str:
        """
        Use the LLM to decide which agent(s) to invoke, then aggregate.
        In production this could be a classifier or embedding-based router.
        """
        agent_descriptions = "\n".join(
            f"- {name}: {desc}" for name, (_, desc) in self._agents.items()
        )
        routing_prompt = (
            f"Available agents:\n{agent_descriptions}\n\n"
            f"User request: {user_request}\n\n"
            "Which agent(s) should handle this? Reply with a comma-separated list of agent names only. "
            "Example: researcher,calculator"
        )
        response = self._client.messages.create(
            model=FAST_MODEL,
            max_tokens=50,
            messages=[{"role": "user", "content": routing_prompt}],
        )
        selected = [s.strip() for s in response.content[0].text.strip().split(",")]
        selected = [s for s in selected if s in self._agents]

        log.info("orchestrator.route", selected=selected, request=user_request[:60])
        print(f"\n  [Orchestrator] Routing to: {selected}")

        results = [self.run_agent(name, user_request) for name in selected]

        # Aggregate results
        if len(results) == 1:
            return str(results[0].result)

        parts = [f"[{r.agent_name}]: {r.result}" for r in results if r.success]
        synthesis_prompt = (
            f"Original request: {user_request}\n\n"
            f"Results from specialized agents:\n" + "\n\n".join(parts) +
            "\n\nSynthesize these results into a single coherent response."
        )
        synthesis = self._client.messages.create(
            model=FAST_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": synthesis_prompt}],
        )
        return synthesis.content[0].text.strip()

    def describe(self) -> None:
        print(f"Orchestrator with {len(self._agents)} agents:")
        for name, (_, desc) in self._agents.items():
            print(f"  {name:<20} {desc}")


# ── Specialist agents ────────────────────────��────────────────────────────────

def make_researcher(client) -> AgentFn:
    def researcher(task: str) -> str:
        response = client.messages.create(
            model=FAST_MODEL,
            max_tokens=300,
            system=cached_system("You are a research agent. Provide factual, concise information."),
            messages=[{"role": "user", "content": f"Research task: {task}"}],
        )
        return response.content[0].text.strip()
    return researcher


def make_calculator(_) -> AgentFn:
    import math
    def calculator(task: str) -> str:
        # For demo: extract and evaluate any numbers in the task
        import re
        numbers = re.findall(r"\d+(?:\.\d+)?", task)
        if len(numbers) >= 2:
            a, b = float(numbers[0]), float(numbers[1])
            return f"Calculation result: {a} * {b} = {a * b}"
        return "No calculation needed."
    return calculator


def make_summarizer(client) -> AgentFn:
    def summarizer(task: str) -> str:
        response = client.messages.create(
            model=FAST_MODEL,
            max_tokens=200,
            system="You are a summarizer. Be extremely concise.",
            messages=[{"role": "user", "content": f"Summarize this in 2 sentences: {task}"}],
        )
        return response.content[0].text.strip()
    return summarizer


if __name__ == "__main__":
    print("=== ORCHESTRATOR DEMO ===\n")
    client = get_client()

    orchestrator = Orchestrator()
    orchestrator.register("researcher", make_researcher(client), "Researches facts and provides information")
    orchestrator.register("calculator", make_calculator(client), "Performs mathematical calculations")
    orchestrator.register("summarizer", make_summarizer(client), "Summarizes long text into key points")

    orchestrator.describe()
    print()

    tasks = [
        "What is RAG and how does it work?",
        "Calculate: if I invest $10,000 at 7% annual return for 20 years, what do I get?",
        "Research and summarize the main differences between LangChain and LlamaIndex.",
    ]

    for task in tasks:
        print(f"\n{'='*60}")
        print(f"Request: {task}")
        result = orchestrator.route(task)
        print(f"\nResult: {result[:300]}")

    print("\n--- Design Patterns Shown ---")
    print("  1. Single responsibility: each agent does one thing well")
    print("  2. LLM-based routing: model decides which specialist to use")
    print("  3. Result aggregation: synthesize multi-agent outputs")
    print("  4. Centralized logging: every routing decision is traced")
