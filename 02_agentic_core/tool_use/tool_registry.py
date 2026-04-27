"""
Tool Registry Pattern
Defines the Tool ABC (abstract base class) and ToolRegistry.

Why this pattern?
  - Decouples the LLM from specific API implementations
  - Lets you swap, mock, or version tools without changing agent code
  - Central registry enables discoverability and introspection
  - Standard interface means any tool works with any agent

Run: python 02_agentic_core/tool_use/tool_registry.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

import math
from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime, timezone


class Tool(ABC):
    """Base class for all tools. Implement name, description, input_schema, and run()."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def input_schema(self) -> dict: ...

    @abstractmethod
    def run(self, **kwargs) -> Any: ...

    def to_claude_schema(self) -> dict:
        """Convert to the format Claude's tool_use API expects."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def __repr__(self) -> str:
        return f"Tool(name={self.name!r})"


class ToolRegistry:
    """Central registry: register tools, look them up, call by name."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> "ToolRegistry":
        self._tools[tool.name] = tool
        return self  # fluent interface

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            available = list(self._tools.keys())
            raise KeyError(f"Tool '{name}' not found. Available: {available}")
        return self._tools[name]

    def call(self, name: str, **kwargs) -> Any:
        return self.get(name).run(**kwargs)

    def to_claude_tools(self) -> list[dict]:
        """Return all tools in the format expected by the Claude messages API."""
        return [t.to_claude_schema() for t in self._tools.values()]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def describe(self) -> None:
        print(f"Registry has {len(self._tools)} tools:")
        for name, tool in self._tools.items():
            print(f"  {name:<20} {tool.description[:60]}")


# ── Concrete tool implementations ────────────────────────────────────────────

class CalculatorTool(Tool):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluate a mathematical expression. Supports +, -, *, /, **, sqrt, etc."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g. '25 * 47 + 100'",
                }
            },
            "required": ["expression"],
        }

    def run(self, expression: str) -> str:
        try:
            result = eval(expression, {"__builtins__": {}}, vars(math))
            return str(result)
        except Exception as e:
            return f"Error evaluating '{expression}': {e}"


class DatetimeTool(Tool):
    @property
    def name(self) -> str:
        return "get_datetime"

    @property
    def description(self) -> str:
        return "Get the current date and time in UTC, including day of week."

    @property
    def input_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    def run(self) -> str:
        return datetime.now(timezone.utc).strftime("%A, %B %d %Y — %H:%M:%S UTC")


class MockWebSearchTool(Tool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for current information. Returns top 3 results."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        }

    def run(self, query: str) -> str:
        return (
            f"[MOCK SEARCH RESULTS for '{query}']\n"
            f"1. Result A: Comprehensive overview of {query} — key facts and context\n"
            f"2. Result B: Recent developments related to {query}\n"
            f"3. Result C: Expert analysis of {query} with examples"
        )


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(DatetimeTool())
    registry.register(MockWebSearchTool())
    return registry


if __name__ == "__main__":
    print("=== TOOL REGISTRY DEMO ===\n")

    registry = build_default_registry()
    registry.describe()

    print("\n--- Calling tools directly ---")
    print(f"calculator('25 * 47')  = {registry.call('calculator', expression='25 * 47')}")
    print(f"get_datetime()         = {registry.call('get_datetime')}")
    print(f"web_search(...)        = {registry.call('web_search', query='RAG systems')[:80]}...")

    print("\n--- Claude-compatible tool schemas ---")
    import json
    for schema in registry.to_claude_tools():
        print(f"\n{schema['name']}:")
        print(f"  Description: {schema['description']}")
        print(f"  Schema: {json.dumps(schema['input_schema'], indent=2)[:120]}")

    print("\n--- Error handling: unknown tool ---")
    try:
        registry.call("nonexistent_tool")
    except KeyError as e:
        print(f"  KeyError: {e}")
