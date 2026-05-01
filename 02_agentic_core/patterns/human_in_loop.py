"""
Human-in-the-Loop Pattern (LangGraph)
Demonstrates LangGraph's native interrupt() + Command(resume=...) API.

interrupt() pauses graph execution and surfaces data to the caller.
The caller resumes by passing Command(resume=<human_response>).

This replaces the old pattern of embedding approval logic inside the
agent's while loop. With LangGraph, the graph pauses at a node boundary
and can be resumed after any amount of time (e.g., the user responds
hours later — state is preserved in the checkpointer).

When to require human approval:
  - Irreversible actions (delete, send email, deploy)
  - Low-confidence outputs (score < threshold)
  - High-stakes decisions (financial, medical, legal)
  - First time an agent takes a new action type

Run: python 02_agentic_core/patterns/human_in_loop.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from core.client import get_llm
from core.models import AgentState


# ── Part 1: Approval Gate ─────────────────────────────────────────────────────

RISKY_ACTIONS = {"send_email", "delete_file", "deploy", "payment"}

llm = get_llm()


def draft_action_node(state: AgentState) -> dict:
    """Generate a draft action for the task."""
    task = state["messages"][-1].content
    response = llm.invoke([
        SystemMessage(content="You are a helpful agent. Describe the action you will take to complete the task."),
        HumanMessage(content=task),
    ])
    return {"messages": [response]}


def approval_gate_node(state: AgentState) -> dict:
    """
    Pause execution and wait for human approval.
    interrupt() surfaces the action details to the caller.
    The graph resumes when Command(resume=...) is passed.
    """
    last_message = state["messages"][-1].content
    print(f"\n  [APPROVAL REQUIRED]")
    print(f"  Proposed action: {last_message[:200]}")

    # interrupt() pauses the graph here and returns data to the caller
    human_response = interrupt({
        "question": "Approve this action?",
        "proposed_action": last_message,
    })

    if human_response == "approved":
        return {"messages": [AIMessage(content="Action approved and executed.")]}
    else:
        return {"messages": [AIMessage(content=f"Action rejected. Reason: {human_response}")]}


def build_approval_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("draft", draft_action_node)
    workflow.add_node("approval_gate", approval_gate_node)
    workflow.set_entry_point("draft")
    workflow.add_edge("draft", "approval_gate")
    workflow.add_edge("approval_gate", END)
    # MemorySaver is required for interrupt() to work — it preserves state
    return workflow.compile(checkpointer=MemorySaver())


def demo_approval_gate() -> None:
    """Run the approval gate demo with simulated human responses."""
    print("\n=== Part 1: Approval Gate ===")
    agent = build_approval_graph()
    config = {"configurable": {"thread_id": "approval-demo"}}

    task = "Summarize this week's engineering work and send an update email to the team."
    print(f"Task: {task}")

    # First invocation: graph runs until interrupt()
    result = agent.invoke({"messages": [HumanMessage(content=task)]}, config)

    # In real usage, the user sees the interrupt data and responds.
    # Here we simulate an immediate approval with Command(resume=...).
    print("\n  [Simulating human approval...]")
    resumed = agent.invoke(Command(resume="approved"), config)
    print(f"\n  Result: {resumed['messages'][-1].content}")


# ── Part 2: Feedback Loop ─────────────────────────────────────────────────────

def draft_writer_node(state: AgentState) -> dict:
    """Generate a draft response."""
    messages = state["messages"]
    response = llm.invoke([
        SystemMessage(content="You are a helpful writing assistant. Produce clear, concise output."),
    ] + messages)
    return {"messages": [response]}


def feedback_review_node(state: AgentState) -> dict:
    """
    Show the draft to the human and collect feedback.
    If feedback is empty, the draft is approved.
    If feedback is provided, it's injected as a user message so the writer revises.
    """
    draft = state["messages"][-1].content
    print(f"\n  [DRAFT FOR REVIEW]:\n  {draft[:300]}")

    human_feedback = interrupt({
        "question": "Any changes needed? (empty = approve as-is)",
        "draft": draft,
    })

    if not human_feedback:
        return {"messages": [AIMessage(content="[APPROVED] " + draft)]}
    else:
        # Inject feedback as a new user message — the writer node will revise
        return {"messages": [HumanMessage(content=f"Please revise: {human_feedback}")]}


def route_after_review(state: AgentState) -> str:
    """If the last message is a revision request, go back to the writer."""
    last = state["messages"][-1]
    if isinstance(last, HumanMessage):
        return "writer"  # needs revision
    return END  # approved


def build_feedback_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("writer", draft_writer_node)
    workflow.add_node("review", feedback_review_node)
    workflow.set_entry_point("writer")
    workflow.add_edge("writer", "review")
    workflow.add_conditional_edges("review", route_after_review)
    return workflow.compile(checkpointer=MemorySaver())


def demo_feedback_loop() -> None:
    """Run the feedback loop with simulated human feedback."""
    print("\n\n=== Part 2: Feedback Loop ===")
    agent = build_feedback_graph()
    config = {"configurable": {"thread_id": "feedback-demo"}}

    task = "Write a brief summary of what RAG (Retrieval-Augmented Generation) is."
    print(f"Task: {task}")

    # First invocation — graph runs until review interrupt()
    agent.invoke({"messages": [HumanMessage(content=task)]}, config)

    # Simulate human feedback requesting a revision
    print("\n  [Simulating feedback: 'Make it more concise and add bullet points']")
    agent.invoke(Command(resume="Make it more concise and add bullet points."), config)

    # Approve the revision
    print("\n  [Simulating approval: empty string = approve]")
    final = agent.invoke(Command(resume=""), config)
    print(f"\n  Final output:\n{final['messages'][-1].content}")


if __name__ == "__main__":
    print("=== HUMAN-IN-THE-LOOP DEMO (LangGraph) ===")

    demo_approval_gate()
    demo_feedback_loop()

    print("\n--- LangGraph interrupt() vs old pattern ---")
    print("  Old: while loop with input() blocking; state not preserved across process restarts")
    print("  New: interrupt() pauses the graph; state survives in MemorySaver/DB")
    print("       human can respond hours later; resume with Command(resume=...)")

    print("\n--- When to use Human-in-the-Loop ---")
    approval_triggers = [
        ("Irreversible actions", "delete, send, deploy, payment"),
        ("Low confidence", "agent confidence score < threshold"),
        ("High stakes", "financial, medical, legal decisions"),
        ("New action type", "first time agent tries something new"),
        ("Policy violation", "output flagged by guardrails"),
    ]
    for trigger, example in approval_triggers:
        print(f"  {trigger:<25} → {example}")
