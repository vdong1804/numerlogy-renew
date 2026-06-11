---
title: Redesign báo cáo Thần Số Học (WeasyPrint + ảnh Gemini)
description: >-
  Thay engine PDF sang WeasyPrint, redesign theme huyền bí navy+gold, tích hợp
  ảnh Gemini (thư viện tĩnh + bìa per-user)
status: completed
priority: P2
branch: master
tags:
  - report
  - pdf
  - weasyprint
  - gemini
  - design
blockedBy: []
blocks: []
created: '2026-06-11T00:39:39.886Z'
createdBy: 'ck:plan'
source: skill
---

# Redesign báo cáo Thần Số Học (WeasyPrint + ảnh Gemini)

## Overview

Báo cáo Thần số học hiện đơn điệu, render bằng `wkhtmltopdf` (WebKit 2012, trần thẩm mỹ thấp). Mục tiêu: đẹp/sinh động hơn với theme huyền bí (navy + gold), ảnh Gemini, và engine hiện đại.

**Design doc nguồn:** `plans/reports/brainstorm-260611-0728-redesign-numerology-report.md`

**⚠️ Lưu ý kiến trúc — 2 đường render báo cáo:**
1. **Routers on-demand** — `numerology_free.py`/`numerology_paid.py` → `invoice-free.html`/`invoice.html` qua `build_report_view()` (dict: header/summary/chart_grid/chart_sections/sections).
2. **Fulfillment sau thanh toán** — `fulfillment_service.py::_render_report_pdf()` → `reports/{template_name}.html` (base_report.html + report-*.html) qua `content_codes` + `_fetch_content_by_codes()`.

Cả 2 đi qua `app/utils/pdf.py::render_pdf()`. P1 (swap engine) phủ cả hai miễn phí. P2 (theme `_theme.css`) phải áp cho cả 2 họ template. P4 (bìa per-user) nằm ở đường fulfillment.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Engine Swap WeasyPrint](./phase-01-engine-swap-weasyprint.md) | Completed |
| 2 | [Design System & Template Restructure](./phase-02-design-system-template-restructure.md) | Completed |
| 3 | [Static Image Library](./phase-03-static-image-library.md) | Completed |
| 4 | [Per-User Cover Pipeline](./phase-04-per-user-cover-pipeline.md) | Completed |

## Key Dependencies

- **P2 ⇐ P1**: redesign cần engine mới (CSS hiện đại) đã ổn định.
- **P3 ⇐ P2**: tích hợp ảnh cần khung template/theme mới.
- **P4 ⇐ P3**: bìa per-user dùng fallback bìa tĩnh từ thư viện P3.
- External: `google-genai` (đã có), `ai-multimodal` skill (gen ảnh tĩnh), `weasyprint` (thêm mới).

## Environment

- Prod: Docker `python:3.12-slim-bookworm`. `settings.media_root="./media"` (mount StaticFiles), `static_root="./static"`.
- Dev Windows: test render **qua Docker** (tránh cài GTK).

## Unresolved Questions (chốt khi triển khai)

1. ~~Imagen 4 vs Nano Banana~~ → **RESOLVED: Imagen 4 (`imagen-4.0-generate-001`)**.
   - ⚠️ Auth đổi: **Vertex AI + service account JSON** (`secrets/*.json`, gitignored) thay `GEMINI_API_KEY` (AI Studio hết credit + cần billing). Embeddings vẫn dùng `GEMINI_API_KEY`. Config: `image_gen.build_client()` ưu tiên SA → fallback key. Vertex per-minute quota thấp → script có throttle+retry (`--delay`).
   - ✅ 12 ảnh đã gen (11 archetype + cover, ~10MB). AI render hex trong prompt thành chữ → đã bỏ hex, dùng tên màu.
2. ~~Lưu ảnh bìa per-user~~ → **RESOLVED: `media_root/covers/{so_chu_dao}.png`**, no TTL (cache bền, xoá tay nếu đổi style). `media/` đã gitignore.
3. Có đồng bộ design sang DOCX export (`scripts/build_report_docx.py`) không? (mặc định: ngoài scope, ghi nhận).
4. ~~Font display: Cormorant vs Playfair~~ → **RESOLVED (P2): Playfair Display (display) + Lora (body)**.
   - ⚠️ Phát hiện P2: **Roboto Serif** (font body cũ) vietnamese subset của Google **thiếu glyph `ỉ`/`Ỉ` (U+1EC8-9)** → "chỉ số"/"đỉnh cao" hỏng. Mọi serif khác (Lora, Noto, EB Garamond...) đều có. Đã đổi body → **Lora**.
   - ⚠️ **Google subset woff2 + WeasyPrint = mangle glyph Việt** (cmap↔glyf lệch). Giải pháp: bundle **full variable TTF** (`static/fonts/{Lora,Lora-Italic,Playfair,Playfair-Italic}.ttf`) qua `@font-face url()` weight rời rạc → render đúng 100%, 0 warning. KHÔNG dùng subset của Google.
   - Drop-cap bị bỏ (xung đột dấu thanh tiếng Việt). DejaVu (`fonts-dejavu-core`) giữ làm fallback an toàn.
