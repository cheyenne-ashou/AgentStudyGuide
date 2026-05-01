"""
Project 3: Multi-Agent Workflow — Validator
Checks the quality of execution results using .with_structured_output()
to guarantee a validated ValidationReport object.

The validator is the quality gate in the pipeline.
Without it, bad results flow through silently.
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from core.client import get_fast_llm
from core.logger import get_logger

log = get_logger(__name__)

VALIDATOR_SYSTEM = "You are a quality validation agent. Review execution results and assess completeness."

APPROVAL_THRESHOLD = 0.7


class StepValidation(BaseModel):
    step_number: int
    score: float = Field(..., ge=0.0, le=1.0)
    approved: bool
    issue: str = ""


class ValidationReport(BaseModel):
    overall_score: float
    approved: bool
    requires_human_review: bool
    step_validations: list[StepValidation]
    summary: str


def validate_results(
    task: str,
    steps: list,
    results: dict[int, str],
) -> ValidationReport:
    """Validate execution results using .with_structured_output()."""
    steps_summary = "\n".join(
        f"Step {s.step_number}: {s.description}\n  Result: {results.get(s.step_number, 'NO RESULT')[:200]}"
        for s in steps
    )

    structured_llm = get_fast_llm().with_structured_output(ValidationReport)

    report: ValidationReport = structured_llm.invoke([
        SystemMessage(content=VALIDATOR_SYSTEM),
        HumanMessage(content=(
            f"Original task: {task}\n\n"
            f"Execution results:\n{steps_summary}\n\n"
            f"Validate each step. Score 1.0=perfect, 0.7=acceptable, 0.4=partial, 0.0=wrong.\n"
            f"Set approved=true if overall score >= {APPROVAL_THRESHOLD}.\n"
            f"Set requires_human_review=true if score < 0.4."
        )),
    ])

    log.info(
        "validator.complete",
        task=task[:50],
        score=report.overall_score,
        approved=report.approved,
    )
    return report
