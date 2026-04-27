"""
Shared Pydantic models used across study modules.
"""
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


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
