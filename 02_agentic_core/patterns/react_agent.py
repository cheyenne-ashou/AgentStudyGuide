"""
ReAct Agent — THE Core Pattern
Implements Reason + Act using LangGraph's StateGraph.

Loop: Think → Choose Tool → Execute → Observe → Repeat until done

This is the most important file in this repo. Every agentic framework
(LangGraph, AutoGen, CrewAI) is a variation on this loop.
Understand it here, at the graph level, before studying abstractions.

Mapping from the raw API version:
  call_model node     ← where client.messages.create() was
  should_continue     ← where if stop_reason == 'tool_use' was
  tools node          ← where the manual for block in response.content loop was
  The logic is identical; the structure is now explicit in the graph edges.

Run: python 02_agentic_core/patterns/react_agent.py
"""
import sys
import math
from pathlib import Path
from datetime import datetime, timezone

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, create_react_agent
from core.client import get_llm
from core.models import AgentState
from core.logger import get_logger

log = get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant with access to tools.
Think carefully about what information you need, use tools to gather it,
and give a clear final answer when you have everything you need.
Do not use a tool if you already have the answer."""


# ── Tool definitions ──────────────────────────────────────────────────────────

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. E.g., '(100 * 1.15) / 12'"""
    try:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool
def get_datetime() -> str:
    """Get the current date and time in UTC (day, date, time)."""
    return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M:%S UTC")


@tool
def web_search(query: str) -> str:
    """Search the web for current information on a topic."""
    return f"[MOCK] Top results for '{query}': 1) Comprehensive overview, 2) Recent updates, 3) Technical deep-dive"


tools = [calculator, get_datetime, web_search]
llm = get_llm().bind_tools(tools)


# ── Explicit StateGraph (the teaching version) ────────────────────────────────
# This IS the ReAct loop — it's now expressed as a directed graph.

def should_continue(state: AgentState) -> str:
    """Router: go to tools if the LLM made tool calls, else end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


def call_model(state: AgentState) -> dict:
    """Agent node: call the LLM with the current message history."""
    messages = state["messages"]
    # Prepend system message if not already present
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm.invoke(messages)
    log.info("agent.call_model", tool_calls=[tc["name"] for tc in response.tool_calls])
    return {"messages": [response]}


def build_explicit_react_graph():
    """Build the ReAct StateGraph explicitly to show every component."""
    workflow = StateGraph(AgentState)

    # Two nodes: the LLM and the tool executor
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))

    # Entry point: always start at agent
    workflow.set_entry_point("agent")

    # Conditional edge: agent → tools (if tool calls present) or END
    workflow.add_conditional_edges("agent", should_continue)

    # After tools run, always go back to agent to process the results
    workflow.add_edge("tools", "agent")

    return workflow.compile()


def run_agent(query: str, max_steps: int = 10, verbose: bool = True) -> str:
    """Run the explicit ReAct StateGraph."""
    agent = build_explicit_react_graph()
    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
    )
    final_message = result["messages"][-1]
    if verbose:
        print(f"\nQuery: {query}")
        print("─" * 60)
        print(f"Final Answer: {final_message.content}")
        # Show the step-by-step trace
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"  → Tool: {tc['name']}({tc['args']})")
            elif hasattr(msg, "name") and msg.name:
                print(f"  ← Result: {msg.content[:100]}")
    return final_message.content


if __name__ == "__main__":
    print("=== ReAct AGENT DEMO (LangGraph StateGraph) ===")

    # Task 1: multi-step math + datetime
    run_agent("What is 25 * 47 + 100? Also, what day of the week is it today?")

    # Task 2: requires search + calculation
    print("\n" + "=" * 60)
    run_agent(
        "I need to save $50,000 in 3 years. How much do I need to save per month? "
        "Also search for current high-yield savings account rates."
    )

    print("\n--- Graph Anatomy (maps to old raw API loop) ---")
    print("  call_model node     ← was: client.messages.create()")
    print("  should_continue     ← was: if response.stop_reason == 'tool_use'")
    print("  ToolNode            ← was: for block in response.content (tool_use blocks)")
    print("  tools → agent edge  ← was: messages.append(tool_results); continue loop")
    print("  END                 ← was: return final_text")

    print("\n--- Shorthand: create_react_agent() ---")
    print("  The explicit graph above collapses to one line in production:")
    print("  agent = create_react_agent(get_llm(), tools=tools)")
    quick_agent = create_react_agent(get_llm(), tools=tools)
    quick_result = quick_agent.invoke({"messages": [HumanMessage(content="What is sqrt(256)?")]})
    print(f"  Result: {quick_result['messages'][-1].content}")
