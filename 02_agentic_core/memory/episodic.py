"""
Episodic Memory
Records past agent runs as a JSON log, queryable by recency and keyword.
Answers the question: "What did I do the last time I worked on this?"

Episodic memory = structured diary of agent execution history.
Unlike long-term (semantic similarity), episodic is queried by time + metadata.

Run: python 02_agentic_core/memory/episodic.py
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

EPISODE_FILE = _root / "tmp_episodes.json"


class Episode:
    def __init__(
        self,
        task: str,
        steps: list[dict],
        outcome: str,
        success: bool,
        duration_seconds: float = 0.0,
        metadata: dict | None = None,
    ):
        self.id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.task = task
        self.steps = steps
        self.outcome = outcome
        self.success = success
        self.duration_seconds = duration_seconds
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "task": self.task,
            "steps": self.steps,
            "outcome": self.outcome,
            "success": self.success,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


class EpisodicMemory:
    """Stores and retrieves agent run history from a JSON file."""

    def __init__(self, filepath: Path = EPISODE_FILE):
        self._path = filepath
        self._episodes: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return []

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._episodes, indent=2))

    def record(self, episode: Episode) -> None:
        self._episodes.append(episode.to_dict())
        self._save()

    def get_recent(self, n: int = 5) -> list[dict]:
        return self._episodes[-n:]

    def search(self, keyword: str) -> list[dict]:
        kw = keyword.lower()
        return [
            ep for ep in self._episodes
            if kw in ep["task"].lower()
            or kw in ep["outcome"].lower()
            or any(kw in str(s).lower() for s in ep["steps"])
        ]

    def get_failures(self) -> list[dict]:
        return [ep for ep in self._episodes if not ep["success"]]

    def success_rate(self) -> float:
        if not self._episodes:
            return 0.0
        return sum(1 for ep in self._episodes if ep["success"]) / len(self._episodes)

    def count(self) -> int:
        return len(self._episodes)

    def clear(self) -> None:
        self._episodes = []
        if self._path.exists():
            self._path.unlink()


if __name__ == "__main__":
    print("=== EPISODIC MEMORY DEMO ===\n")

    mem = EpisodicMemory()
    mem.clear()

    # Simulate recording several past agent runs
    sample_episodes = [
        Episode(
            task="Calculate the quarterly revenue growth",
            steps=[
                {"tool": "calculator", "input": "1250000 / 1100000 - 1", "result": "0.136"},
                {"tool": "calculator", "input": "0.136 * 100", "result": "13.6"},
            ],
            outcome="Revenue grew 13.6% quarter-over-quarter",
            success=True,
            duration_seconds=2.3,
            metadata={"user": "alex", "domain": "finance"},
        ),
        Episode(
            task="Summarize the Q3 product roadmap document",
            steps=[
                {"tool": "web_search", "input": "Q3 roadmap", "result": "Error: document not found"},
            ],
            outcome="Failed — document not accessible via search",
            success=False,
            duration_seconds=5.1,
            metadata={"user": "alex", "domain": "product"},
        ),
        Episode(
            task="Find all Python dependencies newer than 6 months",
            steps=[
                {"tool": "code_exec", "input": "pip list --outdated", "result": "anthropic, pydantic, fastapi..."},
                {"tool": "calculator", "input": "len(['anthropic','pydantic','fastapi'])", "result": "3"},
            ],
            outcome="Found 3 packages with updates available",
            success=True,
            duration_seconds=8.7,
            metadata={"user": "alex", "domain": "devops"},
        ),
        Episode(
            task="Answer customer question about refund policy",
            steps=[
                {"tool": "web_search", "input": "refund policy site:docs.example.com", "result": "30-day no-questions-asked refund"},
                {"thought": "Policy is clear, can answer directly"},
            ],
            outcome="Answered: 30-day refund policy applies",
            success=True,
            duration_seconds=1.8,
            metadata={"user": "support_bot", "domain": "customer_service"},
        ),
    ]

    for ep in sample_episodes:
        mem.record(ep)

    print(f"Recorded {mem.count()} episodes\n")
    print("=" * 60)

    print("\n--- Recent episodes (last 3) ---")
    for ep in mem.get_recent(3):
        status = "✓" if ep["success"] else "✗"
        print(f"  {status} [{ep['id']}] {ep['task']}")
        print(f"    Outcome: {ep['outcome'][:70]}")

    print(f"\n--- Success rate: {mem.success_rate():.0%} ---")

    print("\n--- Search: 'calculator' ---")
    for ep in mem.search("calculator"):
        print(f"  [{ep['id']}] {ep['task']}")

    print("\n--- Failed episodes ---")
    for ep in mem.get_failures():
        print(f"  [{ep['id']}] {ep['task']}")
        print(f"    Why: {ep['outcome']}")

    # Cleanup
    mem.clear()
    print("\n(tmp episode file cleaned up)")

    print("\n--- Interview Answer ---")
    print("Episodic memory lets agents learn from past runs.")
    print("'Last time I tried this approach it failed — let me try differently.'")
    print("Useful for: debugging recurring failures, personalizing responses,")
    print("building audit trails, and reducing repeated mistakes.")
