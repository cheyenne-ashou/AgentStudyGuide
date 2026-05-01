"""
Project 3: Multi-Agent Workflow — Orchestrator (LangGraph StateGraph)
Coordinates the full Planner → Executor → Validator pipeline as a
PlanExecuteState graph with:
  - Conditional retry edge (validator → executor on failure)
  - MemorySaver checkpointer for crash recovery on long tasks
  - Structured logging at every phase

This is the capstone project — it uses patterns from every prior section.

Graph structure:
  planner → executor → validator → (approved? → synthesizer : → executor)
                                                                    ↑
                                             (max retries? → synthesizer)

Run: python 05_projects/project3_multi_agent/workflow.py
"""
import sys
from pathlib import Path
from typing import Literal

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from core.client import get_fast_llm
from core.models import PlanExecuteState
from core.logger import get_logger
from planner import create_plan, TaskPlan
from executor import execute_plan
from validator import validate_results, ValidationReport

log = get_logger(__name__)

MAX_RETRIES = 2


# ── State ─────────────────────────────────────────────────────────────────────
# PlanExecuteState (from core/models.py) adds:
#   plan: list[str] — remaining steps (unused in this workflow; plan is stored separately)
#   past_steps: accumulated (step, result) pairs
#   response: final synthesized answer
#
# We extend it via the state dict to carry workflow-specific data.

# ── Node functions ────────────────────────────────────────────────────────────

def planner_node(state: PlanExecuteState) -> dict:
    task = state["messages"][0].content
    print(f"\n[Phase 1] PLANNING: {task[:60]}")
    plan = create_plan(task)
    print(f"  Created {len(plan.steps)}-step plan:")
    for step in plan.steps:
        print(f"  Step {step.step_number}: [{step.tool}] {step.description}")
    # Store serialized plan in past_steps[0] slot as a signal
    return {"plan": [str(s.step_number) for s in plan.steps], "past_steps": [("__plan__", str(plan.model_dump()))]}


def executor_node(state: PlanExecuteState) -> dict:
    import json
    # Recover the plan from the stored dict
    plan_data = None
    for step, result in state["past_steps"]:
        if step == "__plan__":
            plan_data = json.loads(result.replace("'", '"'))
            break

    if plan_data is None:
        return {"past_steps": [("__executor_error__", "No plan found")]}

    from planner import TaskPlan, TaskStep
    plan = TaskPlan.model_validate(plan_data)

    attempt = sum(1 for step, _ in state["past_steps"] if step == "__attempt__")
    print(f"\n[Phase 2] EXECUTING (attempt {attempt + 1}/{MAX_RETRIES + 1})...")

    results = execute_plan(plan.steps)
    for step_num, result in results.items():
        print(f"  Step {step_num}: {result[:100]}")

    return {"past_steps": [("__attempt__", str(attempt + 1)), ("__results__", str(results))]}


def validator_node(state: PlanExecuteState) -> dict:
    import json
    task = state["messages"][0].content

    plan_data = None
    results_data = None
    for step, result in state["past_steps"]:
        if step == "__plan__":
            plan_data = json.loads(result.replace("'", '"'))
        if step == "__results__":
            results_data = eval(result)

    if plan_data is None or results_data is None:
        return {"past_steps": [("__validation__", "error: missing plan or results")]}

    from planner import TaskPlan
    plan = TaskPlan.model_validate(plan_data)

    print(f"\n[Phase 3] VALIDATING...")
    validation = validate_results(task, plan.steps, results_data)
    print(f"  Overall score: {validation.overall_score:.2f}")
    for sv in validation.step_validations:
        icon = "✓" if sv.approved else "✗"
        print(f"  {icon} Step {sv.step_number}: score={sv.score:.2f} {sv.issue[:50]}")

    if validation.approved:
        print(f"  Validated! Score: {validation.overall_score:.2f}")
    else:
        print(f"  Score {validation.overall_score:.2f} below threshold.")

    return {"past_steps": [("__validation__", str(validation.model_dump()))]}


