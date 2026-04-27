"""
Project 3: Multi-Agent Workflow — Orchestrator
Coordinates the full Planner → Executor → Validator pipeline with:
  - Observability (traced steps)
  - Retry on validation failure
  - Human escalation if repeated failures

This is the capstone project — it uses patterns from every prior section.

Run: python 05_projects/project3_multi_agent/workflow.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

from planner import create_plan, TaskPlan
from executor import execute_plan
from validator import validate_results, ValidationReport
from core.client import get_client, FAST_MODEL, cached_system
from core.logger import get_logger

log = get_logger(__name__)

MAX_RETRIES = 2


def synthesize_answer(task: str, results: dict[int, str], plan: TaskPlan) -> str:
    """Final synthesis: combine all step results into a coherent answer."""
    client = get_client()
    results_str = "\n".join(f"Step {k}: {v}" for k, v in results.items())
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=512,
        system=cached_system(
            "You are a synthesis agent. Combine execution results into a clear, "
            "complete answer to the original task. Be concise and direct."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Original task: {task}\n\n"
                f"Execution results:\n{results_str}\n\n"
                "Write a clear, complete answer."
            ),
        }],
    )
    return response.content[0].text.strip()


def run_workflow(task: str, verbose: bool = True) -> dict:
    """
    Full multi-agent workflow:
      1. Planner creates structured plan
      2. Executor runs each step
      3. Validator checks quality
      4. Synthesizer creates final answer
      If validator rejects, retry up to MAX_RETRIES times.
    """
    if verbose:
        print(f"\n{'='*65}")
        print(f"TASK: {task}")
        print(f"{'='*65}")

    # ── Phase 1: Plan ─────────────────────────────────────────────────────────
    if verbose:
        print("\n[Phase 1] PLANNING...")
    plan = create_plan(task)

    if verbose:
        print(f"  Created {len(plan.steps)}-step plan:")
        for step in plan.steps:
            print(f"  Step {step.step_number}: [{step.tool}] {step.description}")

    # ── Phase 2: Execute + Validate (with retries) ────────────────────────────
    results = None
    validation = None

    for attempt in range(1, MAX_RETRIES + 2):
        if verbose:
            print(f"\n[Phase 2] EXECUTING (attempt {attempt}/{MAX_RETRIES + 1})...")

        results = execute_plan(plan.steps)

        if verbose:
            for step_num, result in results.items():
                print(f"  Step {step_num}: {result[:100]}")

        # ── Phase 3: Validate ─────────────────────────────────────────────────
        if verbose:
            print(f"\n[Phase 3] VALIDATING...")
        validation = validate_results(task, plan.steps, results)

        if verbose:
            print(f"  Overall score: {validation.overall_score:.2f}")
            for sv in validation.step_validations:
                icon = "✓" if sv.approved else "✗"
                print(f"  {icon} Step {sv.step_number}: score={sv.score:.2f} {sv.issue[:50]}")

        if validation.approved:
            if verbose:
                print(f"  ✅ Validated! Score: {validation.overall_score:.2f}")
            break

        if attempt <= MAX_RETRIES:
            if verbose:
                print(f"  ⚠️  Score {validation.overall_score:.2f} below threshold. Retrying...")
        else:
            if verbose:
                print(f"  ❌ Max retries reached. Proceeding with best available results.")

    if validation and validation.requires_human_review:
        if verbose:
            print("\n  ⚠️  HUMAN REVIEW REQUIRED — confidence too low for auto-approval")

    # ── Phase 4: Synthesize ───────────────────────────────────────────────────
    if verbose:
        print(f"\n[Phase 4] SYNTHESIZING...")
    final_answer = synthesize_answer(task, results, plan)

    if verbose:
        print(f"\n{'─'*65}")
        print(f"FINAL ANSWER:\n{final_answer}")
        print(f"{'─'*65}")
        print(f"Plan steps: {len(plan.steps)} | "
              f"Validation score: {validation.overall_score:.2f} | "
              f"Human review: {validation.requires_human_review}")

    log.info(
        "workflow.complete",
        task=task[:50],
        steps=len(plan.steps),
        score=validation.overall_score if validation else 0,
        approved=validation.approved if validation else False,
    )

    return {
        "task": task,
        "answer": final_answer,
        "steps_executed": len(plan.steps),
        "validation_score": validation.overall_score if validation else 0,
        "approved": validation.approved if validation else False,
        "requires_human_review": validation.requires_human_review if validation else True,
    }


if __name__ == "__main__":
    print("=== MULTI-AGENT WORKFLOW DEMO ===")
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

    print("--- Multi-Agent Pattern Summary ---")
    print("  Planner:   Decomposes task, picks tools per step")
    print("  Executor:  Runs each step, passes context forward")
    print("  Validator: Quality gate, requests retry if needed")
    print("  Synthesizer: Combines results into coherent answer")
    print("\n  This pattern is used in: LangGraph, AutoGen, CrewAI, Semantic Kernel")
