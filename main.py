#!/usr/bin/env python3
"""CV Parser & Skill Scorer – main entry point.

Usage:
    python main.py                  # auto-detect mode, process new rows
    python main.py --force-all      # reprocess every worker
    python main.py --local          # force local mode even if Google creds exist
    python main.py --dry-run        # list workers that would be processed, then exit
    python main.py --renormalize    # re-normalize existing results.csv through the taxonomy
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

import config
import cv_downloader
import google_auth
import output_writer
import pdf_parser
import skill_extractor
import skill_normalizer
import tracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("cv-parser")


# ── Input reading ───────────────────────────────────────────────────────────


def read_worker_list_google(gs_client: Any) -> pd.DataFrame:
    sheet = gs_client.open_by_key(config.INPUT_SHEET_ID)
    wks = sheet.get_worksheet_by_id(int(config.INPUT_SHEET_GID))
    if wks is None:
        wks = sheet.sheet1
    rows = wks.get_all_values()
    if len(rows) < 2:
        return pd.DataFrame()

    # First row is a description banner; second row has actual headers.
    headers = rows[1]
    data = rows[2:]
    return pd.DataFrame(data, columns=headers)


def read_worker_list_local() -> pd.DataFrame:
    path = config.LOCAL_INPUT_CSV
    # Row 0 is a description banner; row 1 has the real column headers.
    df = pd.read_csv(path, header=1)
    return df


def read_worker_list(gs_client: Any | None) -> pd.DataFrame:
    if config.google_enabled and gs_client:
        try:
            logger.info("Reading worker list from Google Sheet %s …", config.INPUT_SHEET_ID)
            return read_worker_list_google(gs_client)
        except Exception:
            logger.exception("Failed to read Google Sheet – falling back to local CSV.")

    logger.info("Reading worker list from local CSV: %s", config.LOCAL_INPUT_CSV)
    return read_worker_list_local()


def _update_env_file(updates: dict[str, str]) -> None:
    env_path = Path(".env")
    if not env_path.is_file():
        return
    lines = env_path.read_text().splitlines()
    remaining = dict(updates)
    new_lines: list[str] = []
    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            new_lines.append(line)
            continue
        key, _ = line.split("=", 1)
        if key in remaining:
            new_lines.append(f"{key}={remaining.pop(key)}")
        else:
            new_lines.append(line)
    for key, value in remaining.items():
        new_lines.append(f"{key}={value}")
    env_path.write_text("\n".join(new_lines) + "\n")


def ensure_output_sheet(gs_client: Any | None) -> None:
    if not gs_client:
        return
    if config.OUTPUT_SHEET_ID:
        return

    title = f"cv-parser-results-{datetime.utcnow().strftime('%Y%m%d-%H%M')}"
    sheet = gs_client.create(title)
    ws = sheet.sheet1

    config.OUTPUT_SHEET_ID = sheet.id
    config.OUTPUT_SHEET_GID = str(ws.id)
    _update_env_file(
        {
            "OUTPUT_SHEET_ID": config.OUTPUT_SHEET_ID,
            "OUTPUT_SHEET_GID": config.OUTPUT_SHEET_GID,
        }
    )
    logger.info("Created output sheet: %s", sheet.url)


# ── Per-worker processing ──────────────────────────────────────────────────


def process_worker(
    row: pd.Series, drive_service: Any | None
) -> dict[str, Any] | None:
    name = str(row.get("Name", "")).strip()
    email = str(row.get("Email", "")).strip()
    location = str(row.get("Location", "")).strip()
    cv_url = str(row.get("CV", "")).strip()

    if not email:
        logger.warning("Skipping row with no email: %s", row.to_dict())
        return None

    logger.info("Processing: %s (%s)", name, email)

    cv_paths = cv_downloader.get_cv_paths(email, name, cv_url, drive_service)
    if not cv_paths:
        logger.warning("  → No CV available – skipping.")
        return None

    texts = [pdf_parser.extract_text(p) for p in cv_paths]
    combined_text = "\n\n".join(t for t in texts if t)

    if not combined_text.strip():
        logger.warning("  → CV text is empty (parse error?) – skipping.")
        return {
            "name": name,
            "email": email,
            "location": location,
            "extraction": {},
            "status": "CV_PARSE_ERROR",
        }

    extraction = skill_extractor.extract_skills(combined_text)
    return {
        "name": name,
        "email": email,
        "location": location,
        "extraction": extraction,
        "status": "ok" if extraction else "EXTRACTION_FAILED",
    }


# ── Main pipeline ──────────────────────────────────────────────────────────


def _renormalize_existing(gs_client: Any | None, category: str) -> None:
    """Re-normalize an existing results.csv through the skill taxonomy.

    Reads the wide CSV, converts each row back into pseudo-extraction dicts,
    runs the normalizer, and re-writes all outputs.  No LLM calls needed.
    """
    results_path = config.OUTPUT_DIR / "results.csv"
    if not results_path.is_file():
        logger.error("No existing results at %s", results_path)
        sys.exit(1)

    df = pd.read_csv(results_path, keep_default_na=False, na_values=[""])
    logger.info("Re-normalizing %d rows from %s …", len(df), results_path)

    fixed_set = set(output_writer.FIXED_COLUMNS)
    results: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        skills: dict[str, dict[str, str]] = {}
        for col in df.columns:
            if col in fixed_set:
                continue
            val = row[col]
            if output_writer._has_skill(val):
                parts = col.split(" | ", maxsplit=1)
                if len(parts) == 2:
                    cat, skill = parts
                    skills.setdefault(cat, {})[skill] = str(val)

        extraction: dict[str, Any] = {
            "skills": skills,
            "years_of_experience": row.get("Years of Experience", ""),
            "education_level": row.get("Education Level", ""),
            "education_field": row.get("Education Field", ""),
            "domain_expertise_rating": row.get("Domain Expertise Rating", ""),
            "overall_score": row.get("Overall Score", ""),
            "summary": row.get("Summary", ""),
            "reasoning": row.get("Reasoning", ""),
        }
        results.append({
            "name": row.get("Name", ""),
            "email": row.get("Email", ""),
            "location": row.get("Location", ""),
            "extraction": extraction,
        })

    skill_normalizer.normalize_results_batch(results)

    merged_df = output_writer.build_dataframe(results)

    backup = config.OUTPUT_DIR / "results_pre_renorm.csv"
    df.to_csv(backup, index=False)
    logger.info("Backed up original to %s", backup)

    ensure_output_sheet(gs_client)
    out_path = output_writer.write_results(merged_df, gs_client)
    output_writer.write_extra_sheets(
        merged_df, gs_client, category=category, results=results,
    )
    logger.info("Re-normalization complete – %s", out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="CV Parser & Skill Scorer")
    parser.add_argument("--force-all", action="store_true", help="Reprocess every worker.")
    parser.add_argument("--local", action="store_true", help="Force local mode.")
    parser.add_argument("--dry-run", action="store_true", help="List new workers then exit.")
    parser.add_argument(
        "--upload-only",
        action="store_true",
        help="Upload existing output/results.csv to the output Google Sheet.",
    )
    parser.add_argument(
        "--renormalize",
        action="store_true",
        help=(
            "Re-normalize existing results.csv through the skill taxonomy "
            "(deduplicates, canonicalizes names) without re-running the LLM."
        ),
    )
    parser.add_argument(
        "--category",
        default="Data Science",
        help="Skill category to generate a filtered sheet for (default: 'Data Science').",
    )
    args = parser.parse_args()

    if args.local:
        config.google_enabled = False
        logger.info("Local mode forced via --local flag.")

    # 1. Authenticate (optional)
    gs_client, drive_service = google_auth.get_google_clients()
    mode = "Google" if config.google_enabled else "Local"
    logger.info("=== Running in %s mode ===", mode)

    # -- Re-normalization mode (no LLM calls) --
    if args.renormalize:
        _renormalize_existing(gs_client, args.category)
        return

    if args.upload_only:
        if not gs_client:
            logger.error(
                "Google Sheets access unavailable – reauthorize OAuth with spreadsheets scope."
            )
            sys.exit(1)
        ensure_output_sheet(gs_client)
        results_path = config.OUTPUT_DIR / "results.csv"
        if not results_path.is_file():
            logger.error("No local results found at %s", results_path)
            sys.exit(1)
        df = pd.read_csv(results_path)
        out_path = output_writer.write_results(df, gs_client)
        output_writer.write_extra_sheets(df, gs_client, category=args.category)
        logger.info("Upload complete – %s", out_path)
        return

    # 2. Read worker list
    workers_df = read_worker_list(gs_client)
    if workers_df.empty:
        logger.error("Worker list is empty – nothing to do.")
        sys.exit(1)

    emails = workers_df["Email"].dropna().astype(str).str.strip().tolist()
    emails = [e for e in emails if e]

    # 3. Determine which workers are new
    new_emails, processed_map = tracker.filter_new_workers(emails, force_all=args.force_all)

    if not new_emails:
        logger.info("All workers already processed. Use --force-all to reprocess.")
        return

    if args.dry_run:
        logger.info("Dry run – %d workers would be processed:", len(new_emails))
        for e in new_emails:
            name_row = workers_df.loc[workers_df["Email"].str.strip() == e]
            name = name_row.iloc[0]["Name"] if not name_row.empty else "?"
            logger.info("  • %s (%s)", name, e)
        return

    # 4. Process each new worker
    results: list[dict[str, Any]] = []
    for email in new_emails:
        row_match = workers_df.loc[workers_df["Email"].str.strip() == email]
        if row_match.empty:
            continue
        row = row_match.iloc[0]
        result = process_worker(row, drive_service)
        if result:
            results.append(result)
            tracker.mark_processed(processed_map, email)

    if not results:
        logger.warning("No workers were successfully processed.")
        return

    # 4b. Normalize skills (deduplicate, canonicalize)
    skill_normalizer.normalize_results_batch(results)

    # 5. Build output
    new_df = output_writer.build_dataframe(results)
    if args.force_all:
        merged_df = new_df
    else:
        existing_df = output_writer.load_existing_results(gs_client)
        merged_df = output_writer.merge_results(existing_df, new_df)

    # 6. Write
    ensure_output_sheet(gs_client)
    out_path = output_writer.write_results(merged_df, gs_client)
    output_writer.write_extra_sheets(
        merged_df, gs_client, category=args.category, results=results,
    )
    logger.info("Output saved to %s", out_path)

    # 7. Persist tracker
    tracker.save_processed(processed_map)
    logger.info("Done – processed %d new workers.", len(results))


if __name__ == "__main__":
    main()
