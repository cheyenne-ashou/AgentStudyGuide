"""
Orchestrator / Supervisor Pattern (LangGraph)
Central supervisor that routes tasks to specialized sub-agents
using Command(goto=...) and aggregates results.

The supervisor doesn't do the work — it decides WHO does the work.
Each sub-agent is specialized (researcher, calculator, summarizer).
Command(goto=...) is LangGraph's native routing primitive, replacing
hand-written if/elif routing logic.

Architecture (as a LangGraph):
  User → supervisor → [researcher | calculator | summarizer] → supervisor → END

Run: python 03_system_design/orchestrator.py
"""
import sys
import re
import time
from pathlib import Path
from typing import Literal

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from core.client import get_llm, get_fast_llm
from core.models import SupervisorState
from core.logger import get_logger

log = get_logger(__name__)

MEMBERS = ["researcher", "calculator", "summarizer"]
OPTIONS = MEMBERS + ["FINISH"]


# ── Supervisor node ───────────────────────────────────────────────────────────

SUPERVISOR_PROMPT = (
    f"You are a supervisor coordinating these agents: {', '.join(MEMBERS)}.\n"
    "Given the conversation, decide who should act next, or FINISH if done.\n"
    f"Reply with ONLY one of: {', '.join(OPTIONS)}."
)


def supervisor_node(state: SupervisorState) -> Command[Literal["researcher", "calculator", "summarizer", "__end__"]]:
    """Route to the best specialist, or finish if the task is complete."""
    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    response = get_fast_llm().invoke(messages)
    next_agent = response.content.strip()

    # Clean up any surrounding punctuation
    next_agent = next_agent.strip("'\".,;").strip()

    if next_agent not in OPTIONS:
        next_agent = "FINISH"

    log.info("supervisor.route", next_agent=next_agent)
    print(f"\n  [Supervisor] → {next_agent}")

    if next_agent == "FINISH":
        return Command(goto=END)
    return Command(goto=next_agent, update={"next_agent": next_agent})


# ── Specialist agent nodes ────────────────────────────────────────────────────

def researcher_node(state: SupervisorState) -> Command[Literal["supervisor"]]:
    """Research agent: provides factual information."""
    task = state["messages"][-1].content
    response = get_fast_llm().invoke([
        SystemMessage(content="You are a research agent. Provide factual, concise information."),
        HumanMessage(content=f"Research task: {task}"),
    ])
    result = AIMessage(content=f"[Researcher] {response.content}", name="researcher")
    log.info("researcher.complete", preview=response.content[:60])
    return Command(goto="supervisor", update={"messages": [result]})


def calculator_node(state: SupervisorState) -> Command[Literal["supervisor"]]:
    """Calculator agent: extracts and evaluates math expressions."""
    task = state["messages"][-1].content
    numbers = re.findall(r"\d+(?:\.\d+)?", task)
    if len(numbers) >= 2:
        a, b = float(numbers[0]), float(numbers[1])
        result_text = f"Calculation: {a} × {b} = {a * b}"
    else:
        result_text = "No numeric calculation found in the request."
    result = AIMessage(content=f"[Calculator] {result_text}", name="calculator")
    log.info("calculator.complete", preview=result_text[:60])
    return Command(goto="supervisor", update={"messages": [result]})


def summarizer_node(state: SupervisorState) -> Command[Literal["supervisor"]]:
    """Summarizer agent: condenses information to key points."""
    task = state["messages"][-1].content
    response = get_fast_llm().invoke([
        SystemMessage(content="You are a summarizer. Be extremely concise."),
        HumanMessage(content=f"Summarize in 2 sentences: {task}"),
    ])
    result = AIMessage(content=f"[Summarizer] {response.content}", name="summarizer")
    log.info("summarizer.complete", preview=response.content[:60])
    return Command(goto="supervisor", update={"messages": [result]})


# ── Build the graph ───────────────────────────────────────────────────────────

def build_supervisor_graph():
    workflow = StateGraph(SupervisorState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("calculator", calculator_node)
    workflow.add_node("summarizer", summarizer_node)

    # All nodes use Command(goto=...) for routing — no explicit add_edge needed
    workflow.set_entry_point("supervisor")
    return workflow.compile()


if __name__ == "__main__":
    print("=== SUPERVISOR PATTERN DEMO (LangGraph) ===\n")
    print(f"Agents: {', '.join(MEMBERS)}")
    print()

    agent = build_supervisor_graph()

    tasks = [
        "What is RAG and how does it work?",
        "Calculate: if I invest $10,000 at 7% annual return for 20 years, what do I get?",
        "Research and summarize the main differences between LangChain and LlamaIndex.",
    ]

    for task in tasks:
        print(f"\n{'='*60}")
        print(f"Request: {task}")
        result = agent.invoke(
            {"messages": [HumanMessage(content=task)], "next_agent": ""},
        )
        # Last AI message is the final result
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if ai_messages:
            print(f"\nResult: {ai_messages[-1].content[:300]}")

    print("\n--- Design Patterns Shown ---")
    print("  1. Command(goto=...) replaces hand-written routing if/elif chains")
    print("  2. Single responsibility: each agent node does one thing well")
    print("  3. Supervisor loop: supervisor → specialist → supervisor → ... → END")
    print("  4. Centralized logging: every routing decision is traced")

    print("\n--- Command(goto=...) vs old pattern ---")
    print("  Old: if 'researcher' in selected: run_agent('researcher', task)")
    print("  New: return Command(goto='researcher', update={'messages': [...]})")
    print("       LangGraph handles the routing, state merging, and loop control")
