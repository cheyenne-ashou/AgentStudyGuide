"""
Project 3: Multi-Agent Workflow — Executor
Runs each step from the plan using the appropriate tool.
Returns results for each step, passing context forward.
"""
import sys
import math
from pathlib import Path
from datetime import datetime, timezone

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, FAST_MODEL
from core.logger import get_logger
from planner import TaskStep

log = get_logger(__name__)


def _calculator(expression: str) -> str:
    safe = {"__builtins__": {}}
    ns = {k: v for k, v in vars(math).items() if not k.startswith("_")}
    try:
        result = eval(expression, safe, ns)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


def _web_search(query: str) -> str:
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


def execute_step(step: TaskStep, context: dict[int, str]) -> str:
    """
    Execute a single plan step.
    For tool steps: extract the operation from the step description using LLM.
    For 'none' steps: generate answer directly.
    """
    client = get_client()
    context_str = "\n".join(f"Step {k} result: {v}" for k, v in context.items()) if context else "No prior context."

    if step.tool == "calculator":
        # Ask LLM to extract the math expression from the step description
        expr_response = client.messages.create(
            model=FAST_MODEL,
            max_tokens=80,
            messages=[{
                "role": "user",
                "content": (
                    f"Step: {step.description}\n"
                    f"Context: {context_str}\n"
                    "Extract ONLY the math expression to evaluate. Reply with the expression only."
                ),
            }],
        )
        expr = expr_response.content[0].text.strip().strip("`")
        return _calculator(expr)

    elif step.tool == "web_search":
        # Extract search query from step description
        query_response = client.messages.create(
            model=FAST_MODEL,
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": (
                    f"Step: {step.description}\n"
                    "Extract the search query as a short phrase (5 words max). Reply with the query only."
                ),
            }],
        )
        query = query_response.content[0].text.strip().strip('"')
        return _web_search(query)

    elif step.tool == "get_datetime":
        return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M UTC")

    else:
        # Generate answer directly using LLM
        response = client.messages.create(
            model=FAST_MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    f"Task step: {step.description}\n\n"
                    f"Context from previous steps:\n{context_str}\n\n"
                    "Complete this step. Be concise."
                ),
            }],
        )
        return response.content[0].text.strip()


def execute_plan(steps: list[TaskStep]) -> dict[int, str]:
    """Execute all steps in order, accumulating results."""
    results: dict[int, str] = {}
    for step in steps:
        context = {k: v for k, v in results.items()}
        result = execute_step(step, context)
        results[step.step_number] = result
        log.info("executor.step", step=step.step_number, tool=step.tool, result_preview=result[:60])
    return results
