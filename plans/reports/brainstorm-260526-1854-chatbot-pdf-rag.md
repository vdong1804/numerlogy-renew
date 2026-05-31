# Brainstorm Report — Chatbot RAG cho Numerology Platform

**Date:** 2026-05-26
**Type:** Brainstorm / Architecture Decision
**Status:** Pending plan
**Owner:** DongVD

---

## 1. Problem Statement

Thêm chatbot RAG vào Numerology platform để:
- Trả lời câu hỏi user về **báo cáo PDF numerology** (do hệ thống tự generate, user upload lại để hỏi).
- Cung cấp tri thức **numerology/horoscope** từ knowledge base do admin quản lý.
- Phân tầng **free vs paid**: free quota giới hạn câu/ngày, paid mua add-on packages mở rộng quota + dùng model mạnh hơn.

Phải tích hợp với hệ thống hiện hữu: FastAPI + PostgreSQL 16 + Next.js admin + JWT auth + quota/payment package đã có.

---

## 2. Requirements (Đã chốt qua hỏi đáp)

| # | Yêu cầu | Quyết định |
|---|---------|-----------|
| R1 | Nguồn PDF | System-generate + user upload lại |
| R2 | Tier model | Quota theo câu/ngày |
| R3 | LLM stack | Gemini Flash (free) + Gemini Pro (paid) |
| R4 | Vector DB | pgvector trên PostgreSQL có sẵn |
| R5 | Admin KB | 22 bảng numerology + tài liệu PDF/Word admin upload |
| R6 | User PDF flow | Hybrid: match hash trước, fallback parse |
| R7 | Quota integration | Free hard-code + add-on packages (chỉ user đã đăng ký) |
| R8 | UI placement | Trang `/chat` riêng |
| R9 | Features | Streaming + history multi-turn + citation + rate limit |
| R10 | Timeline | Full feature, 3+ tháng |
| R11 | Scale | 1-10k MAU, budget $100-500/tháng |
| R12 | KB ingestion | Auto-sync khi admin CRUD content |

---

## 3. Evaluated Approaches

### 3.1 LLM Provider — Đã chọn Gemini

| Option | Pros | Cons |
|--------|------|------|
| OpenAI GPT-4o | TV tốt, ecosystem dày | Đắt nhất, prompt caching yếu |
| **Gemini 2.0 Flash / 2.5 Pro** ✓ | Rẻ, context 1M, multimodal PDF native, prompt caching hiệu quả | Đôi khi response style không nhất quán |
| Claude Haiku/Sonnet | Reasoning tốt, caching tốt | Đắt hơn Gemini ~3x |

**Rationale:** Budget $500/tháng + 10k MAU → cost-per-msg là ràng buộc cứng. Gemini Flash $0.10/M input rẻ nhất phân khúc. Pro $1.25/M input vẫn rẻ hơn Sonnet. Multimodal native cho phép gửi thẳng PDF khi parse hybrid.

### 3.2 Vector Store — Đã chọn pgvector

| Option | Pros | Cons |
|--------|------|------|
| **pgvector** ✓ | Cùng DB hiện hữu, transaction nhất quán, không thêm service | Recall thấp hơn Qdrant ở >1M chunks |
| Qdrant self-hosted | Performance tốt, filter linh hoạt | +1 service, +1 backup chain |
| Pinecone | Zero-ops | $70/month minimum, vendor lock |

**Rationale:** 22 numerology tables + ~vài trăm PDF/Word admin = <100k chunks. pgvector HNSW index thừa đủ. Đỡ phức tạp ops.

### 3.3 PDF Ingestion Strategy — Đã chọn Hybrid

| Option | Pros | Cons |
|--------|------|------|
| Match-only | Nhanh nhất, không tốn parse | Fail khi user sửa/scan lại |
| Parse-always | Robust | Tốn compute + storage |
| **Hybrid** ✓ | Cân bằng — match SHA256 trước, fallback parse | Code phức tạp hơn |

