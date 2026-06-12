# Phase 01 — Backend: Entitlement-aware Report API

**Context:** `plan.md` · `plans/reports/analysis-260612-1501-ket-qua-flow.md`
**Priority:** High (foundation) · **Status:** ⬜ Not started

## Overview
Biến `/api/numerology-report` từ "public, trả full" thành **entitlement-aware**: nhận optional Bearer,
resolve order `paid` khớp name+birth_day → tập `unlocked` content codes, rồi builder **strip** content
của section khóa (chỉ giữ code/title + teaser ngắn). Mục tiêu: chống leak (decision #2) + gate theo order (#1).

## Key insights
- Order cần auth; endpoint phải hoạt động **cả khi không có token** (free tier) → token optional.
- Match order: so name+birth_day chuẩn hóa với `input_payload`/`meta` của order paid của user.
- Builder hiện thuần (pure) — thêm tham số `unlocked: set[str]`, không phá tính pure.

## Requirements
**Functional**
- `numerology_report` accept optional auth (reuse dep `get_current_user_optional` nếu có; nếu chưa, tạo).
- Resolve entitlement:
  - Không token / không order khớp → `unlocked = FREE_CODES` (Phase 02).
  - Có order paid khớp → `unlocked = FREE_CODES ∪ (product.content_codes các item)`.
- `build_report(..., unlocked)`:
  - Section thuộc `unlocked` → trả như cũ.
  - Section khóa → `content/content_2..5 = None`, thêm `locked: true`, `teaser: <≤160 ký tự>` (cắt từ title hoặc câu mở đầu nếu nguồn cho phép — KHÔNG trả full HTML).
- Response thêm `tier: "free" | "paid"` + `unlocked: [...]` + `matched_order_id?`.

**Non-functional**
- Không tăng số query đáng kể: 1 query orders (join items+product) theo user + filter status=paid.
- Endpoint vẫn trả 200 cho free; không 401 khi thiếu token.

## Architecture / data flow
```
GET /numerology-report?full_name&birth_day  (Authorization: Bearer? )
  → calc = calculate_numerology_numbers()
  → user = get_current_user_optional()
  → unlocked = resolve_entitlement(db, user, full_name, birth_day)   # new service
  → models = get_numerology_models(db, calc)
  → report = build_report(full_name, birth_day, calc, models, unlocked)
  → { data: report, tier, unlocked, matched_order_id }
```

## Related code files
**Modify**
- `numerology-api/app/routers/numerology_report.py` — optional auth, gọi resolver, truyền `unlocked`.
- `numerology-api/app/services/numerology_report_builder.py` — thêm `unlocked` param + strip logic + `locked/teaser` fields.
- `numerology-api/app/deps.py` — thêm `get_current_user_optional` nếu chưa có.
**Create**
- `numerology-api/app/services/report_entitlement_service.py` — `resolve_entitlement(db, user, full_name, birth_day) -> set[str]` + helper `normalize_identity()`.

## Implementation steps
1. Khảo sát dep auth hiện có (`app/deps.py`, `app/services/auth*`) — tái dùng giải mã JWT; tạo `get_current_user_optional` trả `None` khi thiếu/invalid token (không raise).
2. Viết `report_entitlement_service.resolve_entitlement`:
   - `normalize_identity(name, birth_day)` = lower + strip + bỏ dấu (unidecode/`unicodedata`) + birth_day digits.
   - Query Order paid của user, join items→product; lấy order có `meta/input_payload` khớp identity.
   - Gộp `content_codes` của product trong order khớp ∪ `FREE_CODES`.
3. Sửa `build_report` nhận `unlocked`; viết helper `_gate(section_code, payload)` áp cho từng nhóm (so_chu_dao, core_numbers.*, peaks, challenges, personal, karmic, missing...). Map section→code thống nhất Phase 02.
4. Sửa router: optional user, gọi resolver, trả `tier/unlocked/matched_order_id`.
5. Chạy backend, smoke test: free (no token) vs paid (token + order khớp).

## Todo
- [ ] `get_current_user_optional`
- [ ] `report_entitlement_service.py` (+ normalize)
- [ ] `build_report` unlocked + strip + locked/teaser
- [ ] router wiring + response fields
- [ ] smoke test free vs paid

## Success criteria
- Free request: section khóa KHÔNG chứa `content` (null) nhưng có `locked:true` + `teaser`.
- Paid request (token + order khớp): section tương ứng trả full.
- Network payload free không còn HTML luận giải trả phí (verify bằng curl).

## Risks
- Auth dep chưa có optional variant → phải tạo, cẩn thận không break các route đang require.
- Match identity sai (đồng âm khác dấu) → chuẩn hóa kỹ + test.

## Security
- Không trả content khóa cho client chưa entitled (đây là mục tiêu chính).
- Token invalid → coi như free, không leak lỗi.

## Next
→ Phase 02 định nghĩa `FREE_CODES` + section→code map chính xác.
