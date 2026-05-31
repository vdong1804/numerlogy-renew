"""Admin upload router — POST /admin/upload (multipart image upload)."""

from fastapi import APIRouter, Depends, UploadFile, File

from app.deps import get_db  # noqa: F401 — kept for consistency; upload is stateless
from app.config import settings
from app.services.upload_service import save_upload

router = APIRouter(tags=["admin-uploads"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept multipart image upload. Validates MIME + extension, saves with UUID name.

    Returns: {"url": "/media/uploads/yyyy/mm/uuid.ext"}
    Rejects: .exe, .svg and any non-image MIME types.
    """
    url = await save_upload(file, settings.media_root)
    return {"url": url}