**Flow:**
1. User upload PDF → compute SHA256.
2. Lookup `numerology_pdf_reports.file_hash` → nếu match: load text + chunks đã embed sẵn từ DB.
3. Nếu miss: extract text (pypdf / Gemini multimodal), chunk, embed, lưu `user_pdf_index` (TTL 30 ngày).

### 3.4 Cost Optimization — Đã chốt Registered-only + Cache

**Estimate 10k MAU (worst case không tối ưu):** ~$1500/tháng.

**Sau optimization:**
- Free: **chỉ registered user, 3 msg/day** (loại bỏ anonymous abuse).
- **Gemini prompt caching** cho system prompt + KB context (giảm input cost 75% với cache hit).
- **Semantic cache** câu hỏi (pgvector similarity): nếu query gần giống câu đã trả lời <24h → return cached.
- Free dùng top-k=3 chunks, Pro dùng top-k=8.

**Estimate sau tối ưu:** $300-450/tháng @ 10k MAU. Trong budget.

---

## 4. Final Recommended Architecture

### 4.1 High-level

```
┌──────────────────────────────────────────────────────────────────┐
│  Next.js Frontend                                                │
│  ├─ /chat (full chat UI: history, streaming, citation panel)     │
│  └─ Admin: /admin/chatbot (KB upload, prompt tuning, analytics)  │
└──────────────────────────────────────────────────────────────────┘
                            │ SSE / HTTPS
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                                 │
│  ├─ /api/chat/conversations  CRUD conversations + messages       │
│  ├─ /api/chat/stream         SSE endpoint (Gemini stream)        │
│  ├─ /api/chat/upload-pdf     Hybrid match/parse                  │
│  ├─ /api/chat/addons         Add-on package purchase             │
│  └─ /api/admin/kb/*          KB CRUD (auto-embed on save)        │
│                                                                  │
│  Services Layer:                                                 │
│  ├─ retrieval_service        pgvector top-k + reranker           │
│  ├─ llm_service              Gemini Flash/Pro + streaming        │
│  ├─ embedding_service        text-embedding-004 (768d)           │
│  ├─ quota_service            daily reset + addon balance         │
│  ├─ cache_service            semantic cache + prompt cache       │
│  └─ pdf_service              SHA256 match + parse fallback       │
└──────────────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────────────┐
│  PostgreSQL 16 + pgvector                                        │
│  ├─ Existing: users, packages, numerology_*, pdf_reports         │
│  ├─ NEW: chat_conversations, chat_messages, chat_quota_usage     │
│  ├─ NEW: chat_addon_packages, chat_addon_purchases               │
│  ├─ NEW: kb_documents, kb_chunks (vector(768))                   │
│  ├─ NEW: user_pdf_index (vector(768), TTL 30d)                   │
│  └─ NEW: semantic_cache (vector(768) + answer + ttl)             │
└──────────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │  Google Gemini API    │
                │  - Flash (free tier)  │
                │  - Pro 2.5 (paid)     │
                │  - Embedding-004      │
                └───────────────────────┘
```

### 4.2 DB Schema (mới thêm)

