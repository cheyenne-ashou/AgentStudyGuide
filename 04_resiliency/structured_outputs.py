"""
Structured Outputs — JSON Enforcement
Forces LLM responses into a defined schema, with re-prompting on failure.

The problem: LLMs are trained to be helpful, not machine-readable.
Without enforcement, you get inconsistent formats, missing fields, prose instead of JSON.

The solution:
  1. Tell the model to respond in JSON
  2. Validate with Pydantic
  3. If invalid, re-prompt with the error message
  4. After max retries, raise or return a default

Run: python 04_resiliency/structured_outputs.py
"""
import sys
import json
from pathlib import Path
from typing import TypeVar, Type

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from pydantic import BaseModel, Field
from core.client import get_client, MODEL, FAST_MODEL, cached_system
from core.logger import get_logger

log = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


# ── Schema definitions ────────────────────────────────────────────────────────

class TaskPlan(BaseModel):
    title: str
    steps: list[str] = Field(..., min_length=1, max_length=10)
    estimated_minutes: int = Field(..., ge=1, le=480)
    tools_needed: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)


class SentimentResult(BaseModel):
    sentiment: str = Field(..., pattern=r"^(positive|negative|neutral)$")
    score: float = Field(..., ge=-1.0, le=1.0)
    reasoning: str = Field(..., max_length=200)


class AgentDecision(BaseModel):
    action: str = Field(..., pattern=r"^(call_tool|ask_human|give_answer|escalate)$")
    tool_name: str | None = None
    tool_input: dict = Field(default_factory=dict)
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)


# ── JSON extraction utilities ─────────────────────────────────────────────────

def extract_json(text: str) -> str:
    """Extract JSON from a response that may contain prose around it."""
    # Try to find a JSON object
    start = text.find("{")
    if start == -1:
        return text
    # Find the matching closing brace
    depth = 0
    for i, char in enumerate(text[start:], start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]


def structured_complete(
    prompt: str,
    schema: Type[T],
    system: str = "",
    max_retries: int = 3,
    model: str = FAST_MODEL,
) -> T:
    """
    Ask the LLM to respond as JSON matching the given Pydantic schema.
    Re-prompts with validation errors on failure.
    """
    client = get_client()

    schema_str = json.dumps(schema.model_json_schema(), indent=2)
    base_system = (
        f"{system}\n\n"
        f"IMPORTANT: Respond with ONLY valid JSON matching this exact schema. "
        f"No prose, no markdown, no code blocks — just the JSON object.\n\n"
        f"Schema:\n{schema_str}"
    )

    messages = [{"role": "user", "content": prompt}]

    for attempt in range(1, max_retries + 1):
        response = client.messages.create(
            model=model,
            max_tokens=512,
            system=cached_system(base_system),
            messages=messages,
        )
        raw = response.content[0].text.strip()
        json_str = extract_json(raw)

        try:
            data = json.loads(json_str)
            result = schema.model_validate(data)
            log.info("structured_output.success", attempt=attempt, schema=schema.__name__)
            return result
        except Exception as e:
            log.warning("structured_output.retry", attempt=attempt, error=str(e)[:100])
            if attempt < max_retries:
                # Inject the error into the conversation so Claude can self-correct
                messages.append({"role": "assistant", "content": raw})
                messages.append({
                    "role": "user",
                    "content": f"The JSON was invalid. Error: {e}\n\nPlease fix it and respond with valid JSON only."
                })

    raise ValueError(f"Failed to get valid {schema.__name__} after {max_retries} attempts")


if __name__ == "__main__":
    print("=== STRUCTURED OUTPUTS DEMO ===\n")

    # ── Demo 1: Task planning ─────────────────────────────────────────────────
    print("--- Demo 1: Task Plan ---")
    plan = structured_complete(
        prompt="Create a plan to build a simple RAG system in Python.",
        schema=TaskPlan,
        system="You are a project planning assistant.",
    )
    print(f"  Title:      {plan.title}")
    print(f"  Steps:      {len(plan.steps)}")
    for i, step in enumerate(plan.steps, 1):
        print(f"    {i}. {step}")
    print(f"  Time est:   {plan.estimated_minutes} minutes")
    print(f"  Tools:      {plan.tools_needed}")
    print(f"  Confidence: {plan.confidence}")

    # ── Demo 2: Sentiment analysis ───────────────────────────────────────────
    print("\n--- Demo 2: Sentiment Analysis ---")
    texts = [
        "This RAG implementation is brilliant! Works perfectly.",
        "The agent keeps hallucinating and it's incredibly frustrating.",
        "The system processes requests in about 2 seconds.",
    ]
    for text in texts:
        result = structured_complete(
            prompt=f"Analyze the sentiment of this text: '{text}'",
            schema=SentimentResult,
        )
        print(f"  {result.sentiment:>8} ({result.score:+.2f})  {text[:50]}")

    # ── Demo 3: Agent decision ────────────────────────────────────────────────
    print("\n--- Demo 3: Agent Decision ---")
    decision = structured_complete(
        prompt=(
            "You are an agent. The user asked: 'What is the current price of AAPL?'\n"
            "Available tools: web_search, calculator, get_datetime.\n"
            "What should you do next?"
        ),
        schema=AgentDecision,
        system="You are a decision-making agent.",
    )
    print(f"  Action:     {decision.action}")
    print(f"  Tool:       {decision.tool_name}")
    print(f"  Input:      {decision.tool_input}")
    print(f"  Reasoning:  {decision.reasoning[:100]}")
    print(f"  Confidence: {decision.confidence}")

    print("\n--- Why Structured Outputs Matter ---")
    print("  Agents need to parse tool call inputs, plans, decisions.")
    print("  Free-form text requires fragile regex parsing.")
    print("  Pydantic schemas: self-documenting, validated, type-safe.")
    print("  Re-prompting: 90%+ of JSON errors self-correct on retry.")
