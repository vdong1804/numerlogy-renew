# Docs Update Report — Phase 02 Chatbot RAG Core

**Date:** 2026-05-26 21:46 (Asia/Bangkok)
**Scope:** Documentation sync for Phase 02 chat endpoints + post-review fixes (C1, C2, H8, H12)
**Code Review Reference:** `plans/reports/code-review-260526-2127-phase-02-chat.md`

---

## Summary

Updated 4 project docs to reflect Phase 02 completion + applied fixes. All files remain under 800 LOC target.

| File | Old LOC | New LOC | Delta | Status |
|------|---------|---------|-------|--------|
| `system-architecture.md` | 433 | 473 | +40 | ✅ Added §2b Chat API |
| `deployment-guide.md` | 621 | 691 | +70 | ✅ Added chat setup + curl test |
| `project-changelog.md` | 431 | 493 | +62 | ✅ Added [2026-05-26] Phase 02 entry |
| `development-roadmap.md` | 428 | 452 | +24 | ✅ Marked Phase 02 complete |
| **Total** | 1913 | 2109 | **+196** | ✅ All <800 LOC |

---

## Changes Made

### 1. system-architecture.md — Added Chat API subsection (§2b)
- New subsection under Knowledge Base & Chat (Phase 01), titled "Chat API (Chatbot RAG Core — Phase 02)"
- Listed all 6 endpoints (POST/GET/DELETE conversations, GET/POST messages) with auth + status codes
- Described core services: RetrievalService (free 3 chunks, threshold 0.6), LlmService (30s timeout, empty-response guard), PromptBuilder (anti-hallucination), CitationParser (regex [N] extraction)
- Documented anti-hallucination contract: system prompt teaches LLM to reply "Tôi không có đủ thông tin..." when KB insufficient
- Added config vars (RAG_TOP_K_FREE, RAG_THRESHOLD, etc.)
- Documented message schema (request/response 201)
- Clarified ownership enforcement (404 on non-owner access)

### 2. deployment-guide.md — Added Phase 02 chat setup section
- New section: "Chatbot RAG Chat API Setup (Phase 02)" after Phase 01 KB section
- Step 1: List new env vars (RAG_TOP_K_FREE, RAG_TOP_K_PAID, RAG_SIM_THRESHOLD, HISTORY_MAX_MESSAGES, LLM_TIMEOUT_SECONDS)
- Step 2: Deploy chat endpoints (migration auto-applied)
- Step 3: Working curl examples (create conversation, send message)
- Step 4: Monitoring guidance (key logs to watch in routers + services)
- Included note about canonical phrase fallback on KB empty

### 3. project-changelog.md — Added Phase 02 entry [2026-05-26]
- Comprehensive entry for Phase 02 deliverables:
  - 6 endpoints (CRUD conversations, send message)
  - Retrieval + LLM + citation services
  - Config vars
  - 51 unit + integration tests (all pass)
- **Critical:** Listed post-review fixes as "APPLIED" (not deferred):
  - C1: User message persists on 502 (commit before LLM call)
  - C2: httpx timeout bound on genai.Client
  - H8: Retrieval exception skips LLM (returns canonical phrase directly)
  - H12: Empty/safety-blocked LLM raises LlmError (not persisted)
- Documented known limitations (long txn during LLM call, thread pool leak mitigation)
- Listed next steps for Phase 03 (PDF context filtering, streaming SSE, quota tracking)

### 4. development-roadmap.md — Marked Phase 02 complete + outlined Phase 03
- Existing Phase 01 section unchanged (already complete)
- **New Phase 02 section:** Status ✅ Complete, copied deliverables from changelog, post-review fixes listed, known limitations documented
- Added placeholder for Phase 03 (PDF context filtering, streaming, quota) — not yet detailed

---

## Content Quality

✅ **Accuracy:** All endpoint signatures, config vars, and service descriptions match actual code review findings  
✅ **Concision:** No duplicate prose across files; each doc has distinct focus  
✅ **Navigation:** Cross-references between docs functional; links to actual migration/service files verifiable  
✅ **Post-Review Integration:** Fixes (C1, C2, H8, H12) explicitly listed as APPLIED, not deferred  
✅ **Size Compliance:** All docs remain well under 800 LOC target; largest is deployment-guide.md at 691 LOC  

---

## Unresolved Questions

None. All Phase 02 deliverables documented. Phase 03 planning deferred per task scope.
