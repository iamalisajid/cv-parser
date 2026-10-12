from __future__ import annotations

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

logger = logging.getLogger(__name__)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Google OAuth login (for web app users)
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET: str = os.getenv("JWT_SECRET", "")

# Google auth – supports Service Account OR OAuth credentials
GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
GOOGLE_OAUTH_CREDS_FILE: str = os.getenv(
    "GOOGLE_OAUTH_CREDS_FILE", "creds/oauth_crednetials.json"
)
GOOGLE_TOKEN_FILE: str = os.getenv("GOOGLE_TOKEN_FILE", "creds/token.json")

INPUT_SHEET_ID: str = os.getenv(
    "INPUT_SHEET_ID", ""
)
INPUT_SHEET_GID: str = os.getenv("INPUT_SHEET_GID", "0")
OUTPUT_SHEET_ID: str = os.getenv("OUTPUT_SHEET_ID", "")
OUTPUT_SHEET_GID: str = os.getenv("OUTPUT_SHEET_GID", "0")

LOCAL_INPUT_CSV: str = os.getenv(
    "LOCAL_INPUT_CSV",
    "sample/example-workers.csv",
)
LOCAL_CV_DIR: str = os.getenv("LOCAL_CV_DIR", "cvs/")

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

PROCESSED_ROWS_FILE = Path("processed_rows.json")

CVS_DIR = Path(LOCAL_CV_DIR)
CVS_DIR.mkdir(exist_ok=True)

# Which auth method is available: "service_account", "oauth", or None
google_auth_method: str | None = None


def _detect_google_enabled() -> bool:
    global google_auth_method

    # Priority 1: Service Account
    if GOOGLE_SERVICE_ACCOUNT_FILE and Path(GOOGLE_SERVICE_ACCOUNT_FILE).is_file():
        google_auth_method = "service_account"
        logger.info("Google auth: using Service Account (%s)", GOOGLE_SERVICE_ACCOUNT_FILE)
        return True

    # Priority 2: OAuth token
    if Path(GOOGLE_TOKEN_FILE).is_file():
        google_auth_method = "oauth"
        logger.info("Google auth: using OAuth token (%s)", GOOGLE_TOKEN_FILE)
        return True

    if Path(GOOGLE_OAUTH_CREDS_FILE).is_file():
        google_auth_method = "oauth"
        logger.info(
            "Google auth: OAuth client creds found but no token yet – "
            "run  python google_auth.py  to authorize."
        )
        return False

    logger.info("No Google credentials found – running in local mode.")
    return False


google_enabled: bool = _detect_google_enabled()
