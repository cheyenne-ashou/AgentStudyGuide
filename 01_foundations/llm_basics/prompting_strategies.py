"""
Prompting Strategies Demo
Runs the same math word problem through four prompting styles using LCEL chains:
zero-shot, few-shot, chain-of-thought, and ReAct.

Key insight: CoT and ReAct consistently outperform zero-shot on multi-step problems
because they force intermediate reasoning before committing to an answer.

LangGraph concept: LCEL (LangChain Expression Language) chains use the | operator
to compose prompt templates, LLMs, and output parsers into a single Runnable.

Run: python 01_foundations/llm_basics/prompting_strategies.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.client import get_fast_llm

TASK = (
    "A store sells apples for $0.50 each and bananas for $0.30 each. "
    "I buy 6 apples and 4 bananas. How much do I spend in total?"
)

parser = StrOutputParser()


def zero_shot() -> str:
    # Simplest chain: prompt | llm | parser
    chain = ChatPromptTemplate.from_messages([
        ("human", "{task}"),
    ]) | get_fast_llm() | parser
    return chain.invoke({"task": TASK})


def few_shot() -> str:
    # Examples are baked into the template — the model learns the pattern
    template = (
        "Q: Pens cost $1.00 each. I buy 3. Total?\n"
        "A: 3 × $1.00 = $3.00\n\n"
        "Q: Oranges cost $0.75 each. I buy 4. Total?\n"
        "A: 4 × $0.75 = $3.00\n\n"
        "Q: {task}\n"
        "A:"
    )
    chain = ChatPromptTemplate.from_messages([
        ("human", template),
    ]) | get_fast_llm() | parser
    return chain.invoke({"task": TASK})


def chain_of_thought() -> str:
    # "Let's think step by step" triggers intermediate reasoning before the answer
    chain = ChatPromptTemplate.from_messages([
        ("human", "{task}\n\nLet's think step by step."),
    ]) | get_fast_llm() | parser
    return chain.invoke({"task": TASK})


def react_style() -> str:
    # ReAct format: Thought → Action → Observation → Final Answer
    template = (
        "{task}\n\n"
        "Use this format:\n"
        "Thought: what do I need to figure out?\n"
        "Action: [calculation]\n"
        "Observation: [result]\n"
        "(repeat Thought/Action/Observation as needed)\n"
        "Final Answer: [total with $ sign]"
    )
    chain = ChatPromptTemplate.from_messages([
        ("human", template),
    ]) | get_fast_llm() | parser
    return chain.invoke({"task": TASK})


if __name__ == "__main__":
    print("=== PROMPTING STRATEGIES DEMO (LCEL) ===")
    print(f"\nTask: {TASK}\n")
    print("=" * 60)

    for label, fn in [
        ("ZERO-SHOT", zero_shot),
        ("FEW-SHOT", few_shot),
        ("CHAIN-OF-THOUGHT", chain_of_thought),
        ("ReAct", react_style),
    ]:
        print(f"\n--- {label} ---")
        print(fn())

    print("\n--- LCEL Pattern ---")
    print("  chain = prompt_template | llm | StrOutputParser()")
    print("  chain.invoke({'task': TASK})  ← same interface for all 4 strategies")
    print("  The | operator composes Runnables — each passes its output to the next.")

    print("\n--- Interview Takeaway ---")
    print("CoT/ReAct force the model to show reasoning before committing.")
    print("This reduces errors on multi-step problems by ~30-50%.")
    print("ReAct is the foundation of all LangGraph agent graphs.")
