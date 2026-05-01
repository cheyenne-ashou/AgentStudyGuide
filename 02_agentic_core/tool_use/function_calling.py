"""
Function Calling End-to-End Demo
Shows the complete tool calling cycle with LangGraph:
  1. Decorate Python functions with @tool
  2. Bind tools to the LLM with bind_tools()
  3. LLM returns an AIMessage with .tool_calls populated
  4. ToolNode executes them and returns ToolMessages
  5. LLM generates a final answer

Understand this before studying react_agent.py, which wraps this
pattern in a StateGraph so the loop is explicit in the graph edges.

Run: python 02_agentic_core/tool_use/function_calling.py
"""
import sys
import math
from pathlib import Path
from datetime import datetime, timezone

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from core.client import get_llm


# ── Tool definitions using @tool decorator ────────────────────────────────────
# The decorator reads the function signature and docstring to build the
# JSON schema the LLM needs. No manual schema writing required.

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Supports +, -, *, /, **, sqrt, log."""
    safe_globals = {"__builtins__": {}}
    safe_locals = {k: v for k, v in vars(math).items() if not k.startswith("_")}
    try:
        result = eval(expression, safe_globals, safe_locals)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_datetime() -> str:
    """Get the current UTC date, time, and day of week."""
    return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M:%S UTC")


@tool
def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between units. Supports: km/miles, kg/lbs, celsius/fahrenheit."""
    conversions = {
        ("km", "miles"): lambda v: v * 0.621371,
        ("miles", "km"): lambda v: v * 1.60934,
        ("kg", "lbs"): lambda v: v * 2.20462,
        ("lbs", "kg"): lambda v: v * 0.453592,
        ("celsius", "fahrenheit"): lambda v: v * 9 / 5 + 32,
        ("fahrenheit", "celsius"): lambda v: (v - 32) * 5 / 9,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key not in conversions:
        return f"Unknown conversion: {from_unit} → {to_unit}"
    result = conversions[key](value)
    return f"{value} {from_unit} = {result:.4f} {to_unit}"


tools = [calculator, get_datetime, unit_converter]
tool_node = ToolNode(tools)               # pre-built node that executes tool calls
llm_with_tools = get_llm().bind_tools(tools)  # LLM that knows about the tools


# ── Part 1: Single tool call (step-by-step) ───────────────────────────────────

def run_single_tool_call(query: str) -> str:
    """Step-by-step: one tool call, explicit at every stage."""
    print(f"\nQuery: {query}")
    print("-" * 50)

    # Turn 1: send query — LLM returns an AIMessage with .tool_calls populated
    print("→ Sending to LLM with tools bound...")
    response: AIMessage = llm_with_tools.invoke([HumanMessage(content=query)])
    print(f"  tool_calls: {[tc['name'] for tc in response.tool_calls]}")

    if not response.tool_calls:
        # Model answered directly without calling a tool
        return response.content

    # ToolNode executes all tool calls and returns a list of ToolMessages
    print(f"\n→ ToolNode executing: {response.tool_calls[0]['name']}")
    tool_messages = tool_node.invoke([response])
    print(f"  Result: {tool_messages[0].content}")

    # Turn 2: send tool results back — LLM generates final answer
    print("\n→ Sending tool result back to LLM...")
    final = llm_with_tools.invoke([HumanMessage(content=query), response] + tool_messages)
    return final.content


# ── Part 2: Multi-turn tool loop ──────────────────────────────────────────────

def run_multi_tool_loop(query: str, max_turns: int = 6) -> str:
    """Full loop: keeps calling tools until LLM produces no more tool_calls."""
    messages = [HumanMessage(content=query)]
    print(f"\nQuery: {query}")
    print("-" * 50)

    for turn in range(max_turns):
        response: AIMessage = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            # No more tool calls — LLM is done
            return response.content

        # Execute all tool calls in this response
        print(f"  Turn {turn + 1} — tool calls: {[tc['name'] for tc in response.tool_calls]}")
        tool_messages = tool_node.invoke([response])
        for tm in tool_messages:
            print(f"    {tm.name}: {tm.content}")
        messages.extend(tool_messages)

    return "Max turns reached."


if __name__ == "__main__":
    print("=== FUNCTION CALLING DEMO (LangGraph) ===")

    print("\n\n=== PART 1: Single Tool Call (step-by-step) ===")
    answer = run_single_tool_call("What is 847 divided by 7?")
    print(f"\nFinal answer: {answer}")

    print("\n\n=== PART 2: Multi-Turn Tool Loop ===")
    answer = run_multi_tool_loop(
        "What is 25 * 47? Also, what day of the week is it today? "
        "And how many miles is 100 km?"
    )
    print(f"\nFinal answer: {answer}")

    print("\n--- Key Takeaways ---")
    print("1. @tool reads the function docstring to build the JSON schema automatically")
    print("2. bind_tools() attaches tool schemas to the LLM")
    print("3. response.tool_calls (non-empty) means the LLM wants to call a tool")
    print("4. ToolNode executes all tool calls and returns ToolMessages")
    print("5. react_agent.py wraps this loop as a StateGraph — same logic, explicit structure")

    print("\n--- @tool vs raw JSON schema (old pattern) ---")
    print("  Old: hand-write {'name': 'calculator', 'input_schema': {...}}")
    print("  New: @tool decorator reads the function and builds it automatically")
