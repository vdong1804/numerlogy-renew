# Phase 04 — Test Suite Updates

## Context Links
- Parent: [plan.md](./plan.md)
- Depends on: P2 (LlmService) + P3 (prompt-cache removed).
- Tests touched (verified via grep):
  - `tests/services/chat/test_prompt_cache_service.py` (DELETE)
  - `tests/services/chat/test_llm_service.py` (does not exist — CREATE optional; current LlmService tests live as monkeypatches inside router tests)
  - `tests/routers/chat/test_messages.py` (strip prompt-cache assertions)
  - `tests/routers/chat/test_stream_endpoint.py` (strip prompt-cache assertions)
  - `tests/jobs/test_cleanup_semantic_cache.py` (drop prompt_cache_handles assertions)
- Note: router tests already monkeypatch `LlmService.generate` / `LlmService.generate_stream`; they should mostly survive P2 unchanged because they bypass the SDK entirely.

## Overview
- **Priority:** P0 — gate for ship.
- **Status:** pending.
- Delete prompt-cache tests, scrub references in router + job tests, add a minimal `test_llm_service.py` that exercises the openai SDK via `respx` (already in dev deps).

## Key Insights
- Existing test pattern: `monkeypatch.setattr(LlmService, "generate", _fake)` — survives provider swap because the patched surface is the public method.
- `respx` is in `[project.optional-dependencies].dev` — usable to mock `openai`'s underlying `httpx.AsyncClient` if we want to test the real SDK call path.
- `test_messages.py` and `test_stream_endpoint.py` likely also stub `PromptCacheService` — need to delete those mocks once the import is gone.
- `test_cleanup_semantic_cache.py` asserts both cache cleanups — drop prompt_cache half.

## Requirements
- All pytest collection passes (no `ImportError` from missing `prompt_cache_service`).
- Coverage of LlmService remains: at minimum one streaming + one non-streaming happy-path + one error-path test.
- No fake-data shortcuts to make build pass.

## Architecture
Test isolation strategy unchanged:
- Unit tests: monkeypatch `LlmService.generate` / `generate_stream` directly.
- SDK-level test (new, optional): `respx.mock` intercepts `POST https://api.deepseek.com/chat/completions`.

## Related Code Files

**Delete**
- `tests/services/chat/test_prompt_cache_service.py`

**Modify**
- `tests/routers/chat/test_messages.py` — remove any PromptCacheService imports / monkeypatches; existing `LlmService.generate` mocks stay.
- `tests/routers/chat/test_stream_endpoint.py` — same.
- `tests/jobs/test_cleanup_semantic_cache.py` — drop prompt_cache_handles assertions; assert only semantic_cache deletion.

**Create**
- `tests/services/chat/test_llm_service.py` — minimal coverage:
  1. `test_generate_happy_path` — respx mocks 200 JSON with `choices[0].message.content` + `usage`; asserts LlmResponse fields.
  2. `test_generate_stream_yields_tokens_and_populates_result` — respx mocks SSE stream; asserts tokens yielded + StreamResult populated from final `usage` chunk.
  3. `test_generate_empty_response_raises_llm_error` — mock with empty content → LlmError.
  4. `test_generate_api_error_wraps_in_llm_error` — respx returns 500 → openai.APIError → LlmError.
  5. `test_missing_api_key_raises` — `LlmService(api_key="")` then `.client` → LlmError.

## Implementation Steps
1. Delete `tests/services/chat/test_prompt_cache_service.py`.
2. In `test_messages.py`: grep `PromptCache`; remove all references (imports, monkeypatch, assertions). Keep `LlmService.generate` monkeypatches as-is.
3. In `test_stream_endpoint.py`: same as step 2 against `LlmService.generate_stream`.
4. In `test_cleanup_semantic_cache.py`: assert only `{"semantic_cache": <int>}` return shape; drop seed/teardown of prompt_cache_handles rows.
5. Author `test_llm_service.py` (5 tests above). Use `respx.mock(base_url="https://api.deepseek.com")`.
6. Run `pytest tests/ -x -q`. Fix failures iteratively; do not skip tests.

## Todo List
- [ ] Delete `test_prompt_cache_service.py`
- [ ] Scrub PromptCache refs from `test_messages.py`
- [ ] Scrub PromptCache refs from `test_stream_endpoint.py`
- [ ] Update `test_cleanup_semantic_cache.py` (semantic-only)
- [ ] Author `test_llm_service.py` (5 cases)
- [ ] `pytest tests/services/chat -q` passes
- [ ] `pytest tests/routers/chat -q` passes
- [ ] `pytest tests/jobs -q` passes
- [ ] Full `pytest -q` passes with 0 errors / 0 failures / 0 unintended skips

## Success Criteria
- 100% of existing tests that touched LlmService still pass.
- New `test_llm_service.py` covers the 5 cases above.
- `pytest --collect-only` shows no `ImportError`.
- No `@pytest.mark.skip` added by this phase.

## Risk Assessment
| Risk | L | I | Mitigation |
|------|---|---|-----------|
| respx SSE mocking awkward for openai stream | M | M | Fallback: monkeypatch `AsyncOpenAI.chat.completions.create` to return an async iterator; document choice in test |
| Hidden test fixtures seed `prompt_cache_handles` | M | L | Search `conftest.py` for table refs; remove |
| Flaky test from real network leak | L | H | `respx` raises on unmatched outbound; CI catches |
| Stream usage-chunk shape changes across openai versions | L | M | Pin `openai>=1.40,<2` in P1 if needed |

## Security Considerations
- Tests must use placeholder `DEEPSEEK_API_KEY="test"` env, never a real key.
- `conftest.py` should already override settings; verify.

## Next Steps
- On green: P5 doc sync.
