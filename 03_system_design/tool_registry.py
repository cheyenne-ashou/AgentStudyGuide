"""
Central Tool Registry (System Design Level)
Extended version with: versioning, access control tags, metadata, and discovery.

At the system design level, the tool registry is a service:
  - Agents discover available tools at runtime
  - Tools can be versioned (v1, v2) for backwards compatibility
  - Access control: some tools require elevated permissions
  - Metrics: track which tools are called most

Run: python 03_system_design/tool_registry.py
"""
import sys
import time
import math
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.logger import get_logger

log = get_logger(__name__)


@dataclass
class ToolMetadata:
    name: str
    version: str = "1.0"
    description: str = ""
    category: str = "general"
    requires_permission: str | None = None  # None = public, "admin" = admin only
    rate_limit_per_minute: int = 60
    tags: list[str] = field(default_factory=list)


class Tool(ABC):
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata: ...

    @property
    @abstractmethod
    def input_schema(self) -> dict: ...

    @abstractmethod
    def run(self, **kwargs) -> Any: ...

    def to_claude_schema(self) -> dict:
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "input_schema": self.input_schema,
        }


class CentralToolRegistry:
    """
    System-level tool registry with versioning, permissions, and call metrics.
    """

    def __init__(self):
        self._tools: dict[str, dict[str, Tool]] = {}  # name → {version → tool}
        self._call_counts: dict[str, int] = {}
        self._call_times_ms: dict[str, list[float]] = {}

    def register(self, tool: Tool) -> None:
        name = tool.metadata.name
        version = tool.metadata.version
        if name not in self._tools:
            self._tools[name] = {}
        self._tools[name][version] = tool
        self._call_counts[f"{name}@{version}"] = 0
        log.info("registry.register", tool=name, version=version)

    def get(self, name: str, version: str = "latest") -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found. Available: {list(self._tools)}")
        versions = self._tools[name]
        if version == "latest":
            version = sorted(versions.keys())[-1]
        if version not in versions:
            raise KeyError(f"Tool '{name}' version '{version}' not found.")
        return versions[version]

    def call(self, name: str, caller_permission: str = "public", version: str = "latest", **kwargs) -> Any:
        tool = self.get(name, version)
        meta = tool.metadata

        # Permission check
        if meta.requires_permission and caller_permission != meta.requires_permission:
            raise PermissionError(
                f"Tool '{name}' requires '{meta.requires_permission}' permission. "
                f"Caller has '{caller_permission}'."
            )

        key = f"{name}@{meta.version}"
        start = time.perf_counter()
        result = tool.run(**kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        self._call_counts[key] = self._call_counts.get(key, 0) + 1
        self._call_times_ms.setdefault(key, []).append(elapsed_ms)

        log.info("registry.call", tool=name, version=meta.version, duration_ms=round(elapsed_ms))
        return result

    def discover(self, category: str | None = None, tags: list[str] | None = None) -> list[ToolMetadata]:
        """Return metadata for all tools matching filters — for dynamic agent discovery."""
        results = []
        for name, versions in self._tools.items():
            latest = self.get(name)
            meta = latest.metadata
            if category and meta.category != category:
                continue
            if tags and not any(t in meta.tags for t in tags):
                continue
            results.append(meta)
        return results

    def to_claude_tools(self, caller_permission: str = "public") -> list[dict]:
        result = []
        for name in self._tools:
            tool = self.get(name)
            if tool.metadata.requires_permission and caller_permission != tool.metadata.requires_permission:
                continue  # Don't expose restricted tools to this caller
            result.append(tool.to_claude_schema())
        return result

    def stats(self) -> dict:
        return {
            key: {
                "calls": count,
                "avg_ms": sum(self._call_times_ms.get(key, [0])) / max(len(self._call_times_ms.get(key, [1])), 1),
            }
            for key, count in self._call_counts.items()
            if count > 0
        }


# ── Example tools ─────────────────────────────────────────────────────────────

class CalculatorV1(Tool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="calculator", version="1.0",
            description="Evaluate math expressions",
            category="math", tags=["arithmetic", "compute"],
        )

    @property
    def input_schema(self) -> dict:
        return {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}

    def run(self, expression: str) -> str:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return str(result)


class AdminReportTool(Tool):
    """Admin-only tool — demonstrates access control."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="admin_report", version="1.0",
            description="Generate internal usage report (admin only)",
            category="admin", requires_permission="admin", tags=["internal"],
        )

    @property
    def input_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    def run(self) -> str:
        return "Internal report: 1,247 agent calls today, 3 failures, $0.47 cost"


if __name__ == "__main__":
    print("=== CENTRAL TOOL REGISTRY DEMO ===\n")

    registry = CentralToolRegistry()
    registry.register(CalculatorV1())
    registry.register(AdminReportTool())

    # Make some calls
    for _ in range(3):
        result = registry.call("calculator", expression="100 * 1.15")
    print(f"Calculator called 3 times: last result = {result}")

    # Permission check
    print("\n--- Access Control ---")
    try:
        registry.call("admin_report", caller_permission="public")
    except PermissionError as e:
        print(f"  Public caller blocked: {e}")

    result = registry.call("admin_report", caller_permission="admin")
    print(f"  Admin caller allowed: {result}")

    # Tool discovery
    print("\n--- Tool Discovery (agents call this dynamically) ---")
    all_tools = registry.discover()
    for meta in all_tools:
        perm = f" [{meta.requires_permission}]" if meta.requires_permission else ""
        print(f"  {meta.name} v{meta.version} [{meta.category}]{perm} — {meta.description}")

    # Claude-compatible schemas
    print("\n--- Tools visible to a public caller ---")
    public_tools = registry.to_claude_tools(caller_permission="public")
    print(f"  {len(public_tools)} tool(s) exposed: {[t['name'] for t in public_tools]}")

    # Usage stats
    print("\n--- Usage Stats ---")
    for key, data in registry.stats().items():
        print(f"  {key:<25} calls={data['calls']}, avg_ms={data['avg_ms']:.2f}")
