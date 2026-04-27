"""
Sample Tools Library
A richer set of demo tools: calculator, datetime, unit converter, word counter.
Shows how to write tools with input validation and error handling.

Run: python 02_agentic_core/tool_use/sample_tools.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).parent))

import math
import json
from datetime import datetime, timezone
from tool_registry import Tool, ToolRegistry


class CalculatorTool(Tool):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluate a math expression. Supports basic arithmetic, sqrt, pow, trig functions."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "e.g. '(2 + 3) * sqrt(16)'"}
            },
            "required": ["expression"],
        }

    def run(self, expression: str) -> str:
        safe_globals = {"__builtins__": {}}
        safe_locals = {k: v for k, v in vars(math).items() if not k.startswith("_")}
        try:
            result = eval(expression, safe_globals, safe_locals)
            return f"{result}"
        except ZeroDivisionError:
            return "Error: division by zero"
        except Exception as e:
            return f"Error: {e}"


class DatetimeTool(Tool):
    @property
    def name(self) -> str:
        return "get_datetime"

    @property
    def description(self) -> str:
        return "Returns the current UTC date, time, and day of week."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Optional strftime format string",
                    "default": "%A, %B %d %Y — %H:%M:%S UTC",
                }
            },
            "required": [],
        }

    def run(self, format: str = "%A, %B %d %Y — %H:%M:%S UTC") -> str:
        return datetime.now(timezone.utc).strftime(format)


class UnitConverterTool(Tool):
    CONVERSIONS = {
        ("km", "miles"): 0.621371,
        ("miles", "km"): 1.60934,
        ("kg", "lbs"): 2.20462,
        ("lbs", "kg"): 0.453592,
        ("celsius", "fahrenheit"): None,  # handled specially
        ("fahrenheit", "celsius"): None,
    }

    @property
    def name(self) -> str:
        return "unit_converter"

    @property
    def description(self) -> str:
        return "Convert between units. Supports: km/miles, kg/lbs, celsius/fahrenheit."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {"type": "number", "description": "Numeric value to convert"},
                "from_unit": {"type": "string", "description": "Source unit"},
                "to_unit": {"type": "string", "description": "Target unit"},
            },
            "required": ["value", "from_unit", "to_unit"],
        }

    def run(self, value: float, from_unit: str, to_unit: str) -> str:
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        key = (from_unit, to_unit)
        if key == ("celsius", "fahrenheit"):
            result = value * 9 / 5 + 32
        elif key == ("fahrenheit", "celsius"):
            result = (value - 32) * 5 / 9
        elif key in self.CONVERSIONS:
            result = value * self.CONVERSIONS[key]
        else:
            return f"Unknown conversion: {from_unit} → {to_unit}"
        return f"{value} {from_unit} = {result:.4f} {to_unit}"


class WordCountTool(Tool):
    @property
    def name(self) -> str:
        return "word_count"

    @property
    def description(self) -> str:
        return "Count words, characters, and sentences in a text string."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"}
            },
            "required": ["text"],
        }

    def run(self, text: str) -> str:
        import re
        words = len(text.split())
        chars = len(text)
        sentences = len(re.split(r"[.!?]+", text.strip())) - 1
        return json.dumps({"words": words, "characters": chars, "sentences": sentences})


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(DatetimeTool())
    registry.register(UnitConverterTool())
    registry.register(WordCountTool())
    return registry


if __name__ == "__main__":
    print("=== SAMPLE TOOLS DEMO ===\n")
    registry = build_registry()
    registry.describe()

    test_cases = [
        ("calculator", {"expression": "sqrt(144) + 2**8"}),
        ("get_datetime", {}),
        ("unit_converter", {"value": 100, "from_unit": "km", "to_unit": "miles"}),
        ("unit_converter", {"value": 37, "from_unit": "celsius", "to_unit": "fahrenheit"}),
        ("word_count", {"text": "The quick brown fox jumps over the lazy dog. Twice."}),
    ]

    print("\n--- Test Results ---")
    for tool_name, kwargs in test_cases:
        result = registry.call(tool_name, **kwargs)
        args_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        print(f"  {tool_name}({args_str})")
        print(f"  → {result}\n")
