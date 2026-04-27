"""
Project 1 Tools
Concrete tools used by the tool-using agent:
  - calculator: safe expression evaluator
  - get_datetime: current UTC time
  - web_search: mock web search with realistic stubs
  - note_taking: write/read notes (simulates persistent memory)
"""
import sys
import json
import math
from pathlib import Path
from datetime import datetime, timezone

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

# Tool schemas for Claude's tools API
TOOL_SCHEMAS = [
    {
        "name": "calculator",
        "description": "Evaluate a math expression. Supports +, -, *, /, **, sqrt, log, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression, e.g. 'sqrt(144) + 2**8'",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_datetime",
        "description": "Returns the current UTC date, time, and day of week.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "web_search",
        "description": "Search the web for current information on a topic.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
    {
        "name": "note_taking",
        "description": "Write or read notes. Use to save important findings for later reference.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["write", "read", "list"],
                    "description": "'write' to save a note, 'read' to retrieve one, 'list' to see all notes",
                },
                "title": {"type": "string", "description": "Note title (required for write/read)"},
                "content": {"type": "string", "description": "Note content (required for write)"},
            },
            "required": ["action"],
        },
    },
]

# In-memory notes store (persists for the duration of the agent run)
_notes: dict[str, str] = {}


def execute_tool(name: str, tool_input: dict) -> str:
    if name == "calculator":
        try:
            safe = {"__builtins__": {}}
            math_ns = {k: v for k, v in vars(math).items() if not k.startswith("_")}
            result = eval(tool_input["expression"], safe, math_ns)
            return f"{tool_input['expression']} = {result}"
        except Exception as e:
            return f"Calculator error: {e}"

    elif name == "get_datetime":
        now = datetime.now(timezone.utc)
        return now.strftime("%A, %B %d %Y — %H:%M:%S UTC")

    elif name == "web_search":
        query = tool_input["query"]
        # Realistic mock responses for common queries
        mock_db = {
            "python": "Python is a high-level programming language. Latest version: 3.13.",
            "fastapi": "FastAPI is a modern Python web framework for building APIs. Version 0.115+.",
            "rag": "RAG (Retrieval-Augmented Generation) combines vector search with LLM generation.",
            "langchain": "LangChain is a framework for building LLM applications with chains and agents.",
            "savings": "High-yield savings accounts currently offer 4.5-5.0% APY (2024).",
        }
        for key, response in mock_db.items():
            if key in query.lower():
                return f"[Search: '{query}']\n{response}"
        return (
            f"[Search: '{query}']\n"
            f"1. Comprehensive overview of {query}\n"
            f"2. Recent developments: {query} has seen significant updates\n"
            f"3. Best practices for working with {query}"
        )

    elif name == "note_taking":
        action = tool_input["action"]
        if action == "write":
            title = tool_input.get("title", "untitled")
            content = tool_input.get("content", "")
            _notes[title] = content
            return f"Note '{title}' saved."
        elif action == "read":
            title = tool_input.get("title", "")
            if title in _notes:
                return f"Note '{title}':\n{_notes[title]}"
            return f"Note '{title}' not found. Available: {list(_notes.keys())}"
        elif action == "list":
            if not _notes:
                return "No notes saved yet."
            return "Notes: " + ", ".join(_notes.keys())

    return f"Unknown tool: {name}"
