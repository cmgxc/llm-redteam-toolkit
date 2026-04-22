# Threat Model

This document describes the assumptions and scope of the LLM Red Team Toolkit. It is deliberately narrow so the tool stays focused and the findings are unambiguous to interpret.

## System under test

A **target** is any service that:

- Accepts user-controlled text as input (directly or indirectly via retrieved documents, tool outputs, etc.)
- Routes that input through a large language model
- Returns the model's output to the user, or uses it to drive a downstream action

Typical examples: a customer-support chatbot, a RAG-powered knowledge assistant, a document-summarization endpoint, an agent that calls tools based on user instructions.

## Trust boundaries

```
 ┌─────────┐        ┌───────────────┐        ┌────────────┐
 │  User   │ ─────> │  Application  │ ─────> │    LLM     │
 │ (untrust│        │  (system      │        │  (semi-    │
 │  ed)    │ <───── │   prompt +    │ <───── │  trusted)  │
 └─────────┘        │   routing)    │        └────────────┘
                    └───────┬───────┘
                            │
                    ┌───────┴────────┐
                    │ Retrieved docs │ (untrusted if user-supplied)
                    └────────────────┘
```

The boundaries we care about:

1. **User → Application.** The user message is attacker-controlled. The application's system prompt is trusted.
2. **Retrieved documents → LLM.** If the application pulls in user-supplied or externally-crawled content, that content is also attacker-controlled for the purposes of the LLM context.
3. **LLM → Downstream.** The model's output becomes input to something else (a web view, an email, a tool call). That "something else" often assumes the output is trustworthy; insecure output handling is the result.

## Attacker capabilities (in scope)

We model an attacker who can:

- Send arbitrary text to the target (no rate limit assumed; a few hundred queries per run is typical)
- Optionally plant arbitrary text into documents that end up in the model's context
- Observe the model's output
- Iterate — the toolkit itself encourages this via the regex + semantic judge combination

## Attacker capabilities (out of scope)

We do **not** model:

- Network-level attacks against the hosted model (TLS downgrade, etc.)
- Infrastructure compromise of the target's backend
- Fine-tuning or model-weight manipulation (OWASP LLM03) — we test the model-serving surface, not the training pipeline
- Denial of service via token-cost blowup (future work; see roadmap)

## What a "finding" means in this framework

A **successful payload** means the target's response met the payload's success criterion. Interpreting severity:

- **High severity:** the response would be harmful if the application acted on it — malicious content production, system-prompt leakage with real secrets, tool-call hijacking via indirect injection.
- **Medium severity:** the response shape is dangerous but requires a downstream vulnerability to exploit — e.g. the model emitting unsanitized HTML (LLM05) only matters if the host renders HTML.
- **Low severity:** the response deviates from policy but does not enable a concrete harm — e.g. mild persona drift.

A finding in this tool is **evidence**, not a proof of exploitability. A human reviewer should confirm impact before triaging as a security bug.

## Anti-goals

This tool is not:

- A correctness evaluator. It does not measure whether the model answers benign questions well.
- A bias/fairness auditor. Those are different evaluations with different methodology.
- A substitute for a manual red team. It automates the commoditized parts so a human can focus on application-specific attack paths.
