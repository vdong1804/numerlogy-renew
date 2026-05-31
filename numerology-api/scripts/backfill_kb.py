"""One-shot backfill of all numerology content rows into KB chunks.

Idempotent: re-running replaces existing chunks for each (source_type, source_ref)
pair via KbIngestionService.upsert_document.

Usage:
    python -m scripts.backfill_kb [--dry-run]
"""

import argparse
import asyncio
import sys
from typing import Any, Optional

from sqlalchemy import select

from app.db.models import numerology_content as _nc
from app.services.chat.embedding_service import EmbeddingService
from app.services.chat.kb_ingestion_service import KbIngestionService
from app.services.chat.kb_sync import _to_source
from scripts._db import get_session

# Skip PhoneMasterDataModel — schema lacks title/content
_TARGET_MODELS = [getattr(_nc, name) for name in _nc.__all__ if name != "PhoneMasterDataModel"]


def _row_payload(target: Any) -> tuple[str, str, Optional[str], str]:
    return _to_source(target)


async def _backfill_model(svc: KbIngestionService, model, dry_run: bool) -> int:
    """Return number of docs upserted for one numerology content model."""
    table = model.__tablename__
    async with get_session() as db:
        rows = (await db.execute(select(model))).scalars().all()
    count = 0
    for i, row in enumerate(rows, 1):
        source_type, source_ref, title, content = _row_payload(row)
        if dry_run:
            count += 1
            continue
        await svc.upsert_document(source_type, source_ref, title, content)
        count += 1
        if i % 50 == 0:
            print(f"    {table}: {i}/{len(rows)} ingested")
    return count


async def main(dry_run: bool) -> dict[str, int]:
    results: dict[str, int] = {}
    if dry_run:
        # No need for embedding API in dry-run; only count rows.
        for model in _TARGET_MODELS:
            async with get_session() as db:
                rows = (await db.execute(select(model))).scalars().all()
            results[model.__tablename__] = len(rows)
            print(f"  [DRY] {model.__tablename__:<25} {len(rows):>4} rows")
        return results

    async with get_session() as db:
        svc = KbIngestionService(db, EmbeddingService())
        for model in _TARGET_MODELS:
            n = await _backfill_model(svc, model, dry_run=False)
            results[model.__tablename__] = n
            print(f"  [OK]  {model.__tablename__:<25} {n:>4} rows ingested")
            await db.commit()
    return results


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    parser = argparse.ArgumentParser(description="Backfill numerology content into KB")
    parser.add_argument("--dry-run", action="store_true", help="count rows without embedding")
    args = parser.parse_args()
    totals = asyncio.run(main(args.dry_run))
    print(f"\nTotal: {sum(totals.values())} rows across {len(totals)} tables")
