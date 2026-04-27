"""
Plan-and-Execute Agent
Two-phase approach:
  Phase 1 (Plan): Ask Claude to produce a structured step-by-step plan
  Phase 2 (Execute): Run each step in order, passing results forward

Why use this instead of pure ReAct?
  - Better for complex, long-horizon tasks (more than ~5 steps)
  - Allows human review of the plan before execution
  - Easier to parallelize independent steps
  - Makes the agent's strategy visible and debuggable
  - Tradeoff: inflexible — can't adapt if mid-execution conditions change

Run: python 02_agentic_core/patterns/plan_and_execute.py
"""
import sys
import json
import math
from pathlib import Path
from datetime import datetime, timezone

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, MODEL, cached_system
from pydantic import BaseModel


class Step(BaseModel):
    step_number: int
    description: str
    tool: str | None = None
    depends_on: list[int] = []


class Plan(BaseModel):
    task: str
    steps: list[Step]
    estimated_steps: int


TOOLS_AVAILABLE = ["calculator", "web_search", "get_datetime", "none (answer directly)"]


def phase1_plan(task: str, client) -> Plan:
    """Ask Claude to make a structured plan."""
    system = cached_system(
        "You are a planning agent. When given a task, produce a JSON execution plan. "
        "Be specific about which tool each step uses. "
        f"Available tools: {', '.join(TOOLS_AVAILABLE)}"
    )
    schema = {
        "task": "string",
        "steps": [{"step_number": "int", "description": "string", "tool": "string|null", "depends_on": "[int]"}],
        "estimated_steps": "int"
    }
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Task: {task}\n\nProduce a JSON plan following this schema:\n{json.dumps(schema, indent=2)}"
        }],
    )
    text = response.content[0].text.strip()
    # Extract JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1:
        raise ValueError(f"No JSON found in response: {text[:200]}")
    return Plan.model_validate_json(text[start:end])


def execute_tool(tool: str, description: str, context: dict, client) -> str:
    """Execute a single step, using LLM to derive tool inputs from the step description."""
    if tool == "none (answer directly)" or tool is None:
        response = client.messages.create(
            model=MODEL,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": f"Step: {description}\n\nContext from previous steps:\n{json.dumps(context, indent=2)}\n\nAnswer this step directly."
            }],
        )
        return response.content[0].text.strip()

    if tool == "calculator":
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"Step: {description}\n\nContext: {json.dumps(context)}\n\nExtract the math expression to evaluate. Reply with ONLY the expression, nothing else."
            }],
        )
        expr = response.content[0].text.strip().strip("`")
        try:
            result = eval(expr, {"__builtins__": {}}, vars(math))
            return f"{expr} = {result}"
        except Exception as e:
            return f"Calculator error on '{expr}': {e}"

    elif tool == "get_datetime":
        return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M UTC")

    elif tool == "web_search":
        return f"[MOCK] Search results for '{description[:50]}': relevant information found"

    return f"Unknown tool: {tool}"


def phase2_execute(plan: Plan, client) -> list[dict]:
    """Execute each step in order, accumulating results."""
    results = {}

    print(f"\nExecuting {len(plan.steps)}-step plan...")
    print("─" * 50)

    for step in plan.steps:
        print(f"\n[Step {step.step_number}] {step.description}")
        print(f"  Tool: {step.tool or 'none'}")
        if step.depends_on:
            print(f"  Deps: {step.depends_on}")

        context = {f"step_{k}": v for k, v in results.items() if k in step.depends_on}
        result = execute_tool(step.tool or "none", step.description, context, client)
        results[step.step_number] = result
        print(f"  Result: {result[:100]}")

    return [{"step": k, "result": v} for k, v in results.items()]


if __name__ == "__main__":
    print("=== PLAN-AND-EXECUTE AGENT DEMO ===")
    client = get_client()

    task = (
        "I want to save $50,000 for a house down payment. "
        "Calculate how much I need to save per month over 3 years, "
        "and also what day of the week is today."
    )

    print(f"\nTask: {task}")
    print("\n=== PHASE 1: PLANNING ===")

    plan = phase1_plan(task, client)
    print(f"\nPlan produced: {len(plan.steps)} steps")
    for step in plan.steps:
        deps = f" [depends on steps {step.depends_on}]" if step.depends_on else ""
        print(f"  Step {step.step_number}: [{step.tool or 'direct'}] {step.description}{deps}")

    print("\n=== PHASE 2: EXECUTION ===")
    results = phase2_execute(plan, client)

    print("\n=== RESULTS SUMMARY ===")
    for r in results:
        print(f"  Step {r['step']}: {r['result'][:100]}")

    print("\n--- When to Use Plan-and-Execute ---")
    print("  ✓ Long-horizon tasks (>5 steps)")
    print("  ✓ Tasks where the plan can be reviewed before running")
    print("  ✓ Tasks with parallelizable steps (search + calculate in parallel)")
    print("  ✗ Tasks that need adaptive mid-execution course corrections")
    print("  ✗ Short tasks (overhead not worth it)")
