# Foundations (Week 1–2)

Core concepts every agentic AI engineer must know cold.

## 1.1 LLM Basics

| File | Concept | API needed? |
|---|---|---|
| `prompting_strategies.py` | zero-shot / few-shot / CoT / ReAct as LCEL chains | Yes |
| `temperature_demo.py` | ChatAnthropic(temperature=...) | Yes |
| `hallucination_demo.py` | mitigations as LCEL chains, RAG preview | Yes |

**Key interview question:** *"Why do LLMs hallucinate and how do you reduce it?"*

Hallucinations happen because LLMs are trained to produce plausible next tokens,
not to verify factual accuracy. Mitigations:
1. RAG — ground answers in retrieved facts
2. Structured outputs — constrain what the model can say
3. Uncertainty prompting — instruct model to say "I don't know"
4. Human review — for high-stakes outputs

## 1.2 Embeddings + Vector Search

| File | Concept | API needed? |
|---|---|---|
| `cosine_similarity.py` | dot product, magnitude, similarity score | No |
| `chunking_strategies.py` | fixed / sliding-window / semantic tradeoffs | No |
| `vector_search_demo.py` | ChromaDB ingest + similarity query | No |

**Key interview question:** *"Walk me through how RAG works end-to-end."*

Embed query → search vector DB → retrieve top-k chunks → inject into prompt → generate.

Chunking tradeoffs:
- Smaller chunks → higher precision, lose cross-sentence context
- Larger chunks → better context, more noise, higher cost
- Sliding window → reduces boundary problem, increases cost

## 1.3 ML Concepts

| File | Concept | API needed? |
|---|---|---|
| `rag_vs_finetuning.py` | when to use each approach | Yes (optional) |
| `evaluation_metrics.py` | precision/recall, BLEU/ROUGE | No |

**Key interview question:** *"RAG vs fine-tuning — when do you use each?"*

| | RAG | Fine-tuning |
|---|---|---|
| Knowledge update | Real-time | Requires retraining |
| Cost | Per-query retrieval | Upfront compute |
| Transparency | Sources visible | Opaque |
| Best for | Dynamic knowledge, citations | Style, format, domain vocabulary |
