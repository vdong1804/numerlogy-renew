# Phase 02 — LlmService Rewrite (Gemini → DeepSeek)

## Context Links
- Parent: [plan.md](./plan.md)
- Depends on: [phase-01-config-and-deps.md](./phase-01-config-and-deps.md)
- Code: `numerology-api/app/services/chat/llm_service.py`

## Overview
- **Priority:** P0.
- **Status:** pending.
- Rewrite `LlmService` to call DeepSeek via `openai.AsyncOpenAI`. Preserve public API: `LlmResponse`, `StreamResult`, `LlmError`, `LlmService(api_key, flash_model, pro_model, timeout)`, `model_id(tier)`, `generate()`, `generate_stream()`. Drop `cached_content` param everywhere (callers handled in P3).

## Key Insights
- `openai` SDK exposes `await client.chat.completions.create(model=..., messages=..., stream=True, stream_options={"include_usage": True}, timeout=...)`. Final stream chunk carries `usage` (`prompt_tokens`, `completion_tokens`) **only** when `include_usage=True`.
- No more threading / queue bridge — `async for chunk in stream` runs natively on the event loop. Producer-thread accepted-limitation docstring becomes obsolete; replace with note that consumer cancellation closes the HTTP stream via `httpx` automatically.
- DeepSeek system prompt is just `{"role": "system", "content": system}` first message; no separate `system_instruction` field.
- Error mapping: catch `openai.APIError`, `openai.APITimeoutError`, `openai.APIConnectionError`, `asyncio.TimeoutError` → wrap into `LlmError`. Pass-through `asyncio.CancelledError`.
- Empty-response guard preserved (raise `LlmError("LLM returned empty response")`).
- `model_id(tier)` returns `self._chat_model` regardless of `tier` (both flash and pro map to `deepseek-chat`). Keep param to avoid caller-API break.

## Requirements
- Public API surface unchanged except removal of `cached_content: Optional[str] = None` from `generate` and `generate_stream`.
- `StreamResult` populated after iterator exhausted: `input_tokens`, `output_tokens`, `model_used`.
- `LlmService.client` property returns `AsyncOpenAI` instance (used to be `genai.Client` — referenced by `_build_prompt_cache_svc` which is removed in P3, so safe).
- Constructor signature: `__init__(api_key=None, flash_model=None, pro_model=None, timeout=None)` — keep `flash_model`/`pro_model` kwargs accepted but ignored (back-compat for tests passing them; document as no-op). KISS alt: rename to `chat_model`; will require touching call sites — defer; **decision: keep flash/pro kwargs, ignore; add `chat_model` kwarg**.

## Architecture

### Stream control flow (new)
```
generate_stream(system, user_content, tier, result)
  → AsyncOpenAI.chat.completions.create(
        model=chat_model,
        messages=[{role:"system", content:system}, {role:"user", content:user_content}],
        stream=True,
        stream_options={"include_usage": True},
        timeout=self._timeout)
  → async for chunk in stream:
        text = chunk.choices[0].delta.content if chunk.choices else ""
        if text: yield text
        if chunk.usage:   # last chunk only
            result.input_tokens  = chunk.usage.prompt_tokens
            result.output_tokens = chunk.usage.completion_tokens
            result.model_used    = self._chat_model
```

### Non-streaming flow
```
generate(system, user_content, tier)
  → AsyncOpenAI.chat.completions.create(stream=False, timeout)
  → text = resp.choices[0].message.content
  → usage = resp.usage  → LlmResponse(text, model, prompt_tokens, completion_tokens)
```

### Timeout
- `openai` SDK accepts `timeout=` per call (float seconds) — wraps httpx timeout.
- Outer `asyncio.wait_for` redundant; remove for KISS.

## Related Code Files
**Modify**
- `numerology-api/app/services/chat/llm_service.py` — full rewrite (~120 LOC target, well under 200).

**Read for context (no edit in this phase)**
- `numerology-api/app/routers/chat/messages.py` — uses `llm.client` (P3 strips).
- `numerology-api/app/routers/chat/_stream_generator.py` — same.

