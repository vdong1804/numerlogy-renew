# Phase 02 — Core Chat: Retrieval + Non-Streaming Endpoint + Citations

## Context Links
- Depends on: `phase-01-foundation-db-embedding.md`
- Brainstorm: `../reports/brainstorm-260526-1854-chatbot-pdf-rag.md` §4.3 chat flow

## Overview
- **Priority:** Critical (validates core RAG quality before UI work)
- **Status:** complete (2026-05-26) — 51/51 unit + router tests pass; critical + should-fix post-review issues resolved
- **Duration:** 2 weeks
- **Description:** Build retrieval service (pgvector top-k), prompt builder, Gemini LLM service (non-streaming first), conversation/message CRUD routers. Output cited answers from KB only.

## Key Insights
- Cosine similarity threshold ~0.6 — below = "no info available" response (anti-hallucination).
- Free tier top-k=3, paid top-k=8 (configurable per request).
- Citation format: `[1]`, `[2]`... mapped to KbChunk IDs returned in response payload.
- Multi-turn: include last 5 messages in prompt; trim oldest if total > 32k tokens.
- Gemini prompt caching activates after first call when system prompt + KB stable.

## Requirements

### Functional
- POST `/api/chat/conversations` → create new conversation.
- GET `/api/chat/conversations` → list user's conversations (paginated).
- GET `/api/chat/conversations/{id}/messages` → list messages.
- DELETE `/api/chat/conversations/{id}` → delete (cascade messages).
- POST `/api/chat/conversations/{id}/messages` → send message, return AI reply + citations (non-streaming).
- Retrieval merges KB chunks + (later) user PDF chunks (Phase 03 hook ready).
- Citations include: chunk_id, document_id, source_type, source_ref, title, score.

### Non-Functional
- p95 latency <3s for non-streaming reply.
- Concurrent requests handled async (FastAPI httpx + asyncpg).
- No hard-coded prompts in routers — all in `prompt_builder.py`.

## Architecture

```
app/
├── routers/chat/
│   ├── __init__.py
│   ├── conversations.py          # CRUD conversations
│   └── messages.py               # send message + list
├── services/chat/
│   ├── retrieval_service.py      # pgvector top-k + merge + score
│   ├── prompt_builder.py         # system + history + KB + citation
│   ├── llm_service.py            # Gemini Flash/Pro client (sync + stream)
│   ├── citation_parser.py        # extract [N] refs + map to chunk_ids
│   └── conversation_service.py   # CRUD + history fetch
├── schemas/chat/
│   ├── __init__.py
│   ├── conversation.py           # Pydantic DTOs
│   ├── message.py                # MessageIn/MessageOut + Citation
│   └── retrieval.py              # RetrievedChunk
```

## Prompt Template (system)

```
You are a numerology expert assistant. Answer ONLY based on the provided KNOWLEDGE BASE excerpts below.

RULES:
1. Cite sources inline using [1], [2]... matching the numbered excerpts.
2. If KNOWLEDGE BASE has insufficient information, reply EXACTLY: "Tôi không có đủ thông tin để trả lời câu hỏi này."
3. Answer in Vietnamese unless the user writes in English.
4. Be concise but complete. Use bullet points for lists.
5. Do not invent numerology meanings not present in the excerpts.

KNOWLEDGE BASE:
[1] (source: {source_type}/{source_ref}) {chunk_content}
[2] ...

CONVERSATION HISTORY:
{recent_messages}

USER QUESTION:
{user_message}
```

## Related Code Files

### Create
- `app/routers/chat/__init__.py`
- `app/routers/chat/conversations.py` (≤150 LOC)
- `app/routers/chat/messages.py` (≤180 LOC)
- `app/services/chat/retrieval_service.py` (≤150 LOC)
- `app/services/chat/prompt_builder.py` (≤120 LOC)
- `app/services/chat/llm_service.py` (≤180 LOC)
- `app/services/chat/citation_parser.py` (≤80 LOC)
- `app/services/chat/conversation_service.py` (≤120 LOC)
- `app/schemas/chat/conversation.py`
- `app/schemas/chat/message.py`
- `app/schemas/chat/retrieval.py`
- `tests/routers/chat/test_conversations.py`
- `tests/routers/chat/test_messages.py`
- `tests/services/chat/test_retrieval_service.py`
- `tests/services/chat/test_prompt_builder.py`
- `tests/services/chat/test_citation_parser.py`

