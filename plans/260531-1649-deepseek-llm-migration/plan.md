---
title: "Chat LLM Migration: Gemini → DeepSeek"
description: "Hard-cutover chat generation from google-genai (Gemini) to DeepSeek via OpenAI-compatible SDK; drop prompt-cache layer; keep Gemini embeddings."
status: pending
priority: P2
effort: ~8h
branch: master
tags: [chat, llm, deepseek, migration, refactor]
created: 2026-05-31
---

# Chat LLM Migration: Gemini → DeepSeek

Hard cutover of chat-generation LLM. Embeddings stay on Gemini (text-embedding-004, 768-dim) — DeepSeek has no embedding API. Prompt-cache infrastructure removed wholesale (DeepSeek has automatic free disk caching).

## Decisions (locked)
- `openai` SDK pointed at `https://api.deepseek.com`; model = `deepseek-chat` for BOTH `flash` and `pro` tiers (single-model strategy).
- `tier: Literal["flash","pro"]` param kept (no caller-API break) but maps to same model id.
- Embeddings + pgvector schema (768-dim) unchanged; no re-embedding.
- Prompt-cache service, model, table, settings, job entry: deleted.
- No provider abstraction, no feature flag, no rollback path.

## Phases

| ID  | File | Status | Notes |
|-----|------|--------|-------|
| P1  | [phase-01-config-and-deps.md](./phase-01-config-and-deps.md) | pending | pyproject + config + .env |
| P2  | [phase-02-llm-service-rewrite.md](./phase-02-llm-service-rewrite.md) | pending | LlmService → DeepSeek |
| P3  | [phase-03-remove-prompt-cache.md](./phase-03-remove-prompt-cache.md) | pending | delete service+model+table+callers+job |
| P4  | [phase-04-tests.md](./phase-04-tests.md) | pending | rewrite chat tests, delete cache tests |
| P5  | [phase-05-docs.md](./phase-05-docs.md) | pending | sync /docs |

## Dependency graph
- P1 unblocks P2, P3
- P2 unblocks P3 (callers stripped after new LlmService signature stable)
- P3 unblocks P4
- P4 unblocks P5

## Key risks
- **R1 (Med)**: Streaming model change — google-genai sync iter + thread bridge → openai async iter. Mitigation: `stream_options={"include_usage": True}` captures usage on final chunk; LlmError wrapper preserved.
- **R2 (Low)**: Alembic drop migration on prod must run after code deploy (callers gone). Mitigation: order in runbook.
- **R3 (Low)**: Empty-response semantic ("safety filter") differs between providers — preserve `LlmError("LLM returned empty response")` on blank text from DeepSeek.

## Success criteria (whole plan)
- Chat send + stream endpoints work end-to-end against `api.deepseek.com`.
- `grep -r "PromptCache\|prompt_cache_handles\|cached_content" numerology-api/app` returns zero results.
- `grep -r "google.genai\|google_genai" numerology-api/app` only matches `embedding_service.py`.
- `pytest` green; no skipped tests due to migration.
- `/docs` reflects new architecture + cost model.
