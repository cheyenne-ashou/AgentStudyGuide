# Agentic AI Interview Prep (LangGraph Edition)

Runnable Python demos for every concept in the study guide, built with **LangGraph** and **langchain-anthropic**.
Each file has a `__main__` block — run it, read the output, understand the concept.

## Setup

```bash
# 1. Python 3.11+
python --version

# 2. Install dependencies (LangGraph + LangChain + Anthropic)
pip install -e .

# 3. Set your API key (used by langchain-anthropic)
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...
```

## Old API → LangGraph Quick Reference

| Raw Anthropic SDK | LangGraph / LangChain |
|---|---|
| `from anthropic import Anthropic` | `from langchain_anthropic import ChatAnthropic` |
| `get_client()` | `get_llm()` / `get_fast_llm()` |
| `client.messages.create(...)` | `llm.invoke([...])` or `chain.invoke({...})` |
| `response.content[0].text` | `response.content` (AIMessage.content) |
| `stop_reason == "tool_use"` | `response.tool_calls` (non-empty list) |
| Raw JSON tool schemas | `@tool` decorator + `bind_tools()` |
| Manual tool dispatch loop | `ToolNode` |
| Hand-written ReAct while loop | `StateGraph` with conditional edges |
| `tenacity @retry` | `llm.with_retry(stop_after_attempt=3)` |
| Manual JSON extraction | `llm.with_structured_output(MyModel)` |
| `messages: list[dict]` | `AgentState` TypedDict with `add_messages` |
| Human approval in loop | `interrupt()` + `Command(resume=...)` |
| Custom orchestrator routing | `Command(goto=...)` supervisor pattern |

## Learning Path

Follow this order. Each section builds on the previous.

### Week 1 — Foundations (LCEL chains)
```bash
python 01_foundations/llm_basics/prompting_strategies.py   # zero-shot/few-shot/CoT/ReAct as LCEL chains
python 01_foundations/llm_basics/temperature_demo.py       # ChatAnthropic(temperature=...)
python 01_foundations/llm_basics/hallucination_demo.py     # mitigations as LCEL chains
python 01_foundations/embeddings/cosine_similarity.py      # vector math from scratch (no API)
python 01_foundations/embeddings/chunking_strategies.py    # chunking tradeoffs (no API)
python 01_foundations/embeddings/vector_search_demo.py     # ChromaDB search (no API)
python 01_foundations/ml_concepts/rag_vs_finetuning.py     # decision framework
python 01_foundations/ml_concepts/evaluation_metrics.py    # precision/recall/BLEU (no API)
```

### Week 2 — Agentic Core (StateGraph, ToolNode, MemorySaver)
```bash
python 02_agentic_core/tool_use/tool_registry.py           # Tool ABC + registry (reference)
python 02_agentic_core/tool_use/sample_tools.py            # @tool-decorated tool examples
python 02_agentic_core/tool_use/function_calling.py        # @tool + bind_tools() + ToolNode
python 02_agentic_core/memory/short_term.py                # MemorySaver + thread_id
python 02_agentic_core/memory/long_term.py                 # ChromaDB persistence
python 02_agentic_core/memory/episodic.py                  # JSON run history
python 02_agentic_core/memory/semantic.py                  # key-value fact store
python 02_agentic_core/patterns/react_agent.py             # THE CORE — explicit StateGraph + create_react_agent()
python 02_agentic_core/patterns/plan_and_execute.py        # PlanExecuteState + conditional edges
python 02_agentic_core/patterns/human_in_loop.py           # interrupt() + Command(resume=...)
```

### Week 3 — System Design (Supervisor, .with_retry(), .with_fallbacks())
```bash
python 03_system_design/orchestrator.py     # supervisor pattern with Command(goto=...)
python 03_system_design/llm_gateway.py      # .with_retry() + .with_fallbacks() on Runnables
python 03_system_design/tool_registry.py    # central registry with discoverability
python 03_system_design/observability.py    # step-level tracing + structured logs
```

### Week 3–4 — Resiliency (.with_retry(), .with_structured_output(), eval)
```bash
python 04_resiliency/guardrails.py          # Pydantic input/output validation
python 04_resiliency/retry_strategies.py    # .with_retry() + .with_fallbacks()
python 04_resiliency/loop_control.py        # recursion_limit + timeout
python 04_resiliency/structured_outputs.py  # .with_structured_output()
pytest 04_resiliency/evaluation/            # prompt unit tests + golden dataset eval
```

### Week 4 — Projects (all LangGraph patterns applied)
```bash
# Project 1: create_react_agent() with MemorySaver + @tool
python 05_projects/project1_tool_agent/agent.py

# Project 2: LCEL RAG chain (retriever | prompt | llm | parser)
python 05_projects/project2_rag/ingest.py       # index sample docs
python 05_projects/project2_rag/rag_chain.py    # LCEL query pipeline
uvicorn 05_projects.project2_rag.api:app --reload  # FastAPI endpoint

# Project 3: Multi-agent StateGraph (planner → executor → validator → synthesizer)
python 05_projects/project3_multi_agent/workflow.py
```

### Before Interview — Review
```
06_interview_prep/flashcards.md              # 30+ key terms (incl. LangGraph)
06_interview_prep/system_design_templates.md # architecture diagrams
06_interview_prep/common_questions.md        # 15 prepared answers
```

## Structure

```
core/            shared utilities (ChatAnthropic, models, TypedDict states)
01_foundations/  LLM basics via LCEL chains, embeddings, ML concepts
02_agentic_core/ StateGraph patterns, MemorySaver, @tool, interrupt()
03_system_design/ supervisor, gateway, observability
04_resiliency/   guardrails, .with_retry(), .with_structured_output(), eval
05_projects/     three capstone projects using all LangGraph patterns
06_interview_prep/ flashcards and question banks
web/             Next.js learning UI with LangGraph-aware content
```
