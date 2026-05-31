"""One-shot: compute SHA256 of each UserReport.pdf_path and write file_hash.

Idempotent — skips rows where `file_hash` is already populated.
Missing/unreadable files are logged + counted but don't abort the run.

Usage:
    python -m scripts.backfill_pdf_hashes [--limit N]
"""

import argparse
import asyncio
import hashlib
import os
import sys
from typing import Optional

from sqlalchemy import select

from app.db.models.user_report import UserReport
from scripts._db import get_session


def _sha256_file(path: str, chunk_size: int = 1 << 20) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                buf = f.read(chunk_size)
                if not buf:
                    break
                h.update(buf)
        return h.hexdigest()
    except FileNotFoundError:
        return None
    except OSError as exc:
        print(f"  [WARN] cannot read {path}: {exc}", file=sys.stderr)
        return None


async def main(limit: Optional[int]) -> dict:
    updated = 0
    missing = 0
    skipped = 0
    async with get_session() as db:
        stmt = select(UserReport).where(UserReport.file_hash.is_(None))
        if limit:
            stmt = stmt.limit(limit)
        reports = (await db.execute(stmt)).scalars().all()
        print(f"Found {len(reports)} reports without file_hash")
        for i, report in enumerate(reports, 1):
            if not report.pdf_path or not os.path.exists(report.pdf_path):
                missing += 1
                continue
            digest = _sha256_file(report.pdf_path)
            if digest is None:
                missing += 1
                continue
            report.file_hash = digest
            updated += 1
            if i % 50 == 0:
                print(f"  processed {i}/{len(reports)}")
        await db.commit()
    return {"updated": updated, "missing": missing, "skipped": skipped}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    parser = argparse.ArgumentParser(description="Backfill SHA256 file_hash for user reports")
    parser.add_argument("--limit", type=int, default=None, help="max rows to process")
    args = parser.parse_args()
    summary = asyncio.run(main(args.limit))
    print(f"\nDone: updated={summary['updated']} missing={summary['missing']}")
