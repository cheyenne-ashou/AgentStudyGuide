"""
Function Calling End-to-End Demo
Shows the complete tool_use cycle with Claude:
  1. Send query + tool schemas
  2. Claude returns tool_use block
  3. Execute the tool
  4. Return tool_result
  5. Claude generates final answer

This is the lowest-level demo — no agent abstraction, just raw API calls.
Understand this before studying react_agent.py.

Run: python 02_agentic_core/tool_use/function_calling.py
"""
import sys
import json
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

from core.client import get_client, MODEL
from sample_tools import build_registry


def run_single_tool_call(query: str) -> str:
    """Step-by-step: one tool call, explicit at every stage."""
    client = get_client()
    registry = build_registry()

    print(f"\nQuery: {query}")
    print("-" * 50)

    # Turn 1: send query with tools
    print("→ Sending to Claude with tool schemas...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        tools=registry.to_claude_tools(),
        messages=[{"role": "user", "content": query}],
    )
    print(f"  stop_reason: {response.stop_reason}")
    print(f"  content blocks: {[b.type for b in response.content]}")

    if response.stop_reason != "tool_use":
        # Model answered directly without using a tool
        return response.content[0].text

    # Extract tool call
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    print(f"\n→ Claude wants to call: {tool_use_block.name}")
    print(f"  Input: {json.dumps(tool_use_block.input)}")

    # Execute the tool
    result = registry.call(tool_use_block.name, **tool_use_block.input)
    print(f"\n→ Tool result: {result}")

    # Turn 2: send tool result back to Claude
    print("\n→ Sending tool result back to Claude...")
    response2 = client.messages.create(
        model=MODEL,
        max_tokens=512,
        tools=registry.to_claude_tools(),
        messages=[
            {"role": "user", "content": query},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": result,
                }],
            },
        ],
    )

    return next(b.text for b in response2.content if b.type == "text")


def run_multi_tool_loop(query: str, max_turns: int = 6) -> str:
    """Full loop: keeps calling tools until Claude stops."""
    client = get_client()
    registry = build_registry()
    messages = [{"role": "user", "content": query}]

    print(f"\nQuery: {query}")
    print("-" * 50)

    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            tools=registry.to_claude_tools(),
            messages=messages,
        )

        # Collect all tool calls in this response
        tool_results = []
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"  Thought: {block.text.strip()[:100]}")
            elif block.type == "tool_use":
                result = registry.call(block.name, **block.input)
                print(f"  Tool: {block.name}({json.dumps(block.input)}) → {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if b.type == "text"), "Done."
            )

        # Append assistant message and all tool results
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "Max turns reached."


if __name__ == "__main__":
    print("=== FUNCTION CALLING DEMO ===")

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
    print("1. Tool schemas are JSON — model reads them and decides when/how to call")
    print("2. stop_reason='tool_use' means model wants to call a tool")
    print("3. stop_reason='end_turn' means model is done and has a final answer")
    print("4. Tool results go back as 'user' turn with type='tool_result'")
    print("5. Multiple tool_use blocks can appear in one response (parallel tool calls)")
