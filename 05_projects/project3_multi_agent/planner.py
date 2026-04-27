"""
Project 3: Multi-Agent Workflow — Planner
Decomposes a complex task into a structured, executable step list.
Each step specifies what to do and which tool (if any) to use.
"""
import sys
import json
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from pydantic import BaseModel, Field
from core.client import get_client, MODEL, cached_system
from core.logger import get_logger

log = get_logger(__name__)

PLANNER_SYSTEM = """You are a planning agent. When given a task, decompose it into
clear, sequential steps. Each step should be specific and actionable.
Respond with ONLY valid JSON — no prose, no markdown."""


class TaskStep(BaseModel):
    step_number: int
    description: str
    tool: str = Field(description="One of: web_search, calculator, get_datetime, none")
    expected_output: str


class TaskPlan(BaseModel):
    task: str
    steps: list[TaskStep]
    total_steps: int


def create_plan(task: str) -> TaskPlan:
    client = get_client()

    schema = {
        "task": "string",
        "steps": [
            {
                "step_number": "int",
                "description": "string",
                "tool": "web_search | calculator | get_datetime | none",
                "expected_output": "string",
            }
        ],
        "total_steps": "int",
    }

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=cached_system(PLANNER_SYSTEM),
        messages=[{
            "role": "user",
            "content": (
                f"Task: {task}\n\n"
                f"Create a step-by-step plan. Use this JSON schema:\n"
                f"{json.dumps(schema, indent=2)}"
            ),
        }],
    )

    raw = response.content[0].text.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    plan = TaskPlan.model_validate_json(raw[start:end])

    log.info("planner.complete", task=task[:50], steps=len(plan.steps))
    return plan
