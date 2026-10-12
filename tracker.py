"""Track which workers have already been processed for incremental runs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import config

logger = logging.getLogger(__name__)


def load_processed() -> dict[str, str]:
    """Return ``{email: iso_timestamp}`` of previously processed workers."""
    path = config.PROCESSED_ROWS_FILE
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            return data
    except Exception:
        logger.exception("Corrupted tracker file %s – starting fresh.", path)
    return {}


def save_processed(processed: dict[str, str]) -> None:
    """Persist the processed-workers mapping to disk."""
    config.PROCESSED_ROWS_FILE.write_text(json.dumps(processed, indent=2))
    logger.debug("Tracker saved (%d entries).", len(processed))


def mark_processed(processed: dict[str, str], email: str) -> None:
    """Mark a single worker as processed with the current timestamp."""
    processed[email] = datetime.now(timezone.utc).isoformat()


def filter_new_workers(
    all_emails: list[str], force_all: bool = False
) -> tuple[list[str], dict[str, str]]:
    """Return ``(emails_to_process, processed_map)``.

    If *force_all* is True every email is returned regardless of prior state.
    """
    processed = load_processed()
    if force_all:
        return all_emails, processed

    new = [e for e in all_emails if e not in processed]
    logger.info(
        "%d total workers, %d already processed, %d new.",
        len(all_emails),
        len(all_emails) - len(new),
        len(new),
    )
    return new, processed
