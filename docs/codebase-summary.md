# Codebase Summary

**Last Generated:** 2026-05-28  
**Scope:** numerology-api (FastAPI backend) + Numerology-Landing-Page (Next.js frontend)

> **Phase 06 Highlights (Chatbot RAG — Semantic Cache + Prompt Cache + Rate Limit):**
> - Backend: `app/services/chat/semantic_cache_service.py` (pgvector cosine lookup, tier-scoped, 24h TTL, NO_INFO exclusion), `app/services/chat/rate_limit_service.py` (two-bucket atomic, user+IP, fail-closed, Asia/Bangkok TZ for daily reset), `app/services/chat/prompt_cache_service.py` (SHA256 cache_key, lazy threshold 5, TTL 1h refresh, broad-strokes invalidation), `app/utils/network.py` (get_client_ip), `app/jobs/cleanup_semantic_cache.py` (03:15 nightly cleanup)
> - Backend models/schema: `semantic_cache_entry`, `rate_limit_bucket`, `prompt_cache_handle` tables; `MessageOut.from_cache` field
> - Alembic 0013: adds 3 new tables + HNSW index (requires pgvector ≥0.5.0)
> - Backend modified: `messages.py` (pipeline order: rate limit → quota → retrieval → semantic cache lookup → prompt cache → LLM → cache insert), `_stream_generator.py` (same pipeline, stream variant), `llm_service.py` (+cached_content kwarg, google-genai 1.47.0 confirmed)
> - Frontend: `use-rate-limit-countdown.ts` hook, `useRateLimitCountdown` countdown hint + button disable, HTTP 429 handler with Retry-After parsing, Sonner toast variants (bucket_empty, daily_cap)
> - Scheduler: `cleanup_semantic_cache.run()` wired at `cron(hour=3, minute=15)` UTC
> - Tests: 345 total pass, 0 failed (4 pre-existing pgvector skips). Ruff + tsc + lint clean.
> - Code review: 3 critical + 10 high flagged; blocking issues (prompt-cache invalidation on every KB re-sync, daily_cap TZ mismatch, rate-limit lock held during LLM) require decision; fail-closed policy + Asia/Bangkok daily reset documented
>
> **Phase 05 Highlights (Chatbot RAG — Chat Quota + Add-on Packages):**
> - Backend: `app/services/chat/quota_service.py` (200 LOC, QuotaService + QuotaDecision + QuotaConflictError), `app/services/chat/addon_fulfillment.py` (88 LOC, idempotent fulfillment with payment_id uniqueness), `app/routers/chat/addons.py` (97 LOC, GET /api/chat/addons + POST .../purchase), `app/routers/chat/quota.py` (42 LOC, GET /api/chat/quota), `app/db/models/chat/chat_addon_purchase.py`, `app/schemas/chat/addon.py`
> - Backend modified: `messages.py` (quota gate + sync decrement, 212 LOC), `_stream_generator.py` (quota decrement pre-commit, 132 LOC), `payment_service.py` (branched on package_kind), `packages` table +package_kind/message_count/tier/validity_days columns
> - Alembic 0012: chat_addon_purchases table + packages columns
> - SePay webhook extended: branched matcher for NSQ vs CHATADDON{id} content
> - Frontend: `use-quota.ts`, `QuotaBadge.tsx`, `UpsellModal.tsx`, `/chat/upgrade` page + AddonList/AddonCard, `use-chat-stream` +onQuotaExceeded callback
> - Admin: package-form gained package_kind selector + conditional ChatAddonFields (message_count, tier, validity_days) with zod validation
> - Tests: 290 total pass (post-Phase 05), 0 failed. tsc + lint clean.
>
> **v1.4 update (2026-05-26):** Admin order management (search/filter/export CSV with injection sanitization), SEO image fixes (alt text, next/image migration), go-live runbooks. See `docs/project-changelog.md` v1.4 entry.
>
> **Phase 04 Highlights:**
> - Backend: `app/services/csv_export_service.py` (110 LOC, UTF-8 BOM, formula-injection sanitized), `app/routers/admin/orders.py` extended with email/ref_code/status/date filters (ILIKE partial match + escape_like helper), `app/utils/query.py::escape_like()` (escapes \, %, _ for ILIKE safety), `Order.refunded_at` mapped in model
> - Backend config: no new env vars
> - Frontend: `src/lib/admin-dashboard-api.ts` +searchOrders/exportOrdersCsv, `src/components/admin/order-search-form.tsx` (110 LOC, TZ contract helper, "Xóa lọc" reset, "Xuất CSV" export), `src/pages/admin/orders/index.tsx` rewritten (175 LOC, pagination, empty state)
> - SEO: `src/modules/home/TeacherInfo.tsx` img→next/image (bg-teacher 627KB), `src/modules/home/Banner.tsx` img→next/image (adalash_banner 317KB), fixed alt text on 3 images, created `docs/image-audit.md` (10 img tags tracked, 6 deferred, 4 CSS bg ~5.6MB noted)
> - Docs added: `go-live-runbook.md` (pre-flight 16 items, deploy 12 steps, rollback, comms), `post-launch-monitoring.md` (daily/weekly checks, alert thresholds, escalation)
> - Tests: 173/190 pass (17 pre-existing unchanged, 0 regressions), frontend build clean (94 pages)
> - Fixed: C1 http_http_status typo, H1 ILIKE wildcard escape, H2 CSV formula injection sanitize, H3 DatePicker Bangkok TZ contract, H5 exportOrdersCsv JSON error UX
>
> **v1.3 update (2026-05-26):** Added security (rate limiting, Turnstile CAPTCHA, Nginx headers), email deliverability (plain-text fallbacks, multipart), UX (FAQ, guide, empty states, skeletons), config cleanup. See `docs/project-changelog.md` v1.3 entry.
>
> **Phase 03 Highlights:**
> - Backend: `app/middleware/rate_limit.py` (slowapi, CF-Connecting-IP priority, trusted_proxy_mode setting), `app/services/turnstile_service.py` (httpx async verify, fail-closed, dev skip, startup assertion), rate limit decorators on /auth endpoints, 6 plain-text email fallbacks (.txt), multipart dispatch in `email_outbox_service`, base.html unsubscribe footer with Jinja inheritance
> - Backend config: TURNSTILE_SECRET_KEY, RATE_LIMIT_ENABLED, TRUSTED_PROXY_MODE, startup check for production turnstile secret
> - Frontend: `src/components/turnstile-widget.tsx` (dev fallback guarded by NODE_ENV, prod error on missing siteKey), `src/components/empty-state.tsx`, 3 skeleton components (order-card, report-card, shop-item), `/faq` (15 Q&A, 3 groups, <details> accordion, SSG), `/huong-dan` (5-step guide, placeholder images, SSG)
> - Frontend modified: register.tsx + forgot-password.tsx (TurnstileWidget, captcha_token state, disabled submit), my-account orders/reports (EmptyState + skeleton loaders), Footer.tsx (FAQ + Hướng dẫn links), next.config.js (OAuth env cleanup, NEXT_PUBLIC_TURNSTILE_SITE_KEY, ignore flags retained with TODO)
> - Nginx: 5 security headers (HSTS 2yr, XFO, XCTO, Referrer-Policy, Permissions-Policy, CSP corrected for cms.nhansinhquan.vn + challenges.cloudflare.com + www.facebook.com)
> - Docs added: `lint-cleanup-backlog.md` (100+ pre-existing admin lint issues, Phase 04 deferred sprint)
>
> **Phase 01+02 Highlights:**
> - Backend: `utils/signed_url.py` (HMAC-SHA256 7d tokens), `jobs/reconcile_sepay.py` (15min cron, SePay tx dedup), services extended (refund_order, list_recent_transactions)
> - Backend routers: `admin/orders.py` +refund endpoint, `my_account.py` +signed-token download
> - Backend models: migration `0008` (orders.admin_notes, orders.refunded_at, status enum +refunded)
> - Backend templates: `order-paid.txt`, `order-refund.html|txt`
> - Backend config: Sentry init with PII scrubber, NEXT_PUBLIC_SENTRY_DSN + SENTRY_DSN + ENVIRONMENT + RECONCILE_WINDOW_HOURS
> - Frontend: 4 SSG legal pages (/terms /privacy /refund-policy /contact), `components/cookie-consent.tsx`, `components/analytics.tsx`, `lib/consent-storage.ts`
> - Frontend config: `sentry.client|server|edge.config.ts`, `next-sitemap.config.js`, `robots.txt`, `manifest.json`, Organization JSON-LD
> - Frontend: Meta layout extended (canonical, OG, Twitter, favicon), Footer LEGAL_LINKS, Analytics component with consent gating, refund button on order detail
> - Docs added: `analytics-events.md`, `legal-content-sources.md`, `runbook-payment-incident.md`

