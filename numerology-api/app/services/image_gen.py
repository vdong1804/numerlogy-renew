"""Google image generation + JPEG optimization (shared by the asset script and
the runtime cover pipeline).

Auth goes through the shared Vertex AI client (see genai_client.build_genai_client).
"""

from __future__ import annotations

import io

from app.config import settings
from app.services.genai_client import build_genai_client, is_genai_configured

# Backward-compatible aliases (callers import these from image_gen).
build_client = build_genai_client
is_configured = is_genai_configured


def generate_image_bytes(
    prompt: str, aspect_ratio: str = "1:1", model: str | None = None, client=None,
) -> bytes:
    """Generate one image and return raw bytes. Raises on any failure.

    Supports Imagen (`generate_images`) and Gemini-native image models
    (`generate_content`). Pass a prebuilt `client` to reuse it across a batch.
    """
    from google.genai import types

    client = client or build_client()
    model = model or settings.report_image_model

    if model.startswith("imagen-"):
        resp = client.models.generate_images(
            model=model, prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio=aspect_ratio),
        )
        return resp.generated_images[0].image.image_bytes

    resp = client.models.generate_content(model=model, contents=prompt)
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            return part.inline_data.data
    raise RuntimeError("model returned no image data")


def optimize_image(raw: bytes, max_px: int, quality: int = 85) -> bytes:
    """Downscale to max_px on the long edge and return optimized JPEG bytes.

    Illustrations are full-bleed (no transparency), so JPEG cuts the embedded
    PDF/report size to a fraction of PNG with no visible loss at this quality.
    """
    from PIL import Image

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    if max(img.size) > max_px:
        scale = max_px / max(img.size)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()