### Modify
- `app/main.py` — include chat routers
- `app/deps.py` — add `get_current_user` reuse, add `get_chat_services` factory
- `app/config.py` — add `RAG_TOP_K_FREE=3`, `RAG_TOP_K_PAID=8`, `RAG_SIM_THRESHOLD=0.6`, `HISTORY_MAX_MESSAGES=5`

## Implementation Steps

1. **Retrieval service**
   ```python
   class RetrievalService:
       async def retrieve(
           self,
           query: str,
           top_k: int,
           threshold: float = 0.6,
           pdf_context_id: int | None = None,  # Phase 03
       ) -> list[RetrievedChunk]:
           query_emb = await self.embedding.embed_one(query)
           # pgvector: ORDER BY embedding <=> :emb ASC LIMIT :k
           # filter by 1 - cosine_distance >= threshold
   ```
   - Raw SQL with `<=>` operator (cosine distance, 0=identical).
   - Join `kb_chunks` + `kb_documents` to fetch metadata.
   - Return sorted by similarity DESC.

2. **Prompt builder**
   - Inject numbered excerpts (max 8).
   - Truncate history to last 5 messages.
   - Total token budget check (warn if >32k for Pro / >16k for Flash).
   - System prompt is constant string → cacheable by Gemini.

3. **LLM service**
   ```python
   class LlmService:
       async def generate(
           self,
           system: str,
           messages: list[dict],
           model: Literal["flash", "pro"],
           stream: bool = False,
       ) -> LlmResponse | AsyncIterator[str]:
   ```
   - Wraps `google.genai.GenerativeModel`.
   - Counts tokens via `model.count_tokens()`.
   - Enables `cached_content` after first call (P6 will integrate full prompt caching).
   - Returns: `text`, `input_tokens`, `output_tokens`, `model_used`.

4. **Citation parser**
   - Regex `\[(\d+)\]` extract used indices.
   - Map to source chunks list from prompt.
   - Return citations payload + cleaned text (or keep [N] markers — frontend renders).

5. **Conversation service**
   ```python
   class ConversationService:
       async def create(user_id, title=None) -> ChatConversation
       async def list_for_user(user_id, page, limit) -> tuple[list, int]
       async def get_owned(conversation_id, user_id) -> ChatConversation  # raises 404 if not owner
       async def delete(conversation_id, user_id)
       async def get_recent_messages(conversation_id, limit=5) -> list[ChatMessage]
   ```

6. **Routers**
   - `conversations.py`: CRUD + ownership check via `Depends(get_current_user)`.
   - `messages.py`: POST endpoint orchestrates retrieval → prompt → LLM → save → respond.
   - Use Pydantic schemas for request/response validation.

7. **Schemas**
   ```python
   # message.py
   class MessageIn(BaseModel):
       content: str = Field(min_length=1, max_length=2000)

   class Citation(BaseModel):
       index: int
       chunk_id: int
       document_id: int
       source_type: str
       source_ref: str
       title: str | None
       score: float

   class MessageOut(BaseModel):
       id: int
       role: str
       content: str
       citations: list[Citation]
       model_used: str
       created_at: datetime
   ```

8. **Tier selection (stub for Phase 05)**
   - For now, all authenticated users use Flash + top_k=3.
   - Add `tier` field to MessageOut (always "free" in this phase).
   - Phase 05 will add quota check + tier switching.

9. **Anti-hallucination test**
   - Manual: ask 10 questions on/off-topic, verify "không có đủ thông tin" appears for off-topic.
   - Verify citations always reference real KbChunk IDs.

10. **Compile + test**
    - `python -m compileall app/routers/chat app/services/chat`
    - `pytest tests/routers/chat tests/services/chat`

## Todo List

