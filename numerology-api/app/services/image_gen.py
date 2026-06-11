"""Google image generation + PNG optimization (shared by the asset script and
the runtime cover pipeline).

Auth (in priority order):
  1. Vertex AI via a service-account JSON — `settings.google_application_credentials`
     (needs GCP billing; project read from the JSON if not set explicitly).
  2. AI Studio API key — `settings.gemini_api_key` (image gen needs a paid key).

Embeddings elsewhere keep using the API key; only image generation prefers the
service account so it can run on GCP billing.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from app.config import settings

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def _service_account_path() -> Path | None:
    sa = settings.google_application_credentials
    if sa and Path(sa).exists():
        return Path(sa)
    return None


def is_configured() -> bool:
    """True when image generation has usable auth (service account or API key)."""
    return _service_account_path() is not None or bool(settings.gemini_api_key)


def _project_id(sa: Path) -> str:
    return settings.google_cloud_project or json.loads(
        sa.read_text(encoding="utf-8")
    ).get("project_id", "")


def build_client():
    """Build a configured google-genai Client (Vertex SA preferred, else API key)."""
    from google import genai

    sa = _service_account_path()
    if sa is not None:
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_file(str(sa), scopes=_SCOPES)
        return genai.Client(
            vertexai=True,
            project=_project_id(sa),
            location=settings.google_cloud_location,
            credentials=creds,
        )
    if settings.gemini_api_key:
        return genai.Client(api_key=settings.gemini_api_key)
    raise RuntimeError(
        "no image-gen auth: set google_application_credentials (service account) "
        "or gemini_api_key"
    )


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
