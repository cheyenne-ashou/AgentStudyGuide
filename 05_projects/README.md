# Practice Projects

Three capstone projects that compose everything from sections 1–4.

## Projects at a Glance

| Project | Concepts | Time |
|---|---|---|
| Project 1: Tool Agent | `create_react_agent()`, `@tool`, `MemorySaver`, `.with_retry()` | ~30 min |
| Project 2: RAG System | LCEL chain, `RunnableLambda`, hybrid search, FastAPI | ~1 hour |
| Project 3: Multi-Agent | `PlanExecuteState`, `.with_structured_output()`, supervisor pattern | ~1.5 hours |

## Study Order

Build them in order — each project adds complexity.

## Project 1: Tool-Using Agent

```
05_projects/project1_tool_agent/
```
The simplest project: a single agent with 4 tools. Start here.

## Project 2: RAG System

```
05_projects/project2_rag/
```
Document Q&A with hybrid retrieval and a REST API. Demonstrates the most common
production pattern for knowledge-grounded AI.

## Project 3: Multi-Agent Workflow

```
05_projects/project3_multi_agent/
```
Planner → Executor → Validator pipeline. The most complex pattern you'll encounter in interviews.

## Interview Impact

These projects give you concrete answers to "walk me through something you built":
- "I built a RAG system as an LCEL chain: retriever | prompt | llm | parser, with hybrid BM25+vector search..."
- "I implemented a multi-agent StateGraph with a validator node that conditionally retries execution..."
- "I built a tool-using agent with create_react_agent(), MemorySaver for persistence, and .with_retry() for resilience..."
