# Phase 06 — Tests + Docs

**Context:** `plan.md` · Phase 01-05
**Priority:** Med · **Status:** ⬜ Not started

## Overview
Phủ test cho entitlement + gating + carry-over; cập nhật docs/changelog. Không merge nếu test fail.

## Requirements
**Backend tests** (`numerology-api/tests/`)
- `resolve_entitlement`: no user → FREE_CODES; user có order paid khớp → ∪ content_codes; order pending/expired → không mở; identity chuẩn hóa (dấu/hoa thường/space).
- `build_report` gating: section khóa `content is None` + `locked True` + có `teaser`; section mở giữ full.
- Router `/numerology-report`: free request không chứa HTML khóa; paid request (mock auth + order) mở đúng.

**Frontend** (nếu có harness — kiểm tra `Numerology-Landing-Page` test setup)
- `NumberCard` render LockCard khi `locked`.
- `buildUnlockHref`/`readPrefill` round-trip prefill.
- `tsc --noEmit` sạch.

## Related code files
**Create**
- `numerology-api/tests/services/test_report_entitlement_service.py`
- mở rộng `numerology-api/tests/services/test_numerology_report_builder.py` (đã tồn tại) cho gating.
- `numerology-api/tests/integration/test_numerology_report_entitlement.py` (router-level, nếu pattern integration có sẵn).
**Modify (docs)**
- `docs/project-changelog.md` — entry 2026-06-12 "/ket-qua entitlement + gating + PDF unification".
- `docs/system-architecture.md` — mô tả report entitlement flow.
- `docs/codebase-summary.md` — thêm `report_entitlement_service.py`, LockCard, StickyPurchaseBar.

## Implementation steps
1. Viết backend unit tests (entitlement + builder gating).
2. Router/integration test free vs paid (mock get_current_user_optional + seed order).
3. Chạy `pytest` (lưu ý caveat docker/test trong memory `numerology-formula-source-of-truth`).
4. FE: `tsc --noEmit` + test component nếu có.
5. Cập nhật 3 docs + changelog.

## Todo
- [ ] test_report_entitlement_service
- [ ] builder gating tests
- [ ] router/integration free vs paid
- [ ] pytest pass
- [ ] FE tsc + component test
- [ ] docs + changelog

## Success criteria
- Toàn bộ test pass (không skip để qua build).
- Docs phản ánh flow mới.

## Risks
- Test DB/docker caveat (xem memory). Dùng fixture sẵn có của suite.

## Next
→ Code review (`code-reviewer`) trước khi PR.
