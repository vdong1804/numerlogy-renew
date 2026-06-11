"""Dump the full report view (numbers + DB content) → JSON for offline docx export.

CONTAINER-SIDE (needs DB). Thin wrapper around the shared report service
(app.services.numerology_full_report) so the docx export and the web report
(invoice.html) stay in sync.

Usage:
    python -m scripts.build_report_payload "<full_name>" <ddmmyyyy> <phone>
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from app.services.numerology_full_report import build_report_view
from scripts._db import get_session

OUT = Path(__file__).resolve().parent / "data" / "report_payload.json"


async def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "Vũ Đồng"
    dob = sys.argv[2] if len(sys.argv) > 2 else "01031996"
    phone = sys.argv[3] if len(sys.argv) > 3 else "0986792550"
    async with get_session() as db:
        report = await build_report_view(db, name, dob, phone)
    # calc may contain non-JSON-safe values? all ints/str/list — but drop to be safe
    report.pop("calc", None)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {OUT}  ({len(report['sections'])} sections, {len(report['chart_sections'])} chart digits)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
