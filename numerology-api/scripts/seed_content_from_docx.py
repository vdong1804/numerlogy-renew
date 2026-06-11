"""Load parsed `Nội dung` content (numerology_content.json) into the DB.

CONTAINER-SIDE step: reads scripts/data/numerology_content.json (produced by
parse_content_docx.py on the host) and upserts rows into the content tables,
OVERWRITING the placeholder seed text (on_conflict_do_update on `code`).

Run (inside api container, DB reachable as db:5432):
    docker compose exec api python -m scripts.seed_content_from_docx
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from scripts._db import get_session
from scripts.seed_content import _MODEL_MAP

DATA_FILE = Path(__file__).resolve().parent / "data" / "numerology_content.json"


async def main() -> None:
    records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    by_table: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_table[r["table"]].append(r)

    total = skipped = 0
    async with get_session() as db:
        for table, rows in sorted(by_table.items()):
            model = _MODEL_MAP.get(table)
            if model is None:
                print(f"  [SKIP] unknown table {table} ({len(rows)} rows)")
                skipped += len(rows)
                continue
            for r in rows:
                title = (r.get("title") or f"{table} {r['code']}").strip()[:250]
                values = {
                    "code": str(r["code"]),
                    "title": title,
                    "content": r["content"] or "",
                    "number_page": None,
                }
                stmt = (
                    insert(model)
                    .values(**values)
                    .on_conflict_do_update(
                        index_elements=["code"],
                        set_={"title": values["title"], "content": values["content"]},
                    )
                )
                await db.execute(stmt)
            total += len(rows)
            print(f"  [OK] {table:<22} {len(rows):>3} rows upserted")
        await db.commit()
    print(f"\nDONE — {total} rows upserted, {skipped} skipped")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
