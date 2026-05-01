"""
Shared Pydantic models and LangGraph TypedDict state schemas.
"""
import operator
from pydantic import BaseModel, Field
from typing import Any, Annotated, TypedDict
from datetime import datetime
from langgraph.graph.message import add_messages


# ── LangGraph State Schemas ───────────────────────────────────────────────────

class AgentState(TypedDict):
    """Base state for all ReAct agents. The add_messages reducer appends
    new messages rather than overwriting, enabling incremental history."""
    messages: Annotated[list, add_messages]


class PlanExecuteState(TypedDict):
    """State for plan-and-execute agents: tracks the plan, accumulated
    step results, and the final response once execution completes."""
    messages: Annotated[list, add_messages]
    plan: list[str]
    past_steps: Annotated[list, operator.add]
    response: str | None


class SupervisorState(TypedDict):
    """State for supervisor/multi-agent graphs. next_agent is written by
    the supervisor node and read by the router edge."""
    messages: Annotated[list, add_messages]
    next_agent: str


# ── Pydantic Models (logging, eval, tool tracking) ───────────────────────────

class ToolCall(BaseModel):
    name: str
    input: dict[str, Any]
    result: Any = None


class AgentStep(BaseModel):
    step: int
    thought: str = ""
    action: str = ""
    observation: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        parts = [f"Step {self.step}"]
        if self.thought:
            parts.append(f"Thought: {self.thought[:80]}")
        if self.action:
            parts.append(f"Action: {self.action}")
        if self.observation:
            parts.append(f"Obs: {self.observation[:80]}")
        return " | ".join(parts)


class MemoryEntry(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvalResult(BaseModel):
    question: str
    expected: str
    actual: str
    passed: bool
    score: float = 0.0
    notes: str = ""

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] score={self.score:.2f} | {self.question[:60]}"