```sql
-- Knowledge base (admin global)
CREATE TABLE kb_documents (
  id BIGSERIAL PRIMARY KEY,
  source_type TEXT NOT NULL,  -- 'numerology_table' | 'admin_upload'
  source_ref TEXT,            -- e.g. 'attitude:5' hoặc 'upload:uuid'
  title TEXT,
  metadata JSONB,
  created_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE kb_chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id BIGINT REFERENCES kb_documents(id) ON DELETE CASCADE,
  chunk_index INT,
  content TEXT NOT NULL,
  embedding vector(768),
  token_count INT,
  metadata JSONB
);
CREATE INDEX kb_chunks_embedding_idx ON kb_chunks
  USING hnsw (embedding vector_cosine_ops);

-- User PDF (scoped, TTL)
CREATE TABLE user_pdf_index (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  pdf_hash TEXT NOT NULL,
  matched_report_id BIGINT,  -- nếu match được system PDF
  parsed_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 days',
  UNIQUE(user_id, pdf_hash)
);

CREATE TABLE user_pdf_chunks (
  id BIGSERIAL PRIMARY KEY,
  pdf_index_id BIGINT REFERENCES user_pdf_index(id) ON DELETE CASCADE,
  chunk_index INT,
  content TEXT,
  embedding vector(768)
);
CREATE INDEX user_pdf_chunks_embedding_idx ON user_pdf_chunks
  USING hnsw (embedding vector_cosine_ops);

-- Conversation
CREATE TABLE chat_conversations (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  title TEXT,
  pdf_context_id BIGINT REFERENCES user_pdf_index(id),  -- nullable
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
  id BIGSERIAL PRIMARY KEY,
  conversation_id BIGINT REFERENCES chat_conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL,  -- 'user' | 'assistant' | 'system'
  content TEXT,
  model_used TEXT,     -- 'gemini-2.0-flash' | 'gemini-2.5-pro'
  tier TEXT,           -- 'free' | 'paid'
  input_tokens INT,
  output_tokens INT,
  citations JSONB,     -- [{chunk_id, document_id, score}]
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX chat_messages_conv_idx ON chat_messages(conversation_id, created_at);

-- Quota
CREATE TABLE chat_quota_usage (
  user_id BIGINT REFERENCES users(id),
  date DATE,
  free_used INT DEFAULT 0,
  paid_used INT DEFAULT 0,
  PRIMARY KEY (user_id, date)
);

CREATE TABLE chat_addon_packages (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  price NUMERIC(10,2),
  message_count INT,        -- VD: 100 câu hỏi
  tier TEXT,                -- 'pro' | 'flash'
  validity_days INT,        -- VD: 30 ngày
  is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE chat_addon_purchases (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  package_id BIGINT REFERENCES chat_addon_packages(id),
  remaining_messages INT,
  tier TEXT,
  purchased_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  payment_id BIGINT  -- liên kết hệ thanh toán hiện có
);

-- Semantic cache (FAQ + recent answers)
CREATE TABLE semantic_cache (
  id BIGSERIAL PRIMARY KEY,
  query_embedding vector(768),
  query_text TEXT,
  answer TEXT,
  citations JSONB,
  hit_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);
CREATE INDEX semantic_cache_idx ON semantic_cache
  USING hnsw (query_embedding vector_cosine_ops);
```

### 4.3 Chat Request Flow

```
User gửi message
  │
  ├─[1] Auth check (JWT) — anonymous bị từ chối
  │
  ├─[2] Quota check
  │     ├─ Có addon active? → dùng addon (model=tier), giảm remaining
  │     ├─ Free used < 3 today? → free tier (Flash)
  │     └─ Hết quota → 402 + upsell addon
  │
  ├─[3] Semantic cache lookup
  │     ├─ Embed query → top-1 cosine similarity > 0.92? → return cached
  │     └─ Miss → tiếp tục
  │
  ├─[4] Retrieval
  │     ├─ Embed query (Gemini text-embedding-004)
  │     ├─ pgvector top-k từ kb_chunks (k=3 free / k=8 paid)
  │     ├─ Nếu conversation có pdf_context_id → cũng top-k từ user_pdf_chunks
  │     └─ Merge + sort by score
  │
  ├─[5] Prompt construction (with Gemini prompt caching)
  │     ├─ System prompt (cached) + KB chunks + history (5 msg gần nhất) + user msg
  │     └─ Citation instruction: "trích nguồn theo [1], [2]..."
  │
  ├─[6] LLM streaming
  │     ├─ Gemini stream → SSE → frontend
  │     └─ Đồng thời accumulate tokens
  │
  ├─[7] Persist
  │     ├─ Insert chat_messages (user + assistant)
  │     ├─ Update chat_quota_usage
  │     └─ Nếu hữu ích → insert semantic_cache
  │
  └─[8] Return citations payload (frontend hiển thị panel)
```