- [x] Create `app/schemas/chat/` Pydantic models
- [x] Implement `retrieval_service.py` with pgvector raw SQL + threshold filter
- [x] Implement `prompt_builder.py` with system template + history + KB injection
- [x] Implement `llm_service.py` Gemini wrapper (non-streaming first)
- [x] Implement `citation_parser.py` regex + mapping
- [x] Implement `conversation_service.py` CRUD + ownership checks
- [x] Create `routers/chat/conversations.py` (4 endpoints)
- [x] Create `routers/chat/messages.py` (POST send + GET list)
- [x] Register routers in `app/main.py`
- [x] Add RAG config constants to `app/config.py`
- [x] Write unit tests: retrieval, prompt builder, citation parser (16 tests pass)
- [x] Write integration tests: full message flow (15 router tests pass)
- [ ] Manual hallucination test (10 questions) — deferred, needs real GEMINI_API_KEY
- [x] Update OpenAPI docs (FastAPI auto — covered by router decorators)
- [x] Compile check + test suite green (51/51 phase-02 tests pass after post-review fixes)

## Post-Review Fixes Applied

After code review ([code-review-260526-2127-phase-02-chat.md](../reports/code-review-260526-2127-phase-02-chat.md)):

**C1 Fix: User message persistence on LLM failure**
- `messages.send_message` split user message insert into separate transaction.
- Flow: `db.add(user_msg)` → `db.commit()` (release locks) → LLM call → `db.add(asst_msg)` → `db.commit()`.
- Result: user messages survive LLM 502 errors instead of being rolled back.

**C2 Fix: LLM timeout with HTTP bounds**
- Added `httpx.Timeout(total=30)` to `genai.Client` initialization.
- Ensures sync google-genai HTTP call honors the 30s timeout; previously only `asyncio.wait_for` would cancel but leave thread + socket leaking.
- Result: no thread-pool starvation on repeated timeout scenarios.

**H8 Fix: Retrieval failure short-circuit**
- On `RetrievalService` exception, skip LLM call entirely.
- Return canonical "Tôi không có đủ thông tin..." reply via new `_persist_and_return_canonical` helper.
- Result: clear operational signal (log line), no wasted LLM cost, correct user-visible behavior.

**H12 Fix: Empty LLM response guard**
- `LlmService.generate` now raises `LlmError` if `resp.text` is empty (safety-blocked).
- Prevents blank assistant bubbles in conversation.

**Test additions:**
- `test_system_prompt_contains_canonical_no_info_phrase` — validates system prompt contract.
- `test_retrieval_failure_short_circuits_to_canonical` — integration test for H8.
- `test_user_message_persists_on_llm_error` — validates C1 transaction split.
- All 51/51 tests pass (48/48 original phase-02 + 3 new post-review).

## Success Criteria
- POST message returns response in <3s p95 with real Gemini.
- Citations array non-empty when answer has [N] refs.
- Off-topic question returns canonical "không có đủ thông tin" response.
- Multi-turn: 2nd message references 1st without re-asking context.
- Test coverage ≥80% on services/chat.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Retrieval pulls irrelevant chunks (low recall) | Tune HNSW `ef_search=100`; add reranker in Phase 08 if needed |
| LLM ignores citation instruction | Few-shot example in system prompt; post-validate that [N] refs exist |
| Token budget exceeded with long history | Truncate history before prompt build; log warnings |
| Gemini timeout | 30s timeout; user-facing error "Vui lòng thử lại" |
| User sends 2000+ char question | Pydantic max_length=2000; reject 422 |

## Security Considerations
- `get_current_user` enforces JWT; anonymous rejected (401).
- Ownership check on every conversation/message route.
- Sanitize user input: no role tokens leak (`<|system|>`, etc.) — strip from content before prompt build.
- Log only message IDs + token counts, never full content (PII).

## Next Steps / Dependencies
- **Unlocks:** Phase 03 (User PDF) hooks into `RetrievalService.retrieve(pdf_context_id=...)`.
- **Unlocks:** Phase 04 (Streaming UI) reuses `LlmService` adding `stream=True`.
- **Parallel-safe with:** Phase 03 can start in parallel after retrieval interface is stable.
