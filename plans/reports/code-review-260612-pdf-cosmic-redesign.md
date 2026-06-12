# Code Review — PDF Cosmic Redesign (4 SVG charts + cosmic theme)

Date: 2026-06-12 | Reviewer: code-reviewer | Branch: feat/numerology-report-gaps
Scope: chart/cosmic additions only (files listed in task brief)

## Summary

- Critical: 0
- Major: 0
- Minor: 4
- Nits: 3

Verdict: SHIP-READY. Clean, well-factored, fail-safe design. No must-fix blockers.
All issues are minor/cosmetic. Geometry math verified correct.

## Scope reviewed

- report_charts.py (197 LOC — under 200 budget ✓), report_charts_geometry.py (47)
- fulfillment_service.py (_resolve_charts), report_assets.py (ornament)
- numerology_full_report.py (charts wiring), _macros.html (chart_block/chart_pages/divider)
- base_report.html, invoice.html, invoice-free.html, _theme.css (@page chart, starfield, glow)
- tests: test_report_charts.py, test_report_assets.py

## Correctness (geometry) — VERIFIED OK

- Radar trig: pt() = polar→cartesian clockwise-from-top (cos/sin(deg-90)). Correct.
  Ring polygons, axis lines, data polygon, label anchoring all consistent.
- Donut arc paths (cycle_wheel): seg=40° (<180°) → large-arc-flag=0 correct; outer
  arc sweep=1 (CW) + inner return sweep=0 matches pt() CW direction. Correct donut.
- Bar scaling: h=(v/maxv)*(base-top), maxv guarded `max([*vals,1]) or 1`. No div-zero.
- cap9: digit-sum reduction loop for 11/22/33 → 1..9, clamped max(0,min(9,..)). Correct.
  Master label preserved in radar (tspan shows raw value, radius uses cap9). Good UX.

## Fail-safe guarantees — VERIFIED OK

- build_charts: each of 4 charts in own try/except (BLE001), returns dict with None
  for failed/missing → never raises. Test `test_missing_calc_keys_safe` covers {}.
- _resolve_charts: guards empty name/birth_day → None; broad except logs exc only
  (no PII) → never blocks fulfillment. Mirror of proven _resolve_cover_bg.
- Templates: chart_pages `{% if charts %}`, chart_block `{% if svg %}`, radar/timeline
  return "" → None → skipped. Triple-guarded.

## Security — OK

- No PII at info/warning: logs `exc` / template name only, never name/birth_day.
- autoescape ON (select_autoescape(['html'])); |safe applied only to server-built
  trusted SVG strings (build_charts) and trusted DB rich-text. No user input |safe'd.
- SVG built from numeric calc values + fixed VN labels — no injection surface.

## WeasyPrint — OK

- No `filter: blur`. Glow halo uses radial-gradient (theme.css:165). Compliant.
- No unicode astro glyphs; divider/ornaments are inline SVG paths.
- Starfield + watermark via data-uri / static SVG; missing asset degrades silently.

## Minor issues

1. [MINOR] Fulfillment fallback context mismatch (fulfillment_service.py:273-291).
   Context sets top-level `"charts"`. base_report.html reads top-level `charts` ✓.
   BUT the except-fallback renders `invoice.html`, which reads `report.charts`
   (invoice.html:69). `report` is Undefined there → `report.charts` is Undefined →
   `{% if charts %}` falsy → charts SILENTLY OMITTED on the fallback path (no crash,
   default Undefined not StrictUndefined). Only triggers when template_name is
   missing/bad. Fix: have the fallback also pass `report`-shaped context, or make
   invoice.html accept top-level `charts` (e.g. `chart_pages(charts or report.charts)`).
   Low likelihood (fallback is rare) but charts vanish without trace when it fires.

2. [MINOR] build_charts `birth_day` not digit-sanitized on the build_report_view path
   (numerology_full_report.py:177 passes raw birth_day). power_bar does
   birth_day.count(str(d)) so separators ("14/07/1990") are harmless, but if a year
   like "1990" vs a formatted "1990" differ it's fine — just note _resolve_charts
   strips to digits while build_report_view does not. Harmless today; keep inputs
   consistent if birth_day format ever carries letters.

3. [MINOR] peaks_timeline x-axis fixed at 4 nodes geometry (x0=34,x1=326) but uses
   `gap = (x1-x0)/max(len-1,1)`. With 1 item, single node sits at x0=34 (left), not
   centered. build_charts always feeds 4, so unreachable today (YAGNI-ok), but the
   single-item layout is slightly off if reused. Cosmetic.

4. [MINOR] cap9(0) → 0 → radar point at exact center (r=0). If multiple core numbers
   are 0 the polygon collapses toward center (visually a spike). Numerology core
   values are rarely 0, and Gemini QA passed, so acceptable. Note only.

## Nits

- n() formatting `f"{v:.1f}".rstrip("0").rstrip(".")` — for v=130.0 → "130" ✓; for
  negative tiny floats from trig (~-0.0) could print "-0" but n() only used on
  coords inside viewBox so no visual impact. Fine.
- cycle_wheel `cy_now = cap9(personal_year) or 9` — calc already sets so_nam_ca_nhan
  `or 9` upstream, so the `or 9` here is belt-and-suspenders (harmless DRY-light).
- RADAR_AXES filtered twice (build_charts builds `values` from RADAR_AXES, then
  core_radar re-filters key in values). Redundant but cheap; keeps core_radar
  independently callable. Acceptable.

## Positive observations

- Excellent module split to honor 200-line budget (geometry primitives extracted).
- Pure functions, no I/O — fully unit-testable without DB/async. Tests cover edge
  cases (all-zero, master numbers, empty, out-of-range year).
- chart_pages macro = single source of truth shared by base_report + invoice*. DRY.
- Graceful degradation everywhere (ornament/cover/charts → None, templates guard).
- Palette duplicated in geometry + CSS but explicitly documented "sync with _theme.css".
- 334 tests pass (1 unrelated pre-existing DEEPSEEK env failure).

## Recommended actions (priority order)

1. (Optional, minor) Resolve fulfillment fallback `report.charts` vs top-level
   `charts` mismatch so charts aren't silently dropped if invoice.html fallback fires.
2. (Optional) Digit-sanitize birth_day in build_report_view call for parity with
   _resolve_charts, or add a comment that birth_day is already digits there.

## Unresolved questions

- Does the fulfillment path ever actually fall back to invoice.html in prod, or are
  all paid templates base_report-derived? If always base_report, issue #1 is moot —
  confirm template_name values seeded for report products.
- Is `so_nam_ca_nhan` ever 0 post-`or 9`? If guaranteed 1..9 upstream, the cap9 `or 9`
  in cycle_wheel can be dropped for clarity.
