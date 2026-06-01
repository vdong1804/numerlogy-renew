# Phase 05 — Documentation Sync

## Context Links
- Parent: [plan.md](./plan.md)
- Depends on: P1–P4 merged + tests green.
- Docs to touch (verified via `Glob docs/*.md`):
  - `docs/system-architecture.md`
  - `docs/chatbot-runbook.md`
  - `docs/codebase-summary.md`
  - `docs/project-changelog.md`
  - `docs/chatbot-cost-monitoring.md`
  - (also bump `docs/development-roadmap.md` if migration is listed there)

## Overview
- **Priority:** P1.
- **Status:** pending.
- Sync architecture + ops docs to reflect DeepSeek + removed prompt cache. Note that embeddings remain on Gemini.

## Key Insights
- Cost model differs: DeepSeek pricing is per-1M tokens; previous Gemini explicit-cache savings disappear (auto-cached but accounting model is per-provider).
- Egress now goes to `api.deepseek.com` (CN region) — ops should confirm firewall.
- No DB rollback for prompt_cache data — flagged in changelog.

## Requirements
- Architecture diagram / prose updated.
- Runbook commands updated (env var names, smoke commands).
- Changelog entry written for this migration.
- Cost-monitoring doc reflects new $/Mtok and removed cache savings line item.

## Architecture (diagram in `system-architecture.md`)
```
[Chat router] → LlmService (DeepSeek via openai SDK) → api.deepseek.com
              → EmbeddingService (Gemini text-embedding-004) → ai.googleapis.com
              → SemanticCacheService (pgvector, 768-dim)  // unchanged
              // (Gemini prompt-cache layer removed)
```

## Related Code Files

**Modify (docs only)**
- `docs/system-architecture.md` — replace "Gemini chat + cache" component with "DeepSeek chat (no explicit cache; auto context cache)". Keep embedding component as Gemini.
- `docs/chatbot-runbook.md`:
  - Replace `GEMINI_FLASH_MODEL` / `GEMINI_PRO_MODEL` env references with `DEEPSEEK_*`.
  - Update smoke commands.
  - Add "DeepSeek 5xx → 502 retry guidance" section.
  - Remove "Prompt cache invalidation" section.
- `docs/codebase-summary.md`:
  - Update chat-services index: remove `prompt_cache_service.py`, update `llm_service.py` description.
- `docs/project-changelog.md` — new entry:
  ```
  ## 2026-05-31 — Chat LLM migrated to DeepSeek
  - Replaced Gemini chat with DeepSeek (`deepseek-chat` via OpenAI-compatible SDK).
  - Embeddings remain on Gemini (text-embedding-004, 768-dim).
  - Removed Gemini explicit prompt-cache (service, model, table, scheduled cleanup half).
  - Dropped `prompt_cache_handles` table (alembic <rev>).
  - Config: added DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_CHAT_MODEL; removed GEMINI_FLASH_MODEL / GEMINI_PRO_MODEL / PROMPT_CACHE_*.
  ```
- `docs/chatbot-cost-monitoring.md`:
  - Replace per-Mtok pricing with DeepSeek rates (input cache-miss / hit / output — pull from official pricing page at implementation time).
  - Drop "Gemini explicit cache savings" line item.
  - Note: token counters in DB still meaningful; provider field swap only.

**Create:** none.
**Delete:** none.

## Implementation Steps
1. Edit `system-architecture.md` — chat-LLM component + data-flow diagram.
2. Edit `chatbot-runbook.md` — env vars, smoke, troubleshooting.
3. Edit `codebase-summary.md` — chat-service inventory.
4. Append changelog entry to `project-changelog.md`.
5. Edit `chatbot-cost-monitoring.md` — pricing table + removed savings line.
6. (Optional) Update `development-roadmap.md` if it listed prompt-cache work.
7. Run a final `grep -rn "prompt_cache_handles\|gemini_flash_model\|gemini_pro_model\|cached_content" docs/` — must return empty.

## Todo List
- [ ] `system-architecture.md` updated (chat LLM = DeepSeek)
- [ ] `chatbot-runbook.md` env + smoke + troubleshooting refreshed
- [ ] `codebase-summary.md` service inventory updated
- [ ] `project-changelog.md` entry appended
- [ ] `chatbot-cost-monitoring.md` pricing + cache line updated
- [ ] No stale prompt-cache or Gemini-chat refs in `docs/`

## Success Criteria
- `grep -rn "prompt_cache_handles\|gemini_flash_model\|gemini_pro_model\|cached_content" docs/` returns empty.
- All env var names in docs match `app/config.py`.
- Changelog has a dated entry.

## Risk Assessment
| Risk | L | I | Mitigation |
|------|---|---|-----------|
| Stale runbook commands cause ops mistake | M | M | Pair-review with ops; smoke-test before close |
| Cost numbers go stale fast | H | L | Mark pricing section with "verify against deepseek.com/pricing on review" |
| Forgotten doc file references Gemini chat | L | L | Final grep gate (step 7) |

## Security Considerations
- Do not paste real API keys in docs; use placeholder `${DEEPSEEK_API_KEY}`.

## Next Steps
- Hand off to code-reviewer for final pass.
- Tag release `chat-deepseek-v1`.
