"""Shared google-genai client builder — Vertex AI via a service-account JSON.

Used by both report image generation and chat embeddings. The whole project
authenticates through one GCP service account (runs on GCP billing); there is
no AI Studio API-key path.

Config: `settings.google_application_credentials` points at the service-account
JSON; the project id is read from the JSON when `google_cloud_project` is blank.
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
    """True when a usable Vertex AI service account is configured."""
    return _service_account_path() is not None


def _project_id(sa: Path) -> str:
    return settings.google_cloud_project or json.loads(
        sa.read_text(encoding="utf-8")
    ).get("project_id", "")


def build_genai_client():
    """Build a Vertex AI google-genai Client from the service account."""
    from google import genai
    from google.oauth2 import service_account

    sa = _service_account_path()
    if sa is None:
        raise RuntimeError(
            "no genai auth: set google_application_credentials to a Vertex AI "
            "service-account JSON"
        )
    creds = service_account.Credentials.from_service_account_file(str(sa), scopes=_SCOPES)
    return genai.Client(
        vertexai=True,
        project=_project_id(sa),
        location=settings.google_cloud_location,
        credentials=creds,
    )
