"""
Project 1: Tool-Using Agent (LangGraph)
A complete agent that:
  - Uses 4 tools via @tool decorator: calculator, datetime, web search, note-taking
  - Persists conversation across turns with MemorySaver
  - Retries transient errors via .with_retry()
  - Enforces max iteration limit via recursion_limit
  - Logs every step with structured logging

This is the "hello world" of LangGraph agentic systems.
Run: python 05_projects/project1_tool_agent/agent.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from core.client import get_llm
from core.logger import get_logger
from tools import TOOLS

log = get_logger(__name__)

SYSTEM_PROMPT = """You are a research and calculation assistant.
Use your tools to answer questions accurately. When you find useful information,
save it with the note_taking tool so you can reference it later.
Give a clear, complete final answer when done."""

MAX_STEPS = 15


def build_agent():
    """
    create_react_agent() is the LangGraph shorthand for the explicit StateGraph
    shown in react_agent.py. Equivalent to:
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(TOOLS))
        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")
        return workflow.compile(checkpointer=MemorySaver())
    """
    memory = MemorySaver()
    llm = get_llm().with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
    return create_react_agent(
        llm,
        tools=TOOLS,
        checkpointer=memory,
        prompt=SYSTEM_PROMPT,
    )


def run_agent(task: str, session_id: str = "default") -> str:
    agent = build_agent()
    config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": MAX_STEPS,  # max nodes visited = max agent steps
    }

    print(f"\n{'='*60}")
    print(f"TASK: {task}")
    print(f"{'='*60}")

    log.info("agent.start", task=task[:50], session=session_id)

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=task)]},
            config,
        )
    except Exception as e:
        log.error("agent.error", error=str(e))
        return f"Agent failed: {e}"

    final_message = result["messages"][-1]
    final_answer = final_message.content

    # Count tool-calling turns for summary
    tool_turns = sum(
        1 for m in result["messages"]
        if hasattr(m, "tool_calls") and m.tool_calls
    )

    print(f"\n{'─'*60}")
    print(f"FINAL ANSWER: {final_answer}")
    print(f"Tool-calling turns: {tool_turns}")
    log.info("agent.complete", session=session_id, tool_turns=tool_turns)

    return final_answer


if __name__ == "__main__":
    tasks = [
        # Task 1: Math + datetime
        "Calculate: if I invest $10,000 at 7% annual return for 20 years using compound interest, "
        "what will my investment be worth? Save the result as a note. Also, what day is it today?",

        # Task 2: Research + note-taking
        "Search for information about RAG systems and LangGraph, save key facts as notes, "
        "then summarize what you found.",
    ]

    for i, task in enumerate(tasks, 1):
        result = run_agent(task, session_id=f"project1-task-{i}")
        print(f"\n{'='*60}\n")
