"""
Semantic Memory (Key-Value Fact Store)
Stores discrete facts about users, entities, and the world.
Supports TTL (time-to-live) so stale facts expire automatically.

Semantic memory = "things the agent knows as facts"
Examples: user name, preferences, entity attributes, domain knowledge.

Different from long-term memory: queried by exact key, not semantic similarity.
Different from episodic: stores facts, not events.

Run: python 02_agentic_core/memory/semantic.py
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))


class SemanticMemory:
    """
    Key-value store for facts with optional TTL.
    Facts are namespaced: store("user:name", "Alex") keeps things organized.
    """

    def __init__(self):
        self._store: dict[str, dict] = {}

    def store(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a fact. Set ttl_seconds to make it expire."""
        expires_at = None
        if ttl_seconds is not None:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()
        self._store[key] = {
            "value": value,
            "stored_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a fact. Returns default if not found or expired."""
        if key not in self._store:
            return default
        entry = self._store[key]
        if entry["expires_at"] and datetime.fromisoformat(entry["expires_at"]) < datetime.utcnow():
            del self._store[key]
            return default
        return entry["value"]

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def keys_with_prefix(self, prefix: str) -> list[str]:
        return [k for k in self._store if k.startswith(prefix)]

    def get_namespace(self, prefix: str) -> dict[str, Any]:
        """Get all non-expired facts with a given prefix."""
        return {k: self.get(k) for k in self.keys_with_prefix(prefix) if self.get(k) is not None}

    def purge_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        now = datetime.utcnow()
        expired = [
            k for k, v in self._store.items()
            if v["expires_at"] and datetime.fromisoformat(v["expires_at"]) < now
        ]
        for k in expired:
            del self._store[k]
        return len(expired)

    def count(self) -> int:
        self.purge_expired()
        return len(self._store)

    def dump(self) -> dict:
        return dict(self._store)


if __name__ == "__main__":
    print("=== SEMANTIC MEMORY DEMO ===\n")

    mem = SemanticMemory()

    # Store facts about a user
    mem.store("user:name", "Alex")
    mem.store("user:role", "Senior Backend Engineer")
    mem.store("user:preferred_language", "Python")
    mem.store("user:company", "Stealth AI Startup")

    # Store agent working state with TTL
    mem.store("session:current_task", "Interview prep for agentic AI role", ttl_seconds=3600)
    mem.store("session:last_topic", "Chunking strategies", ttl_seconds=1800)

    # Store temporary rate-limiting info
    mem.store("rate_limit:openai_calls_today", 47, ttl_seconds=86400)

    # Store tool output cache
    mem.store("cache:weather_nyc", "72°F, partly cloudy", ttl_seconds=3600)

    print(f"Stored {mem.count()} facts\n")
    print("=" * 60)

    print("\n--- Exact key lookups ---")
    print(f"  user:name                = {mem.get('user:name')}")
    print(f"  user:preferred_language  = {mem.get('user:preferred_language')}")
    print(f"  nonexistent:key          = {mem.get('nonexistent:key', '[not found]')}")

    print("\n--- Namespace queries ---")
    user_facts = mem.get_namespace("user:")
    print("  user: namespace:")
    for k, v in user_facts.items():
        print(f"    {k:<35} = {v}")

    session_facts = mem.get_namespace("session:")
    print("  session: namespace:")
    for k, v in session_facts.items():
        print(f"    {k:<35} = {v}")

    print("\n--- TTL Demo (simulate expired entry) ---")
    mem.store("temp:api_key_test", "sk-test-xxx", ttl_seconds=0)  # expires immediately
    import time; time.sleep(0.01)
    result = mem.get("temp:api_key_test", "[expired]")
    print(f"  temp:api_key_test after expiry: {result}")

    removed = mem.purge_expired()
    print(f"  Purged {removed} expired entries")

    print("\n--- Practical Agent Usage ---")
    print("  On each agent turn:")
    print("  1. Load relevant facts: user = mem.get_namespace('user:')")
    print("  2. Inject into system prompt: f'User name: {user[\"user:name\"]}'")
    print("  3. Update after learning: mem.store('user:timezone', 'PST')")
    print("  4. Cache tool results: mem.store('cache:query', result, ttl_seconds=300)")

    print("\n--- Types of Semantic Facts ---")
    types = [
        ("user:", "User identity, preferences, profile"),
        ("entity:", "Facts about companies, products, people"),
        ("config:", "Agent configuration and settings"),
        ("cache:", "Cached tool results with TTL"),
        ("session:", "Working memory for current task"),
        ("rate_limit:", "API usage tracking"),
    ]
    for prefix, desc in types:
        print(f"  {prefix:<15} {desc}")
