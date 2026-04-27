# Agentic AI Interview Prep

Runnable Python demos for every concept in the study guide.
Each file has a `__main__` block — run it, read the output, understand the concept.

## Setup

```bash
# 1. Python 3.11+
python --version

# 2. Install dependencies
pip install -e .

# 3. Set your API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...
```

## Learning Path

Follow this order. Each section builds on the previous.

### Week 1 — Foundations
```bash
python 01_foundations/llm_basics/prompting_strategies.py   # zero-shot vs few-shot vs CoT vs ReAct
python 01_foundations/llm_basics/temperature_demo.py       # determinism vs creativity
python 01_foundations/llm_basics/hallucination_demo.py     # why it happens + mitigations
python 01_foundations/embeddings/cosine_similarity.py      # vector math from scratch
python 01_foundations/embeddings/chunking_strategies.py    # chunking tradeoffs (no API needed)
python 01_foundations/embeddings/vector_search_demo.py     # ChromaDB search (no API needed)
python 01_foundations/ml_concepts/rag_vs_finetuning.py     # decision framework
python 01_foundations/ml_concepts/evaluation_metrics.py    # precision/recall/BLEU (no API needed)
```

### Week 2 — Agentic Core
```bash
python 02_agentic_core/tool_use/tool_registry.py           # Tool ABC + registry pattern
python 02_agentic_core/tool_use/sample_tools.py            # calculator, datetime, search stubs
python 02_agentic_core/tool_use/function_calling.py        # end-to-end Claude tool_use
python 02_agentic_core/memory/short_term.py                # context window management
python 02_agentic_core/memory/long_term.py                 # ChromaDB persistence
python 02_agentic_core/memory/episodic.py                  # JSON run history
python 02_agentic_core/memory/semantic.py                  # key-value fact store
python 02_agentic_core/patterns/react_agent.py             # THE CORE PATTERN — study this one
python 02_agentic_core/patterns/plan_and_execute.py        # two-phase planning
python 02_agentic_core/patterns/human_in_loop.py           # approval + feedback loops
```

### Week 3 — System Design
```bash
python 03_system_design/orchestrator.py     # routes tasks to specialized agents
python 03_system_design/llm_gateway.py      # unified LLM interface + fallback chain
python 03_system_design/tool_registry.py    # central registry with discoverability
python 03_system_design/observability.py    # step-level tracing + structured logs
```

### Week 3–4 — Resiliency
```bash
python 04_resiliency/guardrails.py          # Pydantic input/output validation
python 04_resiliency/retry_strategies.py    # tenacity backoff + model fallback
python 04_resiliency/loop_control.py        # max iterations + timeout
python 04_resiliency/structured_outputs.py  # JSON enforcement + re-prompting
pytest 04_resiliency/evaluation/            # prompt unit tests + golden dataset eval
```

### Week 4 — Projects
```bash
# Project 1: Tool-using agent
python 05_projects/project1_tool_agent/agent.py

# Project 2: RAG system
python 05_projects/project2_rag/ingest.py       # index sample docs
python 05_projects/project2_rag/rag_chain.py    # query the system
uvicorn 05_projects.project2_rag.api:app --reload  # run the API

# Project 3: Multi-agent pipeline
python 05_projects/project3_multi_agent/workflow.py
```

### Before Interview — Review
```
06_interview_prep/flashcards.md              # 30 key terms
06_interview_prep/system_design_templates.md # architecture diagrams
06_interview_prep/common_questions.md        # 15 prepared answers
```

## Structure

```
core/           shared utilities (client, logger, models) — imported everywhere
01_foundations/ LLM basics, embeddings, ML concepts
02_agentic_core/ agent patterns, memory types, tool use
03_system_design/ orchestrator, gateway, observability
04_resiliency/  guardrails, retries, loop control, evaluation
05_projects/    three capstone projects
06_interview_prep/ flashcards and question banks
```