---

## Backend Directory Tree (numerology-api/)

```
numerology-api/
├── README.md                    # Quick start + seeding guide
├── pyproject.toml              # Python dependencies (FastAPI, SQLAlchemy, Pydantic)
├── .env.example                # Environment template
├── Dockerfile                  # FastAPI container image
├── docker-compose.yml          # Local dev stack (api + postgres)
│
├── app/                        # Main package
│   ├── main.py                 # FastAPI factory, router registration, CORS
│   ├── config.py               # Pydantic settings (reads .env)
│   ├── deps.py                 # Dependency injection (get_db, get_current_user, get_current_superuser)
│   │
│   ├── db/
│   │   ├── base.py             # SQLAlchemy DeclarativeBase + Base class
│   │   ├── session.py          # Async engine, sessionmaker, AsyncSession
│   │   └── models/
│   │       ├── mixins.py       # TimestampMixin (created_at, updated_at)
│   │       ├── user.py         # User, UserProfile, UserDownload models
│   │       ├── auth.py         # RefreshToken, SocialAccount models
│   │       ├── numerology_content.py  # 22 content tables (attitude, balance, etc.)
│   │       ├── package.py      # Package, UserPackage, UserPayment, Bank models
│   │       ├── news.py         # News model
│   │       └── __init__.py     # Exports all models for Alembic
│   │
│   ├── core/
│   │   ├── security.py         # Hash/verify password (bcrypt), JWT creation
│   │   ├── oauth.py            # Google/Facebook OAuth config (Authlib)
│   │   ├── numerology.py       # Main calculate_numerology_numbers() function (170 LOC)
│   │   ├── numerology_sums.py  # Helper: get_sum(), get_sum_spec(), etc.
│   │   └── alphabet.py         # Vietnamese accents mapping + strip_accents()
│   │
│   ├── routers/
│   │   ├── auth.py             # POST /auth/register, login, refresh, logout, GET /auth/me, /auth/google*, /auth/facebook*
│   │   ├── numerology.py       # Assembly router (includes free + paid sub-routers)
│   │   ├── numerology_free.py  # GET /api/so-hoc-free, /api/la-so, /api/ (debug preview)
│   │   ├── numerology_paid.py  # GET /api/so-hoc (auth + quota-gated PDF)
│   │   ├── profile.py          # GET /profile/me, PUT /profile/me, POST /profile/birthday
│   │   ├── news.py             # GET /news, /news/{id}
│   │   ├── packages.py         # GET /packages, /packages/{id}
│   │   ├── banks.py            # GET /banks, /banks/{id}
│   │   ├── payments.py         # POST /payments (create), GET /payments (list user's)
│   │   └── admin/
│   │       ├── content.py      # GET/POST/PUT/DELETE /admin/content/{resource_name}/{id} (all 23 tables)
│   │       ├── users.py        # GET/PUT /admin/users, /admin/users/{id}
│   │       ├── payments.py     # GET /admin/payments, POST /admin/payments/{id}/approve|reject
│   │       └── uploads.py      # POST /admin/upload (image/file multipart)
│   │
│   ├── services/
│   │   ├── user_service.py     # User CRUD, superuser validation
│   │   ├── token_service.py    # JWT + refresh token generation, validation
│   │   ├── numerology_db.py    # Fetch numerology content by code (23 content tables)
│   │   ├── numerology_context.py # Build Jinja2 context, save download, decrement quota
│   │   ├── numerology_service.py # Thin facade (re-exports numerology_db + context)
│   │   ├── horoscope_client.py  # Async httpx wrapper for vietheart.net API
│   │   ├── payment_service.py   # Payment approval workflow
│   │   └── upload_service.py    # File upload validation (MIME, size)
│   │
│   ├── schemas/
│   │   ├── auth.py             # TokenOut, LoginRequest, RegisterRequest, OAuthCallbackRequest
│   │   ├── numerology.py       # SoHocQuery, SoHocFreeQuery, LasoQuery, CalcResponse, PDFResponse
│   │   ├── profile.py          # UserOut, ProfileOut, ProfileUpdate, BirthdayUpdate
│   │   ├── user.py             # [if separate]
│   │   ├── content.py          # ContentCreate, ContentUpdate (generic, used by admin)
│   │   ├── news.py             # NewsCreate, NewsUpdate, NewsOut
│   │   ├── package.py          # PackageCreate, PackageUpdate, PackageOut
│   │   ├── bank.py             # BankCreate, BankUpdate, BankOut
│   │   ├── payment.py          # PaymentCreate, PaymentApprovalRequest, PaymentOut
│   │   └── common.py           # PaginationParams, PaginatedResponse, ErrorResponse
│   │
│   ├── utils/
│   │   ├── pdf.py              # render_html() (Jinja2), render_pdf() (async wkhtmltopdf)
│   │   └── pagination.py       # paginate() helper, PaginationParams schema
│   │
│   ├── templates/
│   │   ├── invoice.html        # Paid PDF template (Jinja2, ported from Django)
│   │   └── invoice-free.html   # Free PDF template (Jinja2, ported from Django)
│   │
│   └── __init__.py             # Package init
│
├── alembic/                    # Database migrations
│   ├── versions/
│   │   ├── 0001_initial_schema.py    # Create 31 tables
│   │   └── 0002_auth_tables.py       # Create refresh_tokens + social_accounts
│   ├── env.py                  # Alembic config (reads DB_URL from env)
│   ├── script.py.mako          # Migration template
│   └── alembic.ini             # Alembic settings
│
├── tests/                      # Pytest suite
│   ├── conftest.py             # Fixtures (db_session, client, user)
│   ├── test_auth.py            # Auth endpoint tests
│   ├── test_numerology.py      # Calc + PDF endpoint tests
│   ├── test_user_service.py    # User service unit tests
│   └── ... (other test modules)
│
├── scripts/                    # One-off scripts
│   ├── seed_all.py             # Master seeding (calls all seed_*.py)
│   ├── seed_content.py         # Populate 22 numerology content tables
│   ├── seed_packages.py        # Create Free/Basic/Premium packages
│   ├── seed_banks.py           # Create sample bank info
│   └── create_superuser.py     # Create admin user interactively
│
└── deploy/                     # Production deployment
    ├── README.md               # Deployment guide (setup order, one-liner deploy)
    ├── docker-compose.prod.yml # Production stack (api + db + nginx)
    ├── nginx.conf              # SSL, gzip, reverse proxy, media serving
    ├── env.prod.example        # Production env template
    ├── deploy.sh               # One-command deploy script
    ├── backup.sh               # Daily Postgres backup + rotation
    ├── cutover.md              # Runbook: Django → FastAPI migration (30min downtime)
    ├── rollback.md             # Runbook: Rollback if cutover fails (<10min)
    └── .gitignore              # Exclude .env.prod, certs, logs
```

