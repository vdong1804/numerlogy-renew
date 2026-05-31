"""File upload service — validates MIME, saves with UUID filename."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
# Hard-block dangerous extensions regardless of MIME
BLOCKED_EXTENSIONS = {"exe", "svg", "js", "php", "sh", "bat", "cmd", "py"}


def _safe_extension(filename: str) -> str:
    """Extract and validate file extension. Raises 400 on blocked/invalid ext."""
    parts = filename.rsplit(".", 1)
    if len(parts) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File has no extension")
    ext = parts[-1].lower()
    if ext in BLOCKED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type .{ext} is not allowed",
        )
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension .{ext} not supported. Allowed: {ALLOWED_EXTENSIONS}",
        )
    return ext


async def save_upload(file: UploadFile, media_root: str) -> str:
    """Validate + save uploaded file. Returns relative URL string.

    Path pattern: /media/uploads/{yyyy}/{mm}/{uuid}.{ext}
    Security: UUID rename prevents path traversal; MIME + ext whitelist.
    """
    # Validate MIME type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type '{content_type}' not allowed. Allowed: {ALLOWED_MIME_TYPES}",
        )

    # Validate extension from original filename
    original_name = file.filename or "upload"
    ext = _safe_extension(original_name)

    # Build save path: media_root/uploads/yyyy/mm/uuid.ext
    now = datetime.now(timezone.utc)
    rel_dir = Path("uploads") / str(now.year) / f"{now.month:02d}"
    save_dir = Path(media_root) / rel_dir
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = save_dir / filename

    # Stream to disk
    contents = await file.read()
    save_path.write_bytes(contents)

    # Return URL relative to media root
    rel_url = f"/media/{rel_dir.as_posix()}/{filename}"
    return rel_url
