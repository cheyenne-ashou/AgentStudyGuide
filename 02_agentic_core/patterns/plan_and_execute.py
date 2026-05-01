"""
Plan-and-Execute Agent (LangGraph StateGraph)
Two-phase approach expressed as a multi-node graph:
  planner_node:   Ask LLM to produce a structured step-by-step plan
  executor_node:  Pop steps from the plan and execute them one by one
  responder_node: Combine all results into a final answer

Conditional edge: if plan is empty → respond; else → execute

Why use this instead of pure ReAct?
  - Better for complex, long-horizon tasks (more than ~5 steps)
  - Allows human review of the plan before execution
  - Easier to parallelize independent steps
  - Makes the agent's strategy visible and debuggable
  - Tradeoff: inflexible — can't adapt if mid-execution conditions change

LangGraph concept: PlanExecuteState uses operator.add on past_steps so
results accumulate across node invocations without overwriting.

Run: python 02_agentic_core/patterns/plan_and_execute.py
"""
import sys
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Literal

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from core.client import get_llm
from core.models import PlanExecuteState


# ── Pydantic models for structured planning ───────────────────────────────────

class Step(BaseModel):
    step_number: int
    description: str
    tool: str | None = None


class Plan(BaseModel):
    task: str
    steps: list[Step]


TOOLS_AVAILABLE = ["calculator", "web_search", "get_datetime", "none (answer directly)"]


# ── Tool definitions ──────────────────────────────────────────────────────────

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_datetime() -> str:
    """Get the current UTC date and time."""
    return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M UTC")


@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    return f"[MOCK] Search results for '{query[:50]}': relevant information found"


tools = [calculator, get_datetime, web_search]
llm = get_llm()
llm_with_tools = llm.bind_tools(tools)


# ── Node functions ────────────────────────────────────────────────────────────

def planner_node(state: PlanExecuteState) -> dict:
    """Phase 1: generate a structured plan with .with_structured_output()."""
    task = state["messages"][-1].content
    print(f"\n[Planner] Decomposing task: {task[:80]}")

    structured_llm = llm.with_structured_output(Plan)
    plan_obj: Plan = structured_llm.invoke([
        SystemMessage(content=(
            f"You are a planning agent. Decompose the task into sequential steps. "
            f"Available tools: {', '.join(TOOLS_AVAILABLE)}"
        )),
        HumanMessage(content=f"Task: {task}"),
    ])

    # Convert to list of plain strings for the state
    step_list = [f"[{s.tool or 'direct'}] {s.description}" for s in plan_obj.steps]
    print(f"  Plan ({len(step_list)} steps): {step_list}")
    return {"plan": step_list}


def executor_node(state: PlanExecuteState) -> dict:
    """Phase 2: pop one step from the plan and execute it."""
    current_step = state["plan"][0]
    remaining = state["plan"][1:]
    context = "\n".join(f"Previous: {r}" for r in state["past_steps"]) or "No prior context."

    print(f"\n[Executor] Running: {current_step}")

    response = llm_with_tools.invoke([
        SystemMessage(content="Execute the given step. Use tools if specified."),
        HumanMessage(content=f"Step: {current_step}\n\nContext:\n{context}"),
    ])

    # If the LLM called a tool, execute it
    if response.tool_calls:
        tool_node = ToolNode(tools)
        tool_messages = tool_node.invoke([response])
        result = tool_messages[0].content
    else:
        result = response.content

    print(f"  Result: {str(result)[:100]}")
    return {
        "plan": remaining,
        "past_steps": [(current_step, result)],
    }


def responder_node(state: PlanExecuteState) -> dict:
    """Phase 3: synthesize all step results into a final answer."""
    task = state["messages"][-1].content
    steps_summary = "\n".join(f"  {step}: {result}" for step, result in state["past_steps"])

    response = llm.invoke([
        SystemMessage(content="Combine the execution results into a clear, complete answer."),
        HumanMessage(content=f"Task: {task}\n\nResults:\n{steps_summary}\n\nAnswer:"),
    ])
    return {"response": response.content}


def route_after_plan(state: PlanExecuteState) -> Literal["execute", "respond"]:
    """Route to executor if steps remain, or responder if done."""
    return "execute" if state["plan"] else "respond"


# ── Build the graph ───────────────────────────────────────────────────────────

def build_plan_execute_graph():
    workflow = StateGraph(PlanExecuteState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("responder", responder_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_conditional_edges("executor", route_after_plan, {
        "execute": "executor",   # still steps remaining
        "respond": "responder",  # plan exhausted
    })
    workflow.add_edge("responder", END)
    return workflow.compile()


if __name__ == "__main__":
    print("=== PLAN-AND-EXECUTE AGENT DEMO (LangGraph) ===")

    task = (
        "I want to save $50,000 for a house down payment. "
        "Calculate how much I need to save per month over 3 years, "
        "and also what day of the week is today."
    )

    agent = build_plan_execute_graph()
    result = agent.invoke({"messages": [HumanMessage(content=task)], "plan": [], "past_steps": [], "response": None})

    print(f"\n{'='*60}")
    print(f"FINAL ANSWER:\n{result['response']}")

    print("\n--- Graph Structure ---")
    print("  planner → executor (loop until plan empty) → responder → END")
    print("  Conditional edge on executor: plan empty? → responder : → executor")

    print("\n--- PlanExecuteState keys ---")
    print("  messages:    incoming task + accumulated messages")
    print("  plan:        remaining steps (shrinks each executor invocation)")
    print("  past_steps:  completed (step, result) pairs (grows via operator.add)")
    print("  response:    final answer (set by responder)")

    print("\n--- When to Use Plan-and-Execute ---")
    print("  ✓ Long-horizon tasks (>5 steps)")
    print("  ✓ Tasks where the plan can be reviewed before running")
    print("  ✓ Tasks with parallelizable steps")
    print("  ✗ Tasks that need adaptive mid-execution course corrections")
    print("  ✗ Short tasks (overhead not worth it)")
