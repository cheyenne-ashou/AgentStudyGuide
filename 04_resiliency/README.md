# Resiliency in Agentic Systems (CRITICAL)

Most interview candidates fail resiliency questions. This section covers all of them.

## Why Resiliency is Hard in Agentic Systems

1. **Non-deterministic** — same input, different output
2. **Multi-step** — errors compound across steps
3. **External dependencies** — tools fail, APIs rate-limit
4. **Long-running** — hard to recover mid-execution
5. **No rollback** — some actions are irreversible

## Failure Modes

| Failure | Cause | Mitigation |
|---|---|---|
| Hallucination | Model invents facts | RAG, grounding, structured outputs |
| Tool failure | API down, bad input | Retry, fallback, error handling |
| Infinite loop | No termination condition | Max iterations, timeout |
| Bad reasoning chain | Wrong plan | Validator agent, human review |
| Latency spike | Slow tool/model | Timeout, async, fallback model |
| Context overflow | Long conversation | Rolling window, summarization |

## Files

| File | Pattern | Interview question it answers |
|---|---|---|
| `guardrails.py` | Input/output validation | "How do you prevent bad inputs/outputs?" |
| `retry_strategies.py` | `.with_retry()` + `.with_fallbacks()` | "What happens when an API call fails?" |
| `loop_control.py` | Max iterations, timeout | "How do you prevent infinite loops?" |
| `structured_outputs.py` | `.with_structured_output()` | "How do you make LLM output reliable?" |
| `evaluation/prompt_unit_tests.py` | Prompt testing | "How do you test an agent?" |
| `evaluation/golden_dataset.py` | Golden dataset eval | "How do you measure agent quality?" |

## The Key Insight

Agentic systems need **layered defenses**:
1. Input guardrails (before LLM call)
2. Structured outputs (constrain what LLM can say)
3. Output guardrails (after LLM call)
4. Retry + fallback (when things fail)
5. Loop control (prevent runaway execution)
6. Human escalation (last resort)
