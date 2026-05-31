---
name: chatbot-rag-pdf-analysis
date: 2026-05-26
status: complete (8/8 phases code-complete; ops handoff pending)
owner: DongVD
related_report: ../reports/brainstorm-260526-1854-chatbot-pdf-rag.md
last_sync: 2026-05-28
---

# Chatbot RAG PDF Analysis — Implementation Plan

## Goal
Add RAG chatbot to Numerology Platform: analyze system-generated PDF reports + admin knowledge base, multi-tier quota (free 3/day registered + paid add-ons), Gemini Flash/Pro, pgvector, Next.js `/chat`.

## Stack
- Backend: FastAPI (existing `numerology-api/`) + SQLAlchemy 2.0 + Alembic
- DB: PostgreSQL 16 + pgvector extension
- LLM: Google Gemini 2.0 Flash (free) / 2.5 Pro (paid) + text-embedding-004 (768d)
- Frontend: Next.js Pages Router (`Numerology-Landing-Page/`)
- Auth: JWT (reuse existing)
- Payments: reuse existing `UserPayment` flow + extend `Package`

## Budget Constraint
Target <$500/month @ 10k MAU. Hard ceilings: free 3 msg/day (registered only), semantic cache, Gemini prompt caching.

## Phases

| # | Phase | File | Duration | Status |
|---|-------|------|----------|--------|
| 1 | Foundation: DB schema + embedding service + KB ingest | [phase-01-foundation-db-embedding.md](phase-01-foundation-db-embedding.md) | 2 weeks | complete (2026-05-26) |
| 2 | Core Chat: retrieval + non-streaming endpoint + citations | [phase-02-core-chat-retrieval.md](phase-02-core-chat-retrieval.md) | 2 weeks | complete (2026-05-26) |
| 3 | User PDF: hybrid match/parse + per-user index | [phase-03-user-pdf-hybrid.md](phase-03-user-pdf-hybrid.md) | 2 weeks | complete (2026-05-26) |
| 4 | Streaming UI: SSE + Next.js /chat page | [phase-04-streaming-ui.md](phase-04-streaming-ui.md) | 2 weeks | complete (2026-05-27) |
| 5 | Quota + Add-ons: daily reset + addon packages + payment | [phase-05-quota-addons.md](phase-05-quota-addons.md) | 2 weeks | complete (2026-05-28) |
| 6 | Cache + Rate Limit: semantic cache + token bucket | [phase-06-cache-rate-limit.md](phase-06-cache-rate-limit.md) | 1 week | complete (2026-05-28) |
| 7 | Admin Tuning: KB upload UI + prompt editor + analytics | [phase-07-admin-tuning.md](phase-07-admin-tuning.md) | 1 week | complete (2026-05-28) |
| 8 | Hardening: cost monitor + abuse detection + launch | [phase-08-hardening-launch.md](phase-08-hardening-launch.md) | 1 week | complete (2026-05-28) |

## Critical Dependencies
1. Google Cloud project + Gemini API key
2. `CREATE EXTENSION vector` on PG16 production
3. Existing payment flow must accept new package type `chat_addon`
4. Admin UI access for `/admin/chatbot`

## Top Risks
- Cost overrun → P6 cache + P8 monitoring before public launch
- Hallucination → P2 similarity threshold + "no info" prompt
- PII leak → P8 encryption + DSAR endpoint

## Success Criteria (project-level)
- E2E: registered user asks question → gets answer with citation in <2.5s
- Cost @ 10k MAU < $500/month sustained 30 days
- Free→Paid conversion > 3%
- Hallucination rate <5% on 100-sample manual eval
