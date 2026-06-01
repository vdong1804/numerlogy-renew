# Phase 01 — Config & Dependencies

## Context Links
- Parent: [plan.md](./plan.md)
- Code: `numerology-api/pyproject.toml`, `numerology-api/app/config.py`, `numerology-api/.env.example`

## Overview
- **Priority:** P0 — blocks P2/P3.
- **Status:** pending.
- Add `openai` dep, introduce DeepSeek settings, remove prompt-cache settings, keep Gemini key (still needed for `EmbeddingService`).

## Key Insights
- `openai` Python SDK is async-native (`AsyncOpenAI`) — no thread bridging in P2.
- Embeddings continue calling Gemini via `google-genai`; keep `gemini_api_key` + `embedding_model` settings.
- Removing `prompt_cache_hit_threshold` + `prompt_cache_ttl_seconds` now is safe because P3 strips all callers in same PR.

## Requirements
- Functional: `settings.deepseek_api_key`, `settings.deepseek_chat_model`, `settings.deepseek_base_url` available.
- Non-functional: `openai>=1.40` (supports `stream_options`); pin via `>=` not `==`.

## Architecture
Data flow change (chat path only):
```
Before: chat_turn → LlmService → google.genai.Client → Gemini API
After:  chat_turn → LlmService → openai.AsyncOpenAI(base_url=deepseek) → DeepSeek API
```
Embedding path unchanged.

## Related Code Files
**Modify**
- `numerology-api/pyproject.toml` — add `openai>=1.40`. Keep `google-genai>=0.3` (embeddings).
- `numerology-api/app/config.py` — add 3 DeepSeek fields; remove `gemini_flash_model`, `gemini_pro_model`, `prompt_cache_hit_threshold`, `prompt_cache_ttl_seconds`. Keep `gemini_api_key`, `embedding_model`.
- `numerology-api/.env.example` — add DEEPSEEK_* block; remove GEMINI_FLASH_MODEL / GEMINI_PRO_MODEL lines.

**Create / Delete:** none.

## Implementation Steps
1. `pyproject.toml`: append `"openai>=1.40",` to `dependencies` list.
2. `config.py`: replace Gemini chat model fields with:
   ```
   deepseek_api_key: str = ""
   deepseek_base_url: str = "https://api.deepseek.com"
   deepseek_chat_model: str = "deepseek-chat"
   ```
   Drop `gemini_flash_model`, `gemini_pro_model`, `prompt_cache_hit_threshold`, `prompt_cache_ttl_seconds`.
3. `.env.example`: add block:
   ```
   DEEPSEEK_API_KEY=
   DEEPSEEK_BASE_URL=https://api.deepseek.com
   DEEPSEEK_CHAT_MODEL=deepseek-chat
   ```
   Remove `GEMINI_FLASH_MODEL` / `GEMINI_PRO_MODEL` lines (lines 130-131).
4. Run `pip install -e .[dev]` (or `uv sync`) to refresh lockfile.
5. `python -c "from app.config import settings; print(settings.deepseek_chat_model)"` smoke.

## Todo List
- [ ] Add `openai>=1.40` to pyproject.toml dependencies
- [ ] Add 3 deepseek_* fields to Settings
- [ ] Remove `gemini_flash_model`, `gemini_pro_model`, `prompt_cache_*` fields
- [ ] Update `.env.example` DEEPSEEK block + remove GEMINI_FLASH/PRO
- [ ] `pip install -e .` succeeds
- [ ] `python -c "from app.config import settings"` succeeds with deepseek attrs

## Success Criteria
- `python -c "from app.config import settings; assert settings.deepseek_chat_model == 'deepseek-chat'"` passes.
- `python -c "from openai import AsyncOpenAI"` imports cleanly.
- `grep -n "prompt_cache_hit_threshold\|prompt_cache_ttl_seconds\|gemini_flash_model\|gemini_pro_model" app/config.py` returns empty.

## Risk Assessment
- **Low** — pure additive/subtractive config. Breaking change visible at import time (P2 LlmService uses new fields; P3 caller cleanup removes prompt-cache refs).
- Mitigation: do P1 + P2 + P3 in one PR — config + code stay in sync.

## Security Considerations
- `DEEPSEEK_API_KEY` is server-side env only; do not leak via openapi.json / logs.
- `.env` already gitignored; only `.env.example` committed.

## Next Steps
- P2 picks up new settings to construct `AsyncOpenAI` client.
- P3 deletes callers that referenced removed prompt_cache_* settings.
