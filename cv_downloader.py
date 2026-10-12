"""Download or locate CV PDFs.

* **Google mode** – downloads from Google Drive via the API and caches in ``cvs/``.
* **Local mode** – looks for a matching PDF in ``cvs/`` by email, name, or
  partial filename match.
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger(__name__)

DRIVE_ID_RE = re.compile(r"[?&]id=([a-zA-Z0-9_-]+)")


def _extract_file_ids(url_field: str) -> list[str]:
    """Extract one or more Google Drive file IDs from a (possibly comma-separated) URL field."""
    ids: list[str] = []
    for part in url_field.split(","):
        part = part.strip()
        m = DRIVE_ID_RE.search(part)
        if m:
            ids.append(m.group(1))
    return ids


def _sanitize(name: str) -> str:
    return re.sub(r"[^\w.@-]", "_", name).lower()


def _download_from_drive(
    drive_service: Any, file_id: str, dest: Path
) -> Path | None:
    """Download a single file from Google Drive. Returns path on success."""
    try:
        from googleapiclient.http import MediaIoBaseDownload

        request = drive_service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        dest.write_bytes(buf.getvalue())
        logger.info("Downloaded %s → %s", file_id, dest)
        return dest
    except Exception:
        logger.exception("Failed to download file_id=%s", file_id)
        return None


def _find_local_pdf(email: str, name: str) -> Path | None:
    """Try to find a matching PDF in the local cvs/ directory."""
    cv_dir = config.CVS_DIR
    candidates = [
        cv_dir / f"{_sanitize(email)}.pdf",
        cv_dir / f"{_sanitize(name)}.pdf",
    ]
    for c in candidates:
        if c.is_file():
            return c

    email_stem = _sanitize(email.split("@")[0])
    name_lower = name.lower()
    for pdf in cv_dir.glob("*.pdf"):
        stem = pdf.stem.lower()
        if email_stem in stem or name_lower in stem:
            return pdf

    return None


def get_cv_paths(
    email: str,
    name: str,
    cv_url: str,
    drive_service: Any | None,
) -> list[Path]:
    """Return list of local PDF paths for a worker.

    In Google mode, downloads from Drive (caching locally).
    In local mode, searches the ``cvs/`` folder.
    """
    # Try Drive download first when credentials are available
    if drive_service and cv_url:
        file_ids = _extract_file_ids(cv_url)
        paths: list[Path] = []
        for idx, fid in enumerate(file_ids):
            suffix = f"_{idx}" if idx > 0 else ""
            dest = config.CVS_DIR / f"{_sanitize(email)}{suffix}.pdf"
            if dest.is_file():
                logger.debug("Using cached CV: %s", dest)
                paths.append(dest)
                continue
            result = _download_from_drive(drive_service, fid, dest)
            if result:
                paths.append(result)
        if paths:
            return paths
        logger.warning("Drive download failed for %s – trying local fallback.", email)

    # Fall back to local PDF lookup
    local = _find_local_pdf(email, name)
    if local:
        return [local]

    logger.warning("No CV found for %s (%s)", name, email)
    return []
