"""Google API authentication – supports Service Account and OAuth2.

* **Service Account** – uses a JSON key file (headless, no browser needed).
* **OAuth2** – uses ``creds/oauth_crednetials.json`` + ``creds/token.json``.
  Tokens are auto-refreshed when expired.  Run this file directly to perform
  the initial authorization flow::

      python google_auth.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _ensure_importlib_metadata_compat() -> None:
    """Patch missing importlib.metadata.packages_distributions on Python <3.10."""
    try:
        import importlib.metadata as stdlib_metadata  # type: ignore

        if hasattr(stdlib_metadata, "packages_distributions"):
            return

        try:
            import importlib_metadata as backport_metadata  # type: ignore
        except Exception:
            return

        stdlib_metadata.packages_distributions = (  # type: ignore[attr-defined]
            backport_metadata.packages_distributions
        )
    except Exception:
        # Best effort; if this fails, downstream libraries may still error.
        return


def _has_required_scopes(creds: Any) -> bool:
    scopes = set(creds.scopes or [])
    return set(SCOPES).issubset(scopes)


def _has_spreadsheets_scope(creds: Any) -> bool:
    scopes = set(creds.scopes or [])
    return "https://www.googleapis.com/auth/spreadsheets" in scopes



# ── Service Account ────────────────────────────────────────────────────────


def _auth_service_account() -> Any:
    from google.oauth2.service_account import Credentials

    return Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )


# ── OAuth2 ─────────────────────────────────────────────────────────────────


def _auth_oauth() -> Any:
    import os

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    token_path = Path(config.GOOGLE_TOKEN_FILE)
    creds: Credentials | None = None

    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path))

    if creds and creds.expired and creds.refresh_token:
        logger.info("OAuth token expired – refreshing …")
        creds.refresh(Request())
        _save_oauth_token(creds, token_path)
        logger.info("Token refreshed and saved.")

    if creds and creds.valid:
        if _has_required_scopes(creds):
            return creds
        logger.warning(
            "OAuth token missing required scopes; re-authorizing for %s",
            ", ".join(SCOPES),
        )

    # No valid token – need to run the interactive flow
    oauth_creds_path = Path(config.GOOGLE_OAUTH_CREDS_FILE)
    if not oauth_creds_path.is_file():
        raise FileNotFoundError(
            f"OAuth client credentials not found at {oauth_creds_path}. "
            "Download them from Google Cloud Console."
        )

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(oauth_creds_path), SCOPES)

    # Prefer console flow in headless environments (or when forced).
    force_console = os.getenv("GOOGLE_OAUTH_FORCE_CONSOLE") == "1"
    has_display = bool(os.getenv("DISPLAY")) or bool(os.getenv("WAYLAND_DISPLAY"))

    if force_console or not has_display:
        # Don't attempt to open a browser automatically; print URL and wait.
        creds = flow.run_local_server(port=0, open_browser=False)
    else:
        creds = flow.run_local_server(port=0)
    _save_oauth_token(creds, token_path)
    logger.info("OAuth authorization complete – token saved to %s", token_path)
    return creds


def _save_oauth_token(creds: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else [],
        "universe_domain": getattr(creds, "universe_domain", "googleapis.com"),
        "account": "",
        "expiry": creds.expiry.isoformat() if creds.expiry else "",
    }
    path.write_text(json.dumps(data))


# ── Public entry point ─────────────────────────────────────────────────────


def get_google_clients() -> tuple[Any | None, Any | None]:
    """Return ``(gspread_client, drive_service)`` or ``(None, None)``."""
    if not config.google_enabled:
        logger.info("Google mode disabled – skipping authentication.")
        return None, None

    try:
        _ensure_importlib_metadata_compat()
        import gspread
        from googleapiclient.discovery import build

        if config.google_auth_method == "service_account":
            creds = _auth_service_account()
        else:
            creds = _auth_oauth()

        drive_service = build("drive", "v3", credentials=creds)

        gs_client: Any | None = None
        if _has_spreadsheets_scope(creds):
            try:
                gs_client = gspread.authorize(creds)
                logger.info("Google Sheets client initialized.")
            except Exception:
                logger.exception("Failed to initialize Google Sheets client.")
                gs_client = None
        else:
            logger.warning(
                "OAuth token missing spreadsheets scope; Sheets read/write disabled."
            )

        logger.info("Google authentication successful (method=%s).", config.google_auth_method)
        return gs_client, drive_service

    except Exception:
        logger.exception("Google authentication failed – falling back to local mode.")
        config.google_enabled = False
        return None, None


# ── Standalone: run the OAuth authorization flow ───────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    print("Starting OAuth authorization flow …")
    print(f"Scopes requested: {SCOPES}")
    config.google_enabled = True
    config.google_auth_method = "oauth"
    gs, drv = get_google_clients()
    if drv:
        print("✓ Drive access OK")
    if gs:
        print("✓ Sheets access OK")
    if not drv and not gs:
        print("✗ Authorization failed – check the logs above.")
