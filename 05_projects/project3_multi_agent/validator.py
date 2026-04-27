"""
Project 3: Multi-Agent Workflow — Validator
Checks the quality of execution results and either:
  - Approves the output (score >= threshold)
  - Requests a specific step to be re-run
  - Escalates to human if confidence is too low

The validator is the quality gate in the pipeline.
Without it, bad results flow through silently.
"""
import sys
import json
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from pydantic import BaseModel, Field
from core.client import get_client, FAST_MODEL, cached_system
from core.logger import get_logger

log = get_logger(__name__)

VALIDATOR_SYSTEM = """You are a quality validation agent. Review execution results
and assess whether each step was completed correctly and completely.
Respond with ONLY valid JSON."""

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
    steps: list,  # list[TaskStep]
    results: dict[int, str],
) -> ValidationReport:
    client = get_client()

    steps_summary = "\n".join(
        f"Step {s.step_number}: {s.description}\n  Result: {results.get(s.step_number, 'NO RESULT')[:200]}"
        for s in steps
    )

    schema = {
        "overall_score": "float 0-1",
        "approved": "bool",
        "requires_human_review": "bool",
        "step_validations": [
            {
                "step_number": "int",
                "score": "float 0-1",
                "approved": "bool",
                "issue": "string (empty if approved)",
            }
        ],
        "summary": "string",
    }

    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=512,
        system=cached_system(VALIDATOR_SYSTEM),
        messages=[{
            "role": "user",
            "content": (
                f"Original task: {task}\n\n"
                f"Execution results:\n{steps_summary}\n\n"
                f"Validate each step. Score 1.0=perfect, 0.7=acceptable, 0.4=partial, 0.0=wrong.\n"
                f"Approve if overall score >= {APPROVAL_THRESHOLD}.\n"
                f"JSON schema:\n{json.dumps(schema, indent=2)}"
            ),
        }],
    )

    raw = response.content[0].text.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    report = ValidationReport.model_validate_json(raw[start:end])

    log.info(
        "validator.complete",
        task=task[:50],
        score=report.overall_score,
        approved=report.approved,
    )
    return report