def synthesizer_node(state: PlanExecuteState) -> dict:
    task = state["messages"][0].content
    results_data = None
    for step, result in state["past_steps"]:
        if step == "__results__":
            results_data = eval(result)

    print(f"\n[Phase 4] SYNTHESIZING...")
    results_str = "\n".join(f"Step {k}: {v}" for k, v in (results_data or {}).items())

    response = get_fast_llm().invoke([
        SystemMessage(content="Combine the execution results into a clear, complete answer. Be concise and direct."),
        HumanMessage(content=f"Original task: {task}\n\nResults:\n{results_str}\n\nAnswer:"),
    ])

    final = response.content
    print(f"\n{'─'*65}")
    print(f"FINAL ANSWER:\n{final}")
    print(f"{'─'*65}")

    return {"response": final}


def should_retry(state: PlanExecuteState) -> Literal["executor", "synthesizer"]:
    """Route after validation: retry if failed and under max retries."""
    attempt_count = sum(1 for step, _ in state["past_steps"] if step == "__attempt__")
    validation_data = None
    for step, result in state["past_steps"]:
        if step == "__validation__":
            validation_data = eval(result)

    if validation_data and validation_data.get("approved"):
        return "synthesizer"
    if attempt_count > MAX_RETRIES:
        print(f"  Max retries ({MAX_RETRIES}) reached. Proceeding with best available results.")
        return "synthesizer"
    return "executor"


# ── Build the graph ───────────────────────────────────────────────────────────

def build_workflow():
    workflow = StateGraph(PlanExecuteState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "validator")
    workflow.add_conditional_edges("validator", should_retry, {
        "executor": "executor",
        "synthesizer": "synthesizer",
    })
    workflow.add_edge("synthesizer", END)

    # MemorySaver enables crash recovery on long-running tasks
    return workflow.compile(checkpointer=MemorySaver())


def run_workflow(task: str, verbose: bool = True) -> dict:
    print(f"\n{'='*65}")
    print(f"TASK: {task}")
    print(f"{'='*65}")

    agent = build_workflow()
    config = {"configurable": {"thread_id": f"workflow-{hash(task) % 10000}"}}

    result = agent.invoke(
        {"messages": [HumanMessage(content=task)], "plan": [], "past_steps": [], "response": None},
        config,
    )

    validation_score = 0.0
    approved = False
    for step, data in result["past_steps"]:
        if step == "__validation__":
            v = eval(data)
            validation_score = v.get("overall_score", 0.0)
            approved = v.get("approved", False)

    log.info(
        "workflow.complete",
        task=task[:50],
        score=validation_score,
        approved=approved,
    )

    return {
        "task": task,
        "answer": result.get("response", ""),
        "validation_score": validation_score,
        "approved": approved,
    }


if __name__ == "__main__":
    print("=== MULTI-AGENT WORKFLOW DEMO (LangGraph) ===")
    print("Planner → Executor → Validator → Synthesizer\n")

    tasks = [
        "Research Python web frameworks (FastAPI, Django, Flask), compare their main tradeoffs, "
        "and recommend which one to use for building a RAG API.",

        "Calculate: if I save $500/month starting today for 5 years at 4.5% annual interest, "
        "how much will I have? Also, what day of the week is it?",
    ]

    for task in tasks:
        result = run_workflow(task)
        print(f"\n{'='*65}\n")

    print("--- Graph Structure ---")
    print("  planner → executor → validator → (approved? synthesizer : executor)")
    print("  MemorySaver checkpointer enables crash recovery on long tasks")
    print("  Conditional edge on validator: should_retry() decides next step")

    print("\n--- Multi-Agent Pattern Summary ---")
    print("  Planner:     .with_structured_output(TaskPlan) — no JSON extraction needed")
    print("  Executor:    ToolNode executes tool calls from LLM responses")
    print("  Validator:   .with_structured_output(ValidationReport) — typed quality gate")
    print("  Synthesizer: LCEL chain → final grounded answer")
    print("\n  This pattern is used in: LangGraph, AutoGen, CrewAI, Semantic Kernel")