**Backend Summary by Directory:**

| Directory | Purpose | Key Files | LOC |
|-----------|---------|-----------|-----|
| `app/` | Main FastAPI package | main.py, config.py, deps.py | 200 |
| `app/db/` | Database layer | models/, session.py, base.py | 400 |
| `app/core/` | Business logic | numerology.py, security.py, oauth.py | 350 |
| `app/routers/` | API endpoints | auth.py, numerology_*.py, admin/ | 800 |
| `app/services/` | Service layer | user_service.py, numerology_context.py | 600 |
| `app/schemas/` | Pydantic models | auth.py, numerology.py, common.py | 500 |
| `app/utils/` | Helpers | pdf.py, pagination.py | 150 |
| `app/templates/` | Jinja2 templates | invoice.html, invoice-free.html | 700 |
| `alembic/` | DB migrations | versions/ | 300 |
| `tests/` | Test suite | test_*.py (≥70% coverage) | 1200 |
| `scripts/` | Setup scripts | seed_*.py, create_superuser.py | 400 |
| `deploy/` | Production | docker-compose.prod.yml, nginx.conf, runbooks | 600 |

---

## Frontend Directory Tree (Numerology-Landing-Page/src/)

```
Numerology-Landing-Page/
├── package.json                # Dependencies (Next.js, Tailwind, TipTap, TanStack Table)
├── .env.example                # NEXT_PUBLIC_API_BASE env template
├── tsconfig.json               # TypeScript config
├── tailwind.config.js          # Tailwind CSS setup
├── next.config.js              # Next.js config
│
└── src/
    ├── pages/
    │   ├── index.tsx           # Landing page
    │   ├── numerology/
    │   │   ├── so-hoc.tsx      # Paid reading (login + quota)
    │   │   ├── so-hoc-free.tsx # Free reading (phone validation)
    │   │   └── la-so.tsx       # Horoscope chart
    │   │
    │   └── admin/
    │       ├── index.tsx       # Admin dashboard (stat cards + resource grid)
    │       ├── login.tsx       # Email/pw login (email → JWT)
    │       ├── users/
    │       │   ├── index.tsx   # User list (paginated, searchable)
    │       │   └── [id].tsx    # User detail + edit
    │       ├── content/
    │       │   ├── [resource]/
    │       │   │   ├── index.tsx   # List (table + search + paginate)
    │       │   │   ├── new.tsx     # Create form
    │       │   │   └── [id].tsx    # Edit + delete
    │       ├── news/
    │       │   ├── index.tsx   # News list
    │       │   ├── new.tsx     # Create news
    │       │   └── [id].tsx    # Edit/delete news
    │       ├── packages/
    │       │   ├── index.tsx   # Package list
    │       │   ├── new.tsx     # Create package
    │       │   └── [id].tsx    # Edit/delete package
    │       ├── banks/
    │       │   ├── index.tsx   # Bank list
    │       │   ├── new.tsx     # Create bank
    │       │   └── [id].tsx    # Edit/delete bank
    │       └── payments/
    │           ├── index.tsx   # Pending/all payments + status filter
    │           └── [id].tsx    # Payment detail + approve/reject
    │
    ├── components/
    │   ├── admin/              # Admin-specific components
    │   │   ├── admin-layout.tsx     # Sidebar nav + topbar + auth guard (173 LOC)
    │   │   ├── rich-text-editor.tsx # TipTap editor + image upload (152 LOC)
    │   │   ├── content-table.tsx    # TanStack Table generic (197 LOC)
    │   │   ├── content-form.tsx     # Form builder (126 LOC)
    │   │   ├── content-form-fields.tsx # Form field components (108 LOC)
    │   │   ├── generic-crud-form.tsx # Reusable CRUD form (121 LOC)
    │   │   ├── confirm-dialog.tsx   # Delete confirm modal (89 LOC)
    │   │   └── payment-approval-card.tsx # Payment action card (164 LOC)
    │   │
    │   └── [public pages components]
    │
    ├── lib/
    │   ├── admin-api.ts        # API fetch wrapper (Bearer token, error guard)
    │   ├── admin-auth.ts       # useAdminAuth() hook (/auth/me guard + logout)
    │   └── content-resources.ts # 23-slug registry (table names + Vietnamese labels)
    │
    ├── styles/
    │   └── globals.css         # Tailwind imports
    │
    └── [other public components, hooks, utils]
```

