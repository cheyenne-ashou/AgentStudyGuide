"""
Project 1: Tool-Using Agent
A complete agent that:
  - Uses 4 tools: calculator, datetime, web search, note-taking
  - Persists notes across steps (simulated long-term memory)
  - Handles retries with exponential backoff
  - Enforces max iteration limit
  - Logs every step with structured logging

This is the "hello world" of agentic systems.
Run: python 05_projects/project1_tool_agent/agent.py
"""
import sys
import json
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.client import get_client, MODEL, cached_system
from core.logger import get_logger
from core.models import AgentStep, ToolCall
from tools import TOOL_SCHEMAS, execute_tool

log = get_logger(__name__)

SYSTEM_PROMPT = """You are a research and calculation assistant.
Use your tools to answer questions accurately. When you find useful information,
save it with the note_taking tool so you can reference it later.
Give a clear, complete final answer when done."""

MAX_STEPS = 15


@retry(
    retry=retry_if_exception_type(anthropic.RateLimitError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
)
def _call_claude(client, messages: list[dict]) -> anthropic.types.Message:
    return client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=cached_system(SYSTEM_PROMPT),
        tools=TOOL_SCHEMAS,
        messages=messages,
    )


def run_agent(task: str) -> str:
    client = get_client()
    messages = [{"role": "user", "content": task}]
    steps: list[AgentStep] = []

    print(f"\n{'='*60}")
    print(f"TASK: {task}")
    print(f"{'='*60}")

    for step_num in range(1, MAX_STEPS + 1):
        log.info("agent.step.start", step=step_num, task_preview=task[:50])

        try:
            response = _call_claude(client, messages)
        except Exception as e:
            log.error("agent.llm_error", step=step_num, error=str(e))
            return f"Agent failed on step {step_num}: {e}"

        tool_calls_this_step: list[ToolCall] = []
        tool_results: list[dict] = []
        text_output = ""

        for block in response.content:
            if block.type == "text" and block.text.strip():
                text_output = block.text.strip()
                print(f"\n[{step_num}] Thought: {text_output[:250]}")

            elif block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                print(f"[{step_num}] ▶ {block.name}({json.dumps(block.input)[:80]})")
                print(f"[{step_num}] ◀ {result[:150]}")

                tool_calls_this_step.append(
                    ToolCall(name=block.name, input=block.input, result=result)
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        steps.append(AgentStep(
            step=step_num,
            thought=text_output,
            tool_calls=tool_calls_this_step,
        ))

        log.info(
            "agent.step.done",
            step=step_num,
            tools=[tc.name for tc in tool_calls_this_step],
            stop_reason=response.stop_reason,
        )

        if response.stop_reason == "end_turn":
            final = next(
                (b.text for b in response.content if b.type == "text"), "Done."
            )
            print(f"\n{'─'*60}")
            print(f"FINAL ANSWER: {final}")
            print(f"Steps: {len(steps)} | Tokens: {response.usage.input_tokens}+{response.usage.output_tokens}")
            return final

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    log.error("agent.max_steps_reached", max_steps=MAX_STEPS)
    return f"Agent reached max {MAX_STEPS} steps without finishing."


if __name__ == "__main__":
    tasks = [
        # Task 1: Math + datetime
        "Calculate: if I invest $10,000 at 7% annual return for 20 years using compound interest, "
        "what will my investment be worth? Save the result as a note. Also, what day is it today?",

        # Task 2: Research + note-taking
        "Search for information about RAG systems and FastAPI, save key facts as notes, "
        "then summarize what you found.",
    ]

    for task in tasks:
        result = run_agent(task)
        print(f"\n{'='*60}\n")
