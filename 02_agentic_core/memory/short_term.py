"""
Short-Term Memory (Context Window Management)
Demonstrates two strategies for managing the context window:
  1. Rolling window — keep last N messages, drop the oldest
  2. Summarization — compress old messages into a summary when window fills

Short-term memory = the messages list you pass to the API.
It disappears when the process ends. The challenge is managing its size.

Interview question: "How do you handle a long conversation that exceeds the context window?"
Answer: rolling window (fast, loses old details) or summarization (slower, preserves meaning).

Run: python 02_agentic_core/memory/short_term.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, FAST_MODEL


class RollingWindowMemory:
    """Keep only the last N message pairs (user+assistant)."""

    def __init__(self, max_pairs: int = 3, system_prompt: str = ""):
        self.max_pairs = max_pairs
        self.system_prompt = system_prompt
        self._messages: list[dict] = []

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})
        # Trim to keep at most max_pairs complete pairs (2 messages each)
        max_messages = self.max_pairs * 2
        if len(self._messages) > max_messages:
            # Always drop from the front to preserve recency
            self._messages = self._messages[-max_messages:]

    def get_messages(self) -> list[dict]:
        return list(self._messages)

    def stats(self) -> dict:
        return {
            "total_messages": len(self._messages),
            "approx_tokens": sum(len(m["content"].split()) * 1.3 for m in self._messages),
        }


class SummarizingMemory:
    """Summarize old messages when history grows beyond a threshold."""

    def __init__(self, max_messages: int = 6, system_prompt: str = ""):
        self.max_messages = max_messages
        self.system_prompt = system_prompt
        self._messages: list[dict] = []
        self._summary: str = ""
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = get_client()
        return self._client

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})
        if len(self._messages) > self.max_messages:
            self._compress()

    def _compress(self) -> None:
        # Summarize the oldest half of the messages
        cutoff = len(self._messages) // 2
        old_messages = self._messages[:cutoff]
        self._messages = self._messages[cutoff:]

        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in old_messages
        )
        if self._summary:
            history_text = f"Previous summary: {self._summary}\n\n{history_text}"

        response = self._get_client().messages.create(
            model=FAST_MODEL,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"Summarize this conversation in 2-3 sentences, preserving key facts:\n\n{history_text}",
            }],
        )
        self._summary = response.content[0].text.strip()
        print(f"  [Memory compressed. New summary: {self._summary[:80]}...]")

    def get_messages(self) -> list[dict]:
        """Inject summary as the first message if one exists."""
        if not self._summary:
            return list(self._messages)
        summary_message = {
            "role": "user",
            "content": f"[Conversation history summary: {self._summary}]",
        }
        # Insert a placeholder assistant ack so messages alternate properly
        ack = {"role": "assistant", "content": "Understood, I have the context."}
        return [summary_message, ack] + list(self._messages)

    def stats(self) -> dict:
        return {
            "active_messages": len(self._messages),
            "has_summary": bool(self._summary),
            "summary_preview": self._summary[:60] if self._summary else "none",
        }


if __name__ == "__main__":
    print("=== SHORT-TERM MEMORY DEMO ===\n")

    # ── Rolling window demo ──────────────────────────────────────────────────
    print("--- Rolling Window (max 3 pairs) ---")
    mem = RollingWindowMemory(max_pairs=3)
    conversation = [
        ("user", "My name is Alex and I work at a startup."),
        ("assistant", "Nice to meet you, Alex!"),
        ("user", "We're building a RAG system in Python."),
        ("assistant", "Great choice, Python has excellent tooling for that."),
        ("user", "We use FastAPI for the backend."),
        ("assistant", "FastAPI is excellent for async workloads."),
        ("user", "What did I say my name was?"),  # should still be in window
        ("assistant", "You said your name is Alex."),
        ("user", "What company do I work at?"),  # may have been dropped
    ]
    for role, content in conversation:
        mem.add(role, content)
        if role == "user":
            print(f"  After adding: {mem.stats()}")

    print(f"\n  Final messages in window: {len(mem.get_messages())}")
    print(f"  First message: {mem.get_messages()[0]['content'][:60]}")
    print(f"  Warning: early context is DROPPED in rolling window!")

    # ── Summarizing demo (simulated without calling API for speed) ───────────
    print("\n--- Summarizing Memory (concept) ---")
    print("  When window fills:")
    print("  1. Take oldest N/2 messages")
    print("  2. Ask LLM: 'Summarize this conversation in 2-3 sentences'")
    print("  3. Store summary, discard raw messages")
    print("  4. Inject summary as context at the start of remaining messages")
    print("  Tradeoff: preserves meaning, but loses exact quotes and loses ordering of facts")

    print("\n--- Interview Answer ---")
    print("  Rolling window: O(1) time, O(N) space, fast, loses old details")
    print("  Summarization: O(API call) time, much smaller space, preserves meaning")
    print("  Hybrid: rolling window + periodic summarization is most common in production")
