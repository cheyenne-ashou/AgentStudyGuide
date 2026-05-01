"""
Project 3: Multi-Agent Workflow — Planner
Decomposes a complex task into a structured, executable step list using
.with_structured_output() to guarantee a validated TaskPlan object.
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from core.client import get_llm
from core.logger import get_logger

log = get_logger(__name__)

PLANNER_SYSTEM = """You are a planning agent. When given a task, decompose it into
clear, sequential steps. Each step should be specific and actionable."""

TOOLS_AVAILABLE = ["web_search", "calculator", "get_datetime", "none"]


class TaskStep(BaseModel):
    step_number: int
    description: str
    tool: str = Field(description=f"One of: {', '.join(TOOLS_AVAILABLE)}")
    expected_output: str


class TaskPlan(BaseModel):
    task: str
    steps: list[TaskStep]
    total_steps: int


def create_plan(task: str) -> TaskPlan:
    """Generate a structured plan using .with_structured_output()."""
    structured_llm = get_llm().with_structured_output(TaskPlan)

    plan: TaskPlan = structured_llm.invoke([
        SystemMessage(content=(
            f"{PLANNER_SYSTEM}\n"
            f"Available tools: {', '.join(TOOLS_AVAILABLE)}"
        )),
        HumanMessage(content=f"Task: {task}"),
    ])

    log.info("planner.complete", task=task[:50], steps=len(plan.steps))
    return plan
