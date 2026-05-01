"""
LangChain/LangGraph client setup.

Usage:
    from core.client import get_llm, get_fast_llm, MODEL, FAST_MODEL
    llm = get_llm()
    response = llm.invoke([HumanMessage(content="Hello")])
"""
import os
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

# claude-sonnet-4-6 for agentic tasks; FAST_MODEL for cheap demos
MODEL = "claude-sonnet-4-6"
FAST_MODEL = "claude-haiku-4-5-20251001"

_llm: ChatAnthropic | None = None
_fast_llm: ChatAnthropic | None = None


def get_llm(temperature: float = 0.0) -> ChatAnthropic:
    """Return a singleton ChatAnthropic instance for the primary model."""
    global _llm
    if _llm is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        _llm = ChatAnthropic(model=MODEL, temperature=temperature, api_key=api_key)
    return _llm


def get_fast_llm(temperature: float = 0.7) -> ChatAnthropic:
    """Return a singleton ChatAnthropic instance for the fast/cheap model."""
    global _fast_llm
    if _fast_llm is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        _fast_llm = ChatAnthropic(model=FAST_MODEL, temperature=temperature, api_key=api_key)
    return _fast_llm


# Backwards-compatible alias — prefer get_llm() in new code
def get_client() -> ChatAnthropic:
    return get_llm()