## Implementation Steps
1. Replace top-level imports: drop `google.genai` + `threading`; add `from openai import AsyncOpenAI, APIError, APITimeoutError, APIConnectionError`.
2. Keep dataclasses `LlmResponse`, `StreamResult`, exception `LlmError`.
3. Rewrite `LlmService.__init__`:
   - `self._api_key = api_key or settings.deepseek_api_key`
   - `self._chat_model = settings.deepseek_chat_model`
   - `self._base_url = settings.deepseek_base_url`
   - `self._timeout = timeout or settings.llm_timeout_seconds`
   - `self._client: AsyncOpenAI | None = None`
   - Accept (ignore) `flash_model`/`pro_model` kwargs to avoid breaking call sites — document as deprecated.
4. `client` property: lazy-create `AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)`; raise `LlmError("DEEPSEEK_API_KEY is not configured")` when missing.
5. `model_id(tier)`: `return self._chat_model` (param unused; keep for back-compat).
6. `generate_stream` rewrite per Architecture; drop `cached_content` param; drop `_DONE`/queue/thread plumbing; wrap `openai.*` exceptions → `LlmError`.
7. `generate` rewrite per Architecture; drop `_call` helper; one async call.
8. Update module docstring: "DeepSeek chat client (OpenAI-compatible SDK)…"
9. Run `python -c "from app.services.chat.llm_service import LlmService; LlmService()"` smoke.
10. Compile-check: `python -m compileall app/services/chat/llm_service.py`.

## Todo List
- [ ] Replace imports (google.genai → openai)
- [ ] Constructor uses settings.deepseek_*; flash_model/pro_model kwargs accepted-but-ignored
- [ ] `model_id` returns chat_model unconditionally
- [ ] `client` property lazy-creates `AsyncOpenAI`
- [ ] `generate_stream` uses async iter + `stream_options={"include_usage": True}`; populates StreamResult
- [ ] `generate` uses non-streaming chat.completions; populates LlmResponse
- [ ] Drop `cached_content` from both signatures
- [ ] Empty-text guard preserved → `LlmError`
- [ ] Exception mapping covers `APIError`, `APITimeoutError`, `APIConnectionError`, `asyncio.TimeoutError`
- [ ] `asyncio.CancelledError` re-raised (not wrapped)
- [ ] `python -m compileall` passes
- [ ] File under 200 LOC

## Success Criteria
- Importable: `from app.services.chat.llm_service import LlmService, LlmError, LlmResponse, StreamResult`.
- Calling `LlmService()` with `DEEPSEEK_API_KEY` set returns text for a simple prompt (manual smoke).
- Stream returns at least one delta, then a final chunk with usage populated.
- `grep -n "google.genai\|threading\|cached_content\|asyncio.Queue" app/services/chat/llm_service.py` returns empty.

## Risk Assessment
| Risk | L | I | Mitigation |
|------|---|---|-----------|
| `stream_options` ignored if SDK <1.40 | L | H | Pin `openai>=1.40` in P1 |
| Usage absent on aborted stream (client disconnect) | M | L | Caller already tolerates 0 tokens (model_used set early); accept |
| DeepSeek safety-block returns empty content | L | M | Empty-text → LlmError preserved |
| `tier` callers expecting different model | L | L | Single-model strategy documented; no functional difference |
| `flash_model`/`pro_model` kwargs in tests cause TypeError | M | M | Accept-and-ignore in `__init__` |

## Security Considerations
- API key stored in env only; never logged.
- Outbound traffic goes to `api.deepseek.com` (CN-hosted) — confirm allowed by ops; note in P5 docs.

## Next Steps
- P3 strips `cached_content=` from `_stream_generator.py` and `messages.py`, removes `_build_prompt_cache_svc`, removes PromptCacheService imports.
- P4 updates tests; existing tests monkeypatch `LlmService.generate`/`generate_stream` directly so most should pass without SDK-level changes.