### 4.4 Phase Plan (3-month roadmap)

| Phase | Tuần | Nội dung |
|-------|------|----------|
| **P1: Foundation** | 1-2 | DB schema, pgvector setup, embedding service, KB ingestion từ 22 bảng numerology |
| **P2: Core Chat** | 3-4 | Non-streaming chat endpoint, retrieval, citation, conversation/message CRUD |
| **P3: User PDF** | 5-6 | Upload endpoint, SHA256 match, fallback parse (pypdf), per-user index, TTL cleanup |
| **P4: Streaming + UI** | 7-8 | SSE endpoint, Next.js /chat page (markdown render, citation panel, history sidebar) |
| **P5: Quota + Addons** | 9-10 | chat_quota_usage logic, addon packages CRUD admin, purchase flow tích hợp payment hiện có |
| **P6: Cache + Rate limit** | 11 | Semantic cache, prompt caching Gemini, rate limit per user+IP, captcha sau N failed |
| **P7: Admin tuning** | 12 | Admin upload PDF/Word vào KB, prompt template editor, conversation viewer, analytics dashboard |
| **P8: Hardening** | 13+ | Cost monitoring, abuse detection, A/B test prompts, fine-tune retrieval thresholds |

### 4.5 Rate Limit Strategy

- **Free user:** 3 msg/day + 1 msg/10s (anti-burst).
- **Paid (addon active):** package limit + 1 msg/3s.
- **IP-based:** 50 msg/IP/day toàn platform (chặn bot farm acc).
- **Failed/abuse signals:** sau 5 lần CAPTCHA fail → cooldown 1h.
- Implement bằng Redis token bucket (nếu chưa có Redis, dùng PostgreSQL row lock — chậm hơn nhưng đủ ở scale này).

---

## 5. Implementation Considerations & Risks

### 5.1 Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Chi phí Gemini vượt budget | High | Semantic cache, prompt cache, free tier 3/day, monitor daily cost với cảnh báo $400 |
| pgvector recall thấp khi data lớn | Med | Set ef_search = 100, theo dõi recall, có sẵn migration sang Qdrant nếu >500k chunks |
| Hallucination khi KB không có thông tin | High | "Tôi không có thông tin về..." prompt, threshold similarity < 0.6 → từ chối trả lời |
| User upload PDF không phải report numerology | Med | Validate magic bytes + heuristic check title page; reject nếu không match pattern |
| PII leak qua conversation history | High | Mã hóa at-rest, không log prompt + response ra file log, DSAR delete endpoint |
| Streaming SSE timeout qua Nginx | Med | Cấu hình `proxy_read_timeout 300s` + heartbeat keepalive |
| Embedding model thay đổi → reindex toàn bộ | Low | Lưu model_version trong kb_chunks, migration job khi đổi |
| Add-on payment fail giữa chừng | High | Idempotent webhook, transaction wrap purchase + balance update |

### 5.2 Security

- JWT bắt buộc → middleware từ chối anonymous.
- Conversation thuộc user — check `user_id == JWT.user_id` mọi lookup.
- Admin KB upload — virus scan (ClamAV) + giới hạn 50MB.
- Rate limit theo `(user_id, ip)` tuple — chặn share account.
- Prompt injection: filter system prompt khỏi user input (prepend role markers), từ chối query chứa "ignore previous instructions" patterns.
- PDF parser: sandbox pypdf (resource limit) tránh malicious PDF.

### 5.3 Modularity (KISS + DRY)

Đề xuất layout file (mỗi file <200 LOC theo rule):

