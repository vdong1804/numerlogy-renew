---
phase: 4
title: Per-User Cover Pipeline
status: completed
priority: P2
effort: 1d
dependencies:
  - 3
---

# Phase 4: Per-User Cover Pipeline

## Context Links
- Design doc: `plans/reports/brainstorm-260611-0728-redesign-numerology-report.md`
- Fulfillment: `app/services/fulfillment_service.py::_render_report_pdf()`
- Config: `app/config.py` (`media_root`)

## Overview
Gen **bìa nghệ thuật per-user** lúc fulfillment (bản paid) theo Số chủ đạo, **cache theo `so_chu_dao`** để tái dùng (tiết kiệm). Overlay tên/ngày sinh/SĐT bằng CSS đè lên ảnh. **Fail-safe:** lỗi/timeout → dùng `cover-fallback.webp` (P3) → KHÔNG block luồng thanh toán.

## Key Insights
- Bìa = **nền art không chữ** (AI) + **text overlay CSS** (chính xác tiếng Việt).
- Cache theo `so_chu_dao` (1-9,11,22) ⇒ tối đa ~11 ảnh nền per-user-tier dùng lại — gần như static sau khi "ấm" cache, nhưng gen động lần đầu cho số chưa có.
- Gen ảnh là I/O ngoài, có thể chậm/fail → **bắt buộc** timeout + fallback, tách khỏi path tạo PDF tối thiểu.

## Requirements
- Functional: fulfillment paid dùng bìa theo `so_chu_dao`; nếu cache có → dùng ngay; nếu chưa → gen + lưu cache; nếu gen fail/timeout → fallback tĩnh. Overlay text đúng.
- Non-functional: gen có timeout (vd 15-20s); không raise ra ngoài làm fail order; log rõ path đi (cache-hit/gen/fallback).

## Architecture
- **Cache key**: `so_chu_dao`. Lưu nền tại `media_root/covers/{so_chu_dao}.webp` (hoặc `static/report-assets/covers-generated/`). Chốt vị trí + TTL ở bước triển khai (unresolved Q2).
- **Service mới** `app/services/cover_generator.py`:
  - `async get_cover_background(so_chu_dao) -> path`: cache-hit → trả path; miss → gen qua `google-genai` (no-text art prompt theo style-guide P3) với `asyncio.wait_for(timeout)`; lưu cache; mọi exception → trả `cover-fallback.webp`.
  - Idempotent + concurrency-safe (lock/atomic write tránh 2 order cùng số gen đôi).
- **Tích hợp fulfillment**: trong `_render_report_pdf` (hoặc trước khi render), tính `so_chu_dao` từ `input_payload` (cần `build_report_view`/calc — lưu ý đường fulfillment hiện dùng `content_codes`, KHÔNG gọi calc; phải bổ sung tính `so_chu_dao` từ input name+birthday), resolve cover background path, đưa vào context template.
- **Overlay**: template cover dùng `background-image: url(cover_bg)` + lớp CSS chứa tên/ngày sinh/SĐT (đã có ở P2 cover). Bản on-demand (routers) có thể dùng bìa fallback tĩnh (không gen per-request để tránh latency tải free/paid trực tiếp) — chốt: per-user gen chỉ ở fulfillment.
- **Fail-safe**: try/except bao quanh; timeout; fallback path luôn tồn tại (P3).

## Related Code Files
- Create: `app/services/cover_generator.py`.
- Modify: `app/services/fulfillment_service.py` — tính `so_chu_dao` từ input, resolve cover bg, truyền vào context; giữ try/render fallback hiện có.
- Modify: `app/templates/invoice.html` (+ `reports/base_report.html` nếu fulfillment dùng) — cover dùng biến `cover_bg`.
- Read context: `app/core/numerology.py` (`calculate_numerology_numbers` để lấy `so_chu_dao`), `app/config.py` (media_root), `app/main.py` (StaticFiles mount cho phục vụ ảnh nếu cần URL).

## Implementation Steps
1. Chốt vị trí lưu cache + chính sách (mục Unresolved Q2). Tạo thư mục + đảm bảo writable trong Docker volume.
2. Viết `cover_generator.py`: cache-check → gen (timeout) → lưu atomic → fallback. Dùng style-guide prompt P3 (no-text).
3. Trong fulfillment, tính `so_chu_dao` từ `input_payload` (name+birth_day) qua calc; gọi `get_cover_background`; thêm `cover_bg` vào context.
4. Cập nhật template cover dùng `cover_bg` (fallback path mặc định nếu thiếu).
5. Test: (a) cache-miss gen, (b) cache-hit, (c) gen fail/timeout → fallback, (d) order không bị block khi fail.
6. Render verify qua Docker; kiểm tra concurrency (2 order cùng số chủ đạo).

## Todo List
- [ ] Chốt path cache + TTL + Docker volume writable
- [ ] `cover_generator.py` (cache → gen+timeout → atomic save → fallback)
- [ ] Tính `so_chu_dao` trong fulfillment + truyền `cover_bg`
- [ ] Template cover dùng `cover_bg`
- [ ] Test 4 nhánh (miss/hit/fail/non-block) + concurrency
- [ ] Render verify qua Docker

## Success Criteria
- [ ] Fulfillment paid hiển thị bìa theo `so_chu_dao`, overlay tên/ngày sinh đúng.
- [ ] Cache-hit không gen lại; cache-miss gen + lưu.
- [ ] Gen fail/timeout → fallback tĩnh, order vẫn hoàn tất (không raise).
- [ ] Không có double-gen khi 2 order cùng số chủ đạo chạy song song.

## Risk Assessment
- **Gen block thanh toán**: → timeout + try/except + fallback bắt buộc; cân nhắc tách gen ra ngoài critical path nếu cần.
- **Race double-gen / file ghi dở**: → lock theo key + atomic write (ghi tmp rồi rename).
- **Chi phí trôi**: → cache theo số chủ đạo giới hạn ~11 nền; không gen per-request ở routers.
- **Volume không writable trong prod** (bind-mount): → kiểm tra quyền ghi `media_root/covers` trong Docker (tham chiếu commit deploy gần đây về media volume).

## Security Considerations
- Prompt gen từ `so_chu_dao` (số nội bộ), KHÔNG nhúng input người dùng thô vào prompt → tránh prompt-injection/PII rò sang API ảnh.
- Ảnh nền không chứa PII; PII (tên/ngày sinh) chỉ overlay local trong PDF.

## Next Steps
- (Optional/sau) đồng bộ design sang DOCX export nếu cần (Unresolved Q3).
- Cân nhắc job dọn cache cũ nếu đổi style-guide.
