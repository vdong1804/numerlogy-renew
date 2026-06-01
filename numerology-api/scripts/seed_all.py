"""Orchestrator: run all seed scripts in sequence.

Idempotent — safe to run multiple times.
Run: python -m scripts.seed_all
"""

import asyncio
import sys
import time


async def main() -> None:
    t0 = time.perf_counter()
    print("=== Numerology DB Seeder ===\n")

    # --- Content tables (placeholders first) ---
    print("[1/7] Seeding numerology content tables...")
    from scripts.seed_content import main as seed_content
    content_results = await seed_content()
    total_content = sum(content_results.values())
    print(f"      Content total: {total_content} rows across {len(content_results)} tables\n")

    # --- Real report content (overwrites placeholders for report tables) ---
    print("[2/7] Seeding real report content...")
    from scripts.seed_report_content import main as seed_report_content
    await seed_report_content()
    print()

    # --- Packages (legacy) ---
    print("[3/7] Seeding legacy packages...")
    from scripts.seed_packages import main as seed_packages
    await seed_packages()
    print()

    # --- Products (new catalogue) ---
    print("[4/7] Seeding products...")
    from scripts.seed_products import main as seed_products
    await seed_products()
    print()

    # --- Banks ---
    print("[5/7] Seeding banks...")
    from scripts.seed_banks import main as seed_banks
    await seed_banks()
    print()

    # --- Chat add-on packages ---
    print("[6/7] Seeding chat add-on packages...")
    from scripts.seed_chat_addons import main as seed_chat_addons
    await seed_chat_addons()
    print()

    # --- Blog/news articles ---
    print("[7/7] Seeding blog/news articles...")
    from scripts.seed_news import main as seed_news
    await seed_news()
    print()

    elapsed = time.perf_counter() - t0
    print(f"=== Done in {elapsed:.2f}s ===")
    print("\nNext step: create a superuser:")
    print("  python -m scripts.create_superuser --email admin@example.com --password Admin123!")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
