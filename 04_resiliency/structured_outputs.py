"""
Structured Outputs — .with_structured_output()
Forces LLM responses into a defined Pydantic schema with one method call.

The old pattern:
  1. Tell the model to respond in JSON
  2. Extract JSON from the text (fragile)
  3. Validate with Pydantic
  4. If invalid, re-prompt with the error message
  5. After max retries, raise

The new pattern:
  structured_llm = llm.with_structured_output(MyModel)
  result = structured_llm.invoke("...")  ← returns a validated MyModel instance

.with_structured_output() handles schema injection, parsing, and Pydantic validation
internally. The extract_json() function and retry loop become unnecessary.

When .with_structured_output() is NOT enough:
  - Very complex nested extraction with cross-field dependencies
  - When you need to validate business rules beyond type constraints
  - When the model systematically fails on a particular schema (use the re-prompting
    loop as a fallback)

Run: python 04_resiliency/structured_outputs.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from pydantic import BaseModel, Field
from core.client import get_llm, get_fast_llm
from core.logger import get_logger

log = get_logger(__name__)


# ── Schema definitions (unchanged from the old version) ───────────────────────

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


if __name__ == "__main__":
    print("=== STRUCTURED OUTPUTS DEMO (.with_structured_output()) ===\n")

    llm = get_fast_llm()

    # ── Demo 1: Task planning ─────────────────────────────────────────────────
    print("--- Demo 1: Task Plan ---")
    plan: TaskPlan = llm.with_structured_output(TaskPlan).invoke(
        "Create a plan to build a simple RAG system in Python."
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
    structured_sentiment = llm.with_structured_output(SentimentResult)
    texts = [
        "This RAG implementation is brilliant! Works perfectly.",
        "The agent keeps hallucinating and it's incredibly frustrating.",
        "The system processes requests in about 2 seconds.",
    ]
    for text in texts:
        result: SentimentResult = structured_sentiment.invoke(
            f"Analyze the sentiment of this text: '{text}'"
        )
        print(f"  {result.sentiment:>8} ({result.score:+.2f})  {text[:50]}")

    # ── Demo 3: Agent decision ────────────────────────────────────────────────
    print("\n--- Demo 3: Agent Decision ---")
    decision: AgentDecision = llm.with_structured_output(AgentDecision).invoke(
        "You are an agent. The user asked: 'What is the current price of AAPL?'\n"
        "Available tools: web_search, calculator, get_datetime.\n"
        "What should you do next?"
    )
    print(f"  Action:     {decision.action}")
    print(f"  Tool:       {decision.tool_name}")
    print(f"  Input:      {decision.tool_input}")
    print(f"  Reasoning:  {decision.reasoning[:100]}")
    print(f"  Confidence: {decision.confidence}")

    print("\n--- .with_structured_output() vs old extract_json() pattern ---")
    print("  Old: 30-line structured_complete() with:")
    print("       1. schema_str injection into system prompt")
    print("       2. extract_json() to find { } in the response")
    print("       3. json.loads() + Pydantic.model_validate()")
    print("       4. re-prompting loop on validation failure")
    print()
    print("  New: structured_llm = llm.with_structured_output(MyModel)")
    print("       result = structured_llm.invoke('your prompt')  ← done")
    print("       result is already a validated MyModel instance")

    print("\n--- Why Structured Outputs Matter ---")
    print("  Agents need to parse tool call inputs, plans, decisions.")
    print("  Free-form text requires fragile regex parsing.")
    print("  Pydantic schemas: self-documenting, validated, type-safe.")
    print("  .with_structured_output() handles the entire extraction pipeline.")
