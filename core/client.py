"""
Anthropic client singleton with prompt caching enabled by default.

Usage:
    from core.client import get_client, MODEL, FAST_MODEL, cached_system
    client = get_client()
    response = client.messages.create(model=MODEL, ...)
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# claude-sonnet-4-6 for agentic tasks; FAST_MODEL for cheap demos
MODEL = "claude-sonnet-4-6"
FAST_MODEL = "claude-haiku-4-5-20251001"

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        _client = Anthropic(api_key=api_key)
    return _client


def cached_system(text: str) -> list[dict]:
    """Wrap a system prompt with cache_control for prompt caching (5-min TTL).

    Reduces latency and cost when the same system prompt is reused across turns.
    Use on any system prompt longer than ~1000 tokens.
    """
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
