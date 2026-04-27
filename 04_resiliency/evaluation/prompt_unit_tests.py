"""
Prompt Unit Tests
pytest-style tests that assert LLM behavior matches expectations.
Run: pytest 04_resiliency/evaluation/ -v

Key insight: you can't unit test the LLM, but you CAN:
  - Assert output contains expected keywords
  - Assert output length is in a reasonable range
  - Assert output matches a schema
  - Assert the agent calls the right tool for a given query
  - Use LLM-as-judge to evaluate free-form answers against criteria
"""
import sys
import json
import pytest
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, FAST_MODEL


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    return get_client()


def llm_respond(client, prompt: str, max_tokens: int = 200) -> str:
    response = client.messages.create(
        model=FAST_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ── Keyword assertion tests ───────────────────────────────────────────────────

class TestRAGDefinition:
    def test_contains_retrieval_keyword(self, client):
        response = llm_respond(client, "In one sentence, what is RAG?")
        assert any(kw in response.lower() for kw in ["retrieval", "retrieve", "retrieved"])

    def test_contains_generation_keyword(self, client):
        response = llm_respond(client, "In one sentence, what is RAG?")
        assert any(kw in response.lower() for kw in ["generat", "augment"])

    def test_response_is_concise(self, client):
        response = llm_respond(client, "In one sentence, what is RAG?")
        word_count = len(response.split())
        assert 5 <= word_count <= 50, f"Expected 5-50 words, got {word_count}"


class TestHallucinationMitigation:
    def test_acknowledges_uncertainty_about_fake_entity(self, client):
        response = llm_respond(
            client,
            "What are the main products of Zylantrix Corp? "
            "If you don't know, say so explicitly.",
        )
        uncertainty_phrases = [
            "don't know", "not aware", "no information", "cannot find",
            "fictional", "doesn't exist", "i'm not", "unfamiliar",
        ]
        assert any(phrase in response.lower() for phrase in uncertainty_phrases), (
            f"Expected uncertainty phrase, got: {response[:200]}"
        )


class TestStructuredOutput:
    def test_json_output_is_parseable(self, client):
        response = llm_respond(
            client,
            'Respond with ONLY a JSON object with keys "name" and "value". '
            'Set name="test" and value=42.',
            max_tokens=100,
        )
        # Extract JSON
        start = response.find("{")
        end = response.rfind("}") + 1
        assert start != -1, f"No JSON found in: {response}"
        data = json.loads(response[start:end])
        assert "name" in data
        assert "value" in data

    def test_sentiment_is_valid_category(self, client):
        response = llm_respond(
            client,
            "Reply with ONLY one word: the sentiment of 'This is great!' "
            "Choose from: positive, negative, neutral.",
        )
        cleaned = response.strip().lower().rstrip(".")
        assert cleaned in {"positive", "negative", "neutral"}, f"Got: {cleaned!r}"


class TestToolSelection:
    def test_recommends_calculator_for_math(self, client):
        response = llm_respond(
            client,
            "Available tools: calculator, web_search, get_datetime. "
            "Which single tool should I use to compute 847 * 23? "
            "Reply with the tool name only.",
        )
        assert "calculator" in response.lower()

    def test_recommends_search_for_current_info(self, client):
        response = llm_respond(
            client,
            "Available tools: calculator, web_search, get_datetime. "
            "Which single tool should I use to find today's stock price of Apple? "
            "Reply with the tool name only.",
        )
        assert "search" in response.lower()


# ── LLM-as-judge ─────────────────────────────────────────────────────────────

class TestLLMAsJudge:
    def test_answer_addresses_question(self, client):
        question = "What are the main differences between RAG and fine-tuning?"
        answer = llm_respond(client, question, max_tokens=300)

        judgment = llm_respond(
            client,
            f"Question: {question}\n"
            f"Answer: {answer}\n\n"
            "Does the answer directly address the question? "
            "Reply with ONLY 'yes' or 'no'.",
            max_tokens=5,
        )
        assert "yes" in judgment.lower(), f"Judge said no. Answer was: {answer[:200]}"
