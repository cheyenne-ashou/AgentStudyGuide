"""
Project 3: Multi-Agent Workflow — Executor
Runs each step from the plan using the appropriate tool.
Returns results for each step, passing context forward via PlanExecuteState.
"""
import sys
import math
from pathlib import Path
from datetime import datetime, timezone

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from core.client import get_fast_llm
from core.logger import get_logger
from planner import TaskStep

log = get_logger(__name__)


# ── Tool definitions ──────────────────────────────────────────────────────────

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    safe = {"__builtins__": {}}
    ns = {k: v for k, v in vars(math).items() if not k.startswith("_")}
    try:
        result = eval(expression, safe, ns)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    mock_results = {
        "python": "Python 3.13 is latest. Popular for ML/AI, web, automation.",
        "fastapi": "FastAPI 0.115+ — async Python web framework, OpenAPI built-in.",
        "django": "Django 5.1 — batteries-included, ORM, admin panel.",
        "flask": "Flask 3.0 — lightweight, minimal, no ORM included.",
        "savings": "High-yield savings: 4.5-5.0% APY in 2024.",
        "compound interest": "A = P(1 + r/n)^(nt) where P=principal, r=rate, n=times/year, t=years",
    }
    query_lower = query.lower()
    for key, result in mock_results.items():
        if key in query_lower:
            return f"[Search: {query}] {result}"
    return f"[Search: {query}] Relevant information found. Key points: overview, recent updates, best practices."


@tool
def get_datetime() -> str:
    """Get the current UTC date and time."""
    return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M UTC")


TOOLS = [calculator, web_search, get_datetime]
tool_node = ToolNode(TOOLS)
llm_with_tools = get_fast_llm().bind_tools(TOOLS)
llm = get_fast_llm()


# ── Step execution ────────────────────────────────────────────────────────────

def execute_step(step: TaskStep, past_steps: list[tuple[str, str]]) -> str:
    """
    Execute a single plan step.
    Context from prior steps is passed via the past_steps list from PlanExecuteState.
    """
    context_str = "\n".join(f"Step {i+1} result: {r}" for i, (_, r) in enumerate(past_steps))
    context_str = context_str or "No prior context."

    if step.tool in ("none", None):
        # Answer directly from LLM
        response = llm.invoke([
            SystemMessage(content="Complete the following task step. Be concise."),
            HumanMessage(content=f"Step: {step.description}\n\nContext:\n{context_str}"),
        ])
        return response.content

    # Use the LLM to understand what to pass to the tool, then execute
    response = llm_with_tools.invoke([
        SystemMessage(content=f"Use the {step.tool} tool to complete this step."),
        HumanMessage(content=f"Step: {step.description}\n\nContext:\n{context_str}"),
    ])

    if response.tool_calls:
        tool_messages = tool_node.invoke([response])
        return tool_messages[0].content

    return response.content


def execute_plan(steps: list[TaskStep]) -> dict[int, str]:
    """Execute all steps in order, accumulating results."""
    results: dict[int, str] = {}
    past_steps: list[tuple[str, str]] = []

    for step in steps:
        result = execute_step(step, past_steps)
        results[step.step_number] = result
        past_steps.append((step.description, result))
        log.info("executor.step", step=step.step_number, tool=step.tool, result_preview=result[:60])

    return results
