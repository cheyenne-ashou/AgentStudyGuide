"""
Short-Term Memory with LangGraph MemorySaver
Demonstrates LangGraph's built-in checkpointing as the production-grade
replacement for hand-rolled rolling-window and summarization patterns.

MemorySaver persists the full message history keyed by thread_id.
Each call with the same thread_id automatically continues the conversation.

Interview question: "How do you handle a long conversation that exceeds the context window?"
Answer: LangGraph's MemorySaver handles persistence. For large histories, add
a summarization node that condenses old messages before they overflow the window.
Rolling window and summarization remain valid conceptual strategies — MemorySaver
implements rolling append by default.

Run: python 02_agentic_core/memory/short_term.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from core.client import get_llm


def demo_memorysaver_persistence() -> None:
    """
    MemorySaver stores the full message list after each graph invocation.
    The same thread_id retrieves and continues the conversation seamlessly.
    """
    memory = MemorySaver()
    agent = create_react_agent(get_llm(), tools=[], checkpointer=memory)

    # thread_id is the session identifier — think of it as a conversation ID
    config = {"configurable": {"thread_id": "session-demo"}}

    print("--- MemorySaver: persistent conversation across invocations ---\n")

    # Turn 1
    result = agent.invoke(
        {"messages": [HumanMessage(content="My name is Alex and I'm learning LangGraph.")]},
        config,
    )
    print(f"Turn 1 response: {result['messages'][-1].content[:150]}")

    # Turn 2 — MemorySaver automatically supplies the prior history
    result = agent.invoke(
        {"messages": [HumanMessage(content="What did I tell you about myself?")]},
        config,
    )
    print(f"Turn 2 response: {result['messages'][-1].content[:200]}")

    # Inspect the full state — MemorySaver keeps every message
    state = agent.get_state(config)
    print(f"\nTotal messages in memory: {len(state.values['messages'])}")
    print("(MemorySaver has the full history — no manual list management needed)")


def explain_rolling_window_concept() -> None:
    """
    Rolling window and summarization are still valid conceptual strategies
    for production systems with very long conversations.
    """
    print("\n--- Rolling Window (conceptual — still relevant) ---")
    print("  Strategy: keep only the last N message pairs, drop the oldest")
    print("  Pro: O(1) memory, fast, no API cost")
    print("  Con: early context is permanently lost")
    print("  LangGraph equivalent: add a 'trim_messages' node before the agent node")
    print("    that calls trim_messages(messages, max_tokens=4096)")

    print("\n--- Summarization (conceptual) ---")
    print("  Strategy: when history fills, ask LLM to compress old messages into a summary")
    print("  Pro: preserves meaning at low token cost")
    print("  Con: costs an extra LLM call; loses exact quotes")
    print("  LangGraph equivalent: conditional node that triggers summarization when")
    print("    len(messages) > threshold, then replaces old messages with a summary message")

    print("\n--- Hybrid (most common in production) ---")
    print("  Rolling window + periodic summarization")
    print("  thread_id per user session (MemorySaver / SqliteSaver / RedisSaver)")


if __name__ == "__main__":
    print("=== SHORT-TERM MEMORY DEMO (MemorySaver) ===\n")

    demo_memorysaver_persistence()
    explain_rolling_window_concept()

    print("\n--- Interview Answer ---")
    print("  LangGraph: MemorySaver (dev) or SqliteSaver/RedisSaver (prod) persist")
    print("  conversation state keyed by thread_id across invocations.")
    print("  For overflow: add a summarization node or use trim_messages().")
    print("  Rolling window: fast, loses old context.")
    print("  Summarization: preserves meaning, costs an extra LLM call.")
