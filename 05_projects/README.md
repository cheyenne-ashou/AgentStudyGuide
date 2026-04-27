# Practice Projects

Three capstone projects that compose everything from sections 1–4.

## Projects at a Glance

| Project | Concepts | Time |
|---|---|---|
| Project 1: Tool Agent | ReAct loop, tool calling, retries, logging | ~30 min |
| Project 2: RAG System | Hybrid search, FastAPI, chunking | ~1 hour |
| Project 3: Multi-Agent | Plan+execute, validation, orchestration | ~1.5 hours |

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
- "I built a RAG system with hybrid BM25+vector search and RRF re-ranking..."
- "I implemented a multi-agent pipeline where a validator agent quality-gates results..."
- "I designed a tool-using agent with exponential backoff and max iteration limits..."
