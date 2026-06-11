"""Shared google-genai client builder.

Auth priority (used by both report image generation and chat embeddings):
  1. Vertex AI via a service-account JSON — `settings.google_application_credentials`
     (runs on GCP billing; project read from the JSON if not set explicitly).
  2. AI Studio API key — `settings.gemini_api_key`.

Centralizing this lets the whole project move to Vertex by dropping a service
account in, with the API key as a fallback.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def _service_account_path() -> Path | None:
    sa = settings.google_application_credentials
    if sa and Path(sa).exists():
        return Path(sa)
    return None


def is_genai_configured() -> bool:
    """True when genai has usable auth (service account or API key)."""
    return _service_account_path() is not None or bool(settings.gemini_api_key)


def _project_id(sa: Path) -> str:
    return settings.google_cloud_project or json.loads(
        sa.read_text(encoding="utf-8")
    ).get("project_id", "")


def build_genai_client():
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
        "no genai auth: set google_application_credentials (service account) "
        "or gemini_api_key"
    )
