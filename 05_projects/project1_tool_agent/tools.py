"""
Project 1 Tools
Concrete tools used by the tool-using agent, defined with @tool decorator:
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

from langchain_core.tools import tool

# In-memory notes store (persists for the duration of the agent run)
_notes: dict[str, str] = {}


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Supports +, -, *, /, **, sqrt, log, etc."""
    try:
        safe = {"__builtins__": {}}
        math_ns = {k: v for k, v in vars(math).items() if not k.startswith("_")}
        result = eval(expression, safe, math_ns)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculator error: {e}"


@tool
def get_datetime() -> str:
    """Returns the current UTC date, time, and day of week."""
    now = datetime.now(timezone.utc)
    return now.strftime("%A, %B %d %Y — %H:%M:%S UTC")


@tool
def web_search(query: str) -> str:
    """Search the web for current information on a topic."""
    mock_db = {
        "python": "Python is a high-level programming language. Latest version: 3.13.",
        "fastapi": "FastAPI is a modern Python web framework for building APIs. Version 0.115+.",
        "rag": "RAG (Retrieval-Augmented Generation) combines vector search with LLM generation.",
        "langgraph": "LangGraph is a framework for building stateful, graph-based AI agents.",
        "langchain": "LangChain provides the Runnable interface, LCEL, and tool abstractions for LLMs.",
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


@tool
def note_taking(action: str, title: str = "", content: str = "") -> str:
    """Write or read notes. Use to save important findings for later reference.

    action: 'write' to save a note, 'read' to retrieve one, 'list' to see all notes
    title: note title (required for write/read)
    content: note content (required for write)
    """
    if action == "write":
        if not title:
            return "Error: title is required for write action"
        _notes[title] = content
        return f"Note '{title}' saved."
    elif action == "read":
        if title in _notes:
            return f"Note '{title}':\n{_notes[title]}"
        return f"Note '{title}' not found. Available: {list(_notes.keys())}"
    elif action == "list":
        if not _notes:
            return "No notes saved yet."
        return "Notes: " + ", ".join(_notes.keys())
    return f"Unknown action: {action}. Use: write, read, list"


TOOLS = [calculator, get_datetime, web_search, note_taking]
