"""Local-file helpers for multipart uploads (knowledge documents, voice clones).

Coding agents usually have the file on disk, so the upload tools take a path
rather than base64 content.
"""

import mimetypes
from pathlib import Path
from typing import Any

from ._dispatch import MissingInputError

# Voice-cloning uploads are capped at 50 MB server-side; use the same ceiling
# locally so oversized files fail fast without a long upload.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def file_part(file_path: str) -> dict[str, Any]:
    """Build an httpx ``files`` mapping for the file at ``file_path``.

    Raises:
        MissingInputError: If the path is missing, not a file, or too large.
    """
    path = Path(file_path).expanduser().resolve()
    hidden = [part for part in path.parts if part.startswith(".") and part not in (".", "..")]
    if hidden:
        # Dotfiles/dot-dirs (~/.ssh, ~/.aws, .env, ...) hold secrets; never
        # upload them to a third-party API, even if a prompt asks to.
        raise MissingInputError(f"Error: refusing to upload from a hidden path ({hidden[0]}): {path}")
    if not path.is_file():
        raise MissingInputError(f"Error: file not found: {path}")
    size = path.stat().st_size
    if size > MAX_UPLOAD_BYTES:
        raise MissingInputError(f"Error: {path.name} is {size // (1024 * 1024)} MB; the limit is 50 MB.")
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {"file": (path.name, path.read_bytes(), content_type)}