**Frontend Summary by Directory:**

| Directory | Purpose | Key Files | Count |
|-----------|---------|-----------|-------|
| `pages/admin/` | Admin pages | login, content, users, news, packages, banks, payments | 18 |
| `components/admin/` | Admin UI components | admin-layout, rich-text-editor, content-table, forms, dialogs | 8 |
| `pages/chat.tsx` | Chat page | Auth guard + ChatLayout wrapper | 1 |
| `modules/chat/` | Chat module (Phase 04) | parts/, hooks/, api/, models/Chat.ts | 13 files |
| `lib/` | API + utilities | admin-api, admin-auth, content-resources, chat-api | 4 |
| `pages/` | Public pages | index, numerology/*, /chat | ~5 |
| `components/` | Public components | [existing] + turnstile, empty-state, skeletons | ~20 |

**Chat Module (src/modules/chat/ — Phase 04 + Phase 05):**
| File | LOC | Purpose |
|------|-----|---------|
| `api/chat-api.ts` | 100 | Axios wrappers: listConversations, createConversation, deleteConversation, listMessages, uploadPdf, clearPdfContext |
| `hooks/use-conversations.ts` | 62 | List/create/delete conversations with useState |
| `hooks/use-messages.ts` | 48 | Fetch message history for active conversation |
| `hooks/use-chat-stream.ts` | 228 | SSE consumer — while-loop pump, token batching via rAF, fullTextRef stale-closure-safe; Phase 05: onQuotaExceeded callback |
| `hooks/use-pdf-upload.ts` | 58 | Multipart PDF upload, client-side size/type guard |
| `hooks/use-quota.ts` | 42 | Phase 05: getQuota hook, 10s polling, 5min cap |
| `parts/MessageMarkdown.tsx` | 88 | react-markdown + remark-gfm + rehype-sanitize; [N] → clickable citation spans |
| `parts/CitationDrawer.tsx` | 78 | Slide-in right Sheet with citation detail, score bar |
| `parts/PdfUploadButton.tsx` | 82 | File picker button + attached-pill state + remove |
| `parts/ConversationSidebar.tsx` | 96 | Conversation list + New button + delete with ConfirmDialog |
| `parts/MessageInput.tsx` | 118 | Auto-expanding textarea (≤8 rows), Enter/Shift+Enter, send + cancel buttons |
| `parts/MessageThread.tsx` | 204 | History + streaming bubble + skeleton loading + auto-scroll with isNearBottom guard |
| `parts/QuotaBadge.tsx` | 45 | Phase 05: Display free/addon quota remaining + tier badge |
| `parts/UpsellModal.tsx` | 78 | Phase 05: Modal showing bank info for purchase, 5-10s polling after payment |
| `upgrade/index.tsx` | 92 | Phase 05: /chat/upgrade page with AddonList + purchase form |
| `upgrade/AddonList.tsx` | 68 | Phase 05: List of chat addon packages, searchable |
| `upgrade/AddonCard.tsx` | 52 | Phase 05: Package card with message count, tier, price, purchase button |
| `ChatLayout.tsx` | 204 | 3-column layout shell — wires all hooks, desktop sidebar + mobile Sheet; Phase 05: quota display + upsell modal |

**Header Integration (Phase 04):**
- `src/layouts/Header.tsx` modified: Added "Chat AI" button (desktop) + "Chat AI" MenuItem (mobile drawer)
- Visible only when `user !== null` (authenticated users only)
- Links to `/chat` page

---

## Database Schema (31 Tables)

### Numerology Content (22 tables)
All use `NumerologyContentMixin`: id (PK), code (U), number (U), title, content, number_page.

**Standard content tables (21):**
```
attitude_number, balance_number, birthday_chart, birthday_number, 
challenge_life, deficit_number, development_number, execution_number, 
identifiable, introspective_number, karmic_number, mature_number, 
miss_number, mission_number, name_chart, peak_life, personal_month_number, 
personal_year_number, phone_number, souls_number, stages_of_life
```

**Special content:**
- `main_number`: +content_2, content_3, content_4, content_5 (master numbers)
- `phone_master_data`: id, code, bow (no mixin)

### User & Authentication (4 tables)
- `users`: id, email (U), hashed_password, is_superuser, created_at, updated_at
- `user_profiles`: id, user_id (FK→users, 1-1), birthday, gender, address, quota, updated_at
- `refresh_tokens`: id, user_id (FK→users, indexed), token_hash (U, indexed), expires_at, revoked_at, created_at
- `social_accounts`: id, user_id (FK→users), provider, provider_user_id, email, created_at (U(provider, provider_user_id))

### Business & Transactions (5 tables)
- `packages`: id, name, price, quota, renewal_days, created_at
- `user_packages`: id, user_id (FK→users), package_id (FK→packages), expires_at
- `user_payments`: id, user_id (FK→users), amount, status (pending/approved/rejected), bank, reference, created_at
- `banks`: id, code, name, account, icon_url
- `news`: id, slug (U), title, html_content, featured_image, created_at, updated_at

### Downloads & Audit (1 table)
- `user_downloads`: id, user_id (FK→users), type (0=free, 1=paid, CHECK), created_at

---

## API Endpoint Groups

### Authentication (`/auth`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/register` | none | Email/pw signup → TokenOut |
| POST | `/auth/login` | none | Email/pw login → TokenOut |
| POST | `/auth/refresh` | none | Refresh token → new TokenOut |
| POST | `/auth/logout` | none | Revoke refresh token → 204 |
| GET | `/auth/me` | Bearer | Current user + profile |
| GET | `/auth/google` | none | OAuth start (redirect) |
| GET | `/auth/google/callback` | none | OAuth callback → token in URL |
| GET | `/auth/facebook` | none | OAuth start (redirect) |
| GET | `/auth/facebook/callback` | none | OAuth callback → token in URL |

### Numerology — Free (`/api`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/so-hoc-free` | none | Free reading (phone validation) |
| GET | `/api/la-so` | none | Horoscope chart (vietheart.net) |
| GET | `/api/` | none | Debug HTML preview (invoice-free) |

### Numerology — Paid (`/api`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/so-hoc` | Bearer JWT | Paid PDF (quota-gated, quota decrement) |

### Profile (`/profile`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/profile/me` | Bearer | User + profile data |
| PUT | `/profile/me` | Bearer | Update name, address, gender |
| POST | `/profile/birthday` | Bearer | Set/update birthday |

### Content — Public (`/content`, `/news`, `/packages`, `/banks`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/news` | none | News list (paginated) |
| GET | `/news/{id}` | none | News detail |
| GET | `/packages` | none | Package list |
| GET | `/packages/{id}` | none | Package detail |
| GET | `/banks` | none | Bank list |

### Payments (`/payments`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/payments` | Bearer | Create payment record |
| GET | `/payments` | Bearer | User's payment history |

### Admin CRUD (`/admin`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/admin/content/{resource}` | Bearer (superuser) | List content (paginated, all 23 tables) |
| POST | `/admin/content/{resource}` | Bearer (superuser) | Create content |
| GET | `/admin/content/{resource}/{id}` | Bearer (superuser) | Get content detail |
| PUT | `/admin/content/{resource}/{id}` | Bearer (superuser) | Update content |
| DELETE | `/admin/content/{resource}/{id}` | Bearer (superuser) | Delete content |
| GET | `/admin/users` | Bearer (superuser) | List users |
| GET | `/admin/users/{id}` | Bearer (superuser) | User detail |
| PUT | `/admin/users/{id}` | Bearer (superuser) | Update user |
| GET | `/admin/payments` | Bearer (superuser) | All pending/approved/rejected payments |
| POST | `/admin/payments/{id}/approve` | Bearer (superuser) | Approve payment + increment quota |
| POST | `/admin/payments/{id}/reject` | Bearer (superuser) | Reject payment |
| POST | `/admin/upload` | Bearer (superuser) | Multipart file upload → URL |

---

## Key Technologies

| Layer | Tech Stack |
|-------|-----------|
| **Backend Runtime** | Python 3.12, FastAPI 0.115+, Uvicorn/Gunicorn |
| **Backend DB** | PostgreSQL 16, SQLAlchemy 2.0 async, Alembic |
| **Backend Validation** | Pydantic v2 |
| **Auth** | JWT (python-jose), Authlib (OAuth), bcrypt (passwords) |
| **Frontend** | Next.js (Pages Router), React 18, TypeScript 5 |
| **Frontend Editor** | TipTap (rich-text), TanStack Table (data tables), react-hook-form + Zod (forms) |
| **Styling** | Tailwind CSS |
| **PDF Generation** | wkhtmltopdf (async via Python subprocess) |
| **External APIs** | Google/Facebook OAuth, vietheart.net (horoscope) |
| **Container** | Docker, Docker Compose |
| **Reverse Proxy** | Nginx 1.27-alpine, Certbot (SSL) |
| **Testing** | Pytest, pytest-asyncio (Python) |

---

## Configuration & Environment

### Backend (.env, numerology-api/)
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/numerology
JWT_SECRET=... (strong random string)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...
FRONTEND_URL=http://localhost:3000
OAUTH_REDIRECT_BASE=http://localhost:8000
WKHTMLTOPDF_CMD=/usr/bin/wkhtmltopdf (in Docker: yes; local: brew install wkhtmltopdf)
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (.env.local, Numerology-Landing-Page/)
```
NEXT_PUBLIC_API_BASE=http://localhost:8000  (local) or https://api.nhansinhquan.vn (prod)
```

### Production (.env.prod, deploy/env.prod.example)
```
DATABASE_URL=postgresql://...@postgres:5432/numerology
JWT_SECRET=... (prod secret)
GOOGLE_CLIENT_ID=... (prod OAuth app)
FRONTEND_URL=https://nhansinhquan.vn
CORS_ORIGINS=["https://nhansinhquan.vn"]
ENVIRONMENT=production
DEBUG=False
```

---

## Deployment Artifacts

| File | Purpose |
|------|---------|
| `deploy/docker-compose.prod.yml` | Production stack (api + postgres + nginx) |
| `deploy/nginx.conf` | SSL, gzip, reverse proxy, static/media serving |
| `deploy/deploy.sh` | One-command deploy (pull → build → migrate → up) |
| `deploy/backup.sh` | Daily Postgres backup script |
| `deploy/cutover.md` | Django → FastAPI migration runbook |
| `deploy/rollback.md` | Rollback procedure (< 10min recovery) |