```
app/services/chat/
  ├─ embedding_service.py        # wrap Gemini embedding
  ├─ retrieval_service.py        # pgvector queries + merge
  ├─ llm_service.py              # Gemini stream + non-stream
  ├─ prompt_builder.py           # system + history + KB + citation
  ├─ semantic_cache_service.py   # cache lookup/insert
  ├─ quota_service.py            # daily + addon
  ├─ pdf_match_service.py        # hash match + parse
  └─ rate_limit_service.py       # token bucket

app/api/chat/
  ├─ conversations.py            # CRUD
  ├─ stream.py                   # SSE endpoint
  ├─ upload.py                   # PDF upload
  └─ addons.py                   # purchase + balance

app/models/chat/                 # SQLAlchemy models, 1 file per entity
app/schemas/chat/                # Pydantic DTOs
```

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| First message response latency (free) | < 2.5s |
| Streaming first token | < 1.2s |
| Cache hit rate | > 25% sau 1 tháng vận hành |
| Citation accuracy (manual sample 100 msg) | > 85% trích đúng nguồn |
| Hallucination rate (manual eval) | < 5% |
| Free→Paid conversion rate | > 3% |
| Monthly LLM cost @ 5k MAU | < $300 |
| Monthly LLM cost @ 10k MAU | < $500 |
| Quota abuse incidents/month | < 10 |

---

## 7. Cost Projection Detail

**Giả định:** 10k MAU, 30% active hàng tháng, 60% trong active dùng chat.

| Item | Volume | Rate | Cost |
|------|--------|------|------|
| Embedding (KB indexing one-time + delta) | ~5M tokens | $0.025/M | $0.125 |
| Embedding (query) | ~500k queries × 50 tokens | $0.025/M | $0.625 |
| Gemini Flash (free tier msgs) | ~400k msgs × 2000 in + 400 out | $0.10/M in + $0.40/M out | $80 + $64 = $144 |
| Gemini Pro (paid msgs) | ~80k msgs × 4000 in + 800 out | $1.25/M in + $5/M out | $400 + $320 = $720 |
| Prompt caching savings | 60% cache hit input | -75% trên cached | -$280 |
| Semantic cache savings | 25% query hit | -100% trên cached | -$170 |
| **Total** | | | **~$415/tháng** |

Trong budget $500. Có biên an toàn 15%.

---

## 8. Next Steps & Dependencies

### Dependencies (phải ready trước khi build)

1. Google Cloud project + Gemini API key (Vertex AI nếu cần SLA).
2. pgvector extension installed trên PG16 (`CREATE EXTENSION vector`).
3. Redis (optional) cho rate limit + addon balance cache.
4. Existing payment integration phải support thêm package type "chat_addon".
5. Admin UI route mới `/admin/chatbot` (KB upload + prompt tuning).

### Open / Unresolved Questions

1. **Free anonymous vs registered:** đã chốt registered-only, nhưng có cần demo mode (1 câu thử cho khách) để increase conversion không?
2. **Pricing add-on packages:** chưa định giá VND. Cần đề xuất 3 mức (basic/standard/premium) tham khảo PDF package hiện có.
3. **Conversation retention:** giữ lịch sử bao lâu? 30/90/365 ngày? Ảnh hưởng GDPR/disk.
4. **Multimodal PDF qua Gemini native:** thay vì pypdf parse, có thể gửi PDF binary cho Gemini Flash multimodal — đắt hơn nhưng accuracy cao hơn cho scan/image-based PDF. Trade-off cần test sample.
5. **Admin có cần override prompt per-package không** (VD: package "Premium" dùng prompt khác)? Hiện thiết kế 1 prompt template global.
6. **Localization:** UI tiếng Việt là chính, có cần i18n từ đầu cho prompt template (VN/EN) không?
7. **Rerank model:** sau pgvector top-k có cần rerank (cross-encoder) cho paid tier không? Tăng chất lượng nhưng +200ms latency.

---

## 9. Recommended Decision

Build theo kiến trúc trên với 8-phase roadmap. **Bắt đầu Phase 1 (DB schema + embedding service + KB ingestion)** để sớm có baseline đo lường cost thực tế trước khi đầu tư UI.

**Critical guardrail:** sau Phase 2 (basic chat hoạt động) phải có **cost dashboard** trước khi mở public — tránh blow budget trong tuần đầu launch.
