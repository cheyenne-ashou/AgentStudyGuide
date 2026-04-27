"""
ReAct Agent — THE Core Pattern
Implements Reason + Act using Claude's native tool_use blocks.

Loop: Think → Choose Tool → Execute → Observe → Repeat until done

This is the most important file in this repo. Every agentic framework
(LangChain, LangGraph, AutoGen, CrewAI) is a variation on this loop.
Understand it here, at the raw API level, before studying abstractions.

Run: python 02_agentic_core/patterns/react_agent.py
"""
import sys
import json
import math
from pathlib import Path
from datetime import datetime, timezone

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, MODEL, cached_system
from core.logger import get_logger
from core.models import AgentStep, ToolCall

log = get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant with access to tools.
Think carefully about what information you need, use tools to gather it,
and give a clear final answer when you have everything you need.
Do not use a tool if you already have the answer."""

TOOLS = [
    {
        "name": "calculator",
        "description": "Evaluate a mathematical expression. E.g., '(100 * 1.15) / 12'",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate"}
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_datetime",
        "description": "Get the current date and time in UTC (day, date, time).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "web_search",
        "description": "Search the web for current information on a topic.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> str:
    if name == "calculator":
        try:
            result = eval(tool_input["expression"], {"__builtins__": {}}, vars(math))
            return str(result)
        except Exception as e:
            return f"Error: {e}"
    elif name == "get_datetime":
        return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M:%S UTC")
    elif name == "web_search":
        q = tool_input["query"]
        return f"[MOCK] Top results for '{q}': 1) Comprehensive overview, 2) Recent updates, 3) Technical deep-dive"
    return f"Unknown tool: {name}"


def run_agent(query: str, max_steps: int = 10, verbose: bool = True) -> tuple[str, list[AgentStep]]:
    """
    Run the ReAct loop.
    Returns (final_answer, list_of_steps).
    """
    client = get_client()
    messages = [{"role": "user", "content": query}]
    steps: list[AgentStep] = []

    if verbose:
        print(f"\nQuery: {query}")
        print("─" * 60)

    for step_num in range(1, max_steps + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=cached_system(SYSTEM_PROMPT),
            tools=TOOLS,
            messages=messages,
        )

        tool_calls_this_step: list[ToolCall] = []
        tool_results: list[dict] = []
        thoughts: list[str] = []

        for block in response.content:
            if block.type == "text" and block.text.strip():
                thoughts.append(block.text.strip())
                if verbose:
                    print(f"\n[Step {step_num}] Thought: {block.text.strip()[:200]}")

            elif block.type == "tool_use":
                result = execute_tool(block.name, block.input)

                if verbose:
                    print(f"[Step {step_num}] Action:  {block.name}({json.dumps(block.input)})")
                    print(f"[Step {step_num}] Observe: {result[:150]}")

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
            thought=" | ".join(thoughts),
            tool_calls=tool_calls_this_step,
        ))

        log.info("agent.step", step=step_num, tools_called=[tc.name for tc in tool_calls_this_step])

        # If no tool calls, the agent has finished
        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if b.type == "text"), "Done."
            )
            return final_text, steps

        # Append assistant response and tool results, continue loop
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "Max steps reached without a final answer.", steps


if __name__ == "__main__":
    print("=== ReAct AGENT DEMO ===")

    # Task 1: multi-step math + datetime
    answer, steps = run_agent(
        "What is 25 * 47 + 100? Also, what day of the week is it today?"
    )
    print(f"\nFinal Answer: {answer}")
    print(f"Steps taken: {len(steps)}")

    # Task 2: requires search + calculation
    print("\n" + "=" * 60)
    answer2, steps2 = run_agent(
        "I need to save $50,000 in 3 years. How much do I need to save per month? "
        "Also search for current high-yield savings account rates."
    )
    print(f"\nFinal Answer: {answer2}")
    print(f"Steps taken: {len(steps2)}")

    # Print step summary
    print("\n--- Step Summary ---")
    for step in steps + steps2:
        tools = [tc.name for tc in step.tool_calls]
        print(f"  Step {step.step}: tools={tools or 'none (final answer)'}")

    print("\n--- Loop Anatomy ---")
    print("  1. Build messages list with user query")
    print("  2. Call Claude with tools defined")
    print("  3. If stop_reason='tool_use': execute tools, append results, go to 2")
    print("  4. If stop_reason='end_turn': extract text response, return")
    print("  5. If step_num >= max_steps: return timeout error")
