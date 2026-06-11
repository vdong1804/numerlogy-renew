#!/usr/bin/env python3
"""Generate the static report illustration library (run once, commit the output).

11 Số chủ đạo archetypes (1-9, 11, 22) + 1 cover background, in a consistent
navy + gold "mystical/celestial" style. AI renders ABSTRACT ART ONLY — no text
(all labels are overlaid by the template), so master-number/Vietnamese text is
never garbled by the image model.

Prompts + generation are shared with the runtime per-user cover pipeline
(app/services/report_art_prompts.py, image_gen.py) → single source of truth.

Usage (needs a billing-enabled Google key in env or numerology-api/.env):
    GEMINI_API_KEY=... python scripts/gen_report_assets.py
    python scripts/gen_report_assets.py --only 8 cover     # regenerate a subset
    python scripts/gen_report_assets.py --model imagen-4.0-ultra-generate-001
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))  # make `app` importable when run from scripts/

from app.config import settings  # noqa: E402
from app.services.image_gen import (  # noqa: E402
    build_client, generate_image_bytes, is_configured, optimize_image,
)
from app.services.report_art_prompts import (  # noqa: E402
    MOTIFS, build_archetype_prompt, build_cover_prompt,
)

_ARCH_DIR = _ROOT / "static" / "report-assets" / "archetypes"
_COVER_DIR = _ROOT / "static" / "report-assets" / "cover"

# (key, prompt, aspect_ratio, output_path, max_px)
_TARGETS: list[tuple[str, str, str, Path, int]] = [
    *[(n, build_archetype_prompt(n), "1:1", _ARCH_DIR / f"{n}.jpg", 820) for n in MOTIFS],
    ("cover", build_cover_prompt(None), "3:4", _COVER_DIR / "cover-fallback.jpg", 1240),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=settings.report_image_model,
                    help="Google image model (imagen-4.0-* or gemini-*-image)")
    ap.add_argument("--only", nargs="+", metavar="KEY",
                    help="generate only these keys (e.g. 8 11 cover)")
    ap.add_argument("--delay", type=float, default=12.0,
                    help="seconds to wait between images (Vertex per-minute quota)")
    ap.add_argument("--skip-existing", action="store_true",
                    help="skip targets whose output already exists")
    args = ap.parse_args()

    if not is_configured():
        sys.exit("ERROR: no image-gen auth. Set google_application_credentials "
                 "(service-account JSON, Vertex AI) or gemini_api_key in .env.")
    client = build_client()  # reuse one client across the whole batch
    targets = _TARGETS
    if args.only:
        wanted = set(args.only)
        targets = [t for t in _TARGETS if t[0] in wanted]
    if args.skip_existing:
        targets = [t for t in targets if not t[3].exists()]
    if not targets:
        sys.exit("nothing to generate (check --only / --skip-existing)")

    print(f"Generating {len(targets)} asset(s) with {args.model}\n")
    ok = 0
    for i, (name, prompt, aspect, out, max_px) in enumerate(targets):
        if i:
            time.sleep(args.delay)  # throttle to respect Vertex per-minute quota
        try:
            raw = _gen_retry(prompt, aspect, args.model, client)
            img = optimize_image(raw, max_px)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(img)
            print(f"  OK  {name:>5}  -> {out.relative_to(_ROOT)}  ({len(img) // 1024} KB)")
            ok += 1
        except Exception as exc:  # noqa: BLE001 — keep going on per-image failure
            print(f"  FAIL {name:>5}  {type(exc).__name__}: {exc}")
    print(f"\nDone: {ok}/{len(targets)} succeeded.")


def _gen_retry(prompt: str, aspect: str, model: str, client, attempts: int = 6):
    """Generate with exponential backoff on Vertex per-minute quota (429)."""
    for attempt in range(attempts):
        try:
            return generate_image_bytes(prompt, aspect, model, client=client)
        except Exception as exc:  # noqa: BLE001
            if "RESOURCE_EXHAUSTED" in str(exc) and attempt < attempts - 1:
                wait = 20 * (attempt + 1)
                print(f"        quota hit — retrying in {wait}s "
                      f"(attempt {attempt + 1}/{attempts})")
                time.sleep(wait)
                continue
            raise


if __name__ == "__main__":
    main()
