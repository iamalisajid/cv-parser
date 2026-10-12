"""Aggregate extraction results into a skill-matrix CSV and optionally push to Google Sheets."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import config
from skill_taxonomy import SKILL_FAMILIES, get_related_skills

logger = logging.getLogger(__name__)

NA_VALUE = "N/A"

PROFICIENCY_LEVELS = ("Expert", "Advanced", "Intermediate", "Beginner")

FIXED_COLUMNS = [
    "Name",
    "Email",
    "Location",
    "Education Level",
    "Education Field",
    "Years of Experience",
    "Domain Expertise Rating",
    "Overall Score",
    "Summary",
    "Reasoning",
]


def _flatten_skills(extraction: dict[str, Any]) -> dict[str, str]:
    """Turn nested ``skills`` dict into a flat ``{col_name: proficiency}`` mapping.

    Handles both the new structured format (``{"level": …, "context": …}``)
    and the legacy plain-string format (``"Advanced"``).
    Column names are ``"Category | Skill"`` with values like ``"Advanced"``.
    """
    flat: dict[str, str] = {}
    skills = extraction.get("skills", {})
    for category, items in skills.items():
        if isinstance(items, dict):
            for skill, value in items.items():
                col_name = f"{category} | {skill}"
                if isinstance(value, dict):
                    flat[col_name] = str(value.get("level", "")) or NA_VALUE
                else:
                    flat[col_name] = str(value) if value else NA_VALUE
        elif isinstance(items, list):
            for skill in items:
                col_name = f"{category} | {skill}"
                flat[col_name] = "Intermediate"
    return flat


def _skill_columns(df: pd.DataFrame) -> list[str]:
    """Return the list of skill columns in *df*."""
    return [c for c in df.columns if c not in FIXED_COLUMNS]


def _has_skill(val: Any) -> bool:
    """Return True if *val* represents a real proficiency (not N/A or empty)."""
    if pd.isna(val):
        return False
    s = str(val).strip()
    return s != "" and s != NA_VALUE and s.lower() != "false"


def build_dataframe(results: list[dict[str, Any]]) -> pd.DataFrame:
    """Build the full output DataFrame from per-worker extraction results."""
    rows: list[dict[str, Any]] = []
    for r in results:
        ext = r.get("extraction", {})
        row: dict[str, Any] = {
            "Name": r.get("name", ""),
            "Email": r.get("email", ""),
            "Location": r.get("location", ""),
            "Education Level": ext.get("education_level", ""),
            "Education Field": ext.get("education_field", ""),
            "Years of Experience": ext.get("years_of_experience", ""),
            "Domain Expertise Rating": ext.get("domain_expertise_rating", ""),
            "Overall Score": ext.get("overall_score", ""),
            "Summary": ext.get("summary", ""),
            "Reasoning": ext.get("reasoning", ""),
        }
        row.update(_flatten_skills(ext))
        rows.append(row)

    df = pd.DataFrame(rows)

    fixed_present = [c for c in FIXED_COLUMNS if c in df.columns]
    skill_cols = sorted(_skill_columns(df))
    df = df[fixed_present + skill_cols]

    for col in skill_cols:
        df[col] = df[col].fillna(NA_VALUE).astype(str)

    empty_cols = [c for c in skill_cols if not df[c].apply(_has_skill).any()]
    if empty_cols:
        df = df.drop(columns=empty_cols)

    return df


# ---------------------------------------------------------------------------
# Load / merge existing results
# ---------------------------------------------------------------------------

def load_existing_results(gs_client: Any | None) -> pd.DataFrame | None:
    """Load previously written results for incremental merging."""
    if config.google_enabled and gs_client and config.OUTPUT_SHEET_ID:
        try:
            sheet = gs_client.open_by_key(config.OUTPUT_SHEET_ID)
            wks = sheet.get_worksheet_by_id(int(config.OUTPUT_SHEET_GID))
            if wks is None:
                wks = sheet.sheet1
            records = wks.get_all_records()
            if records:
                return pd.DataFrame(records)
        except Exception:
            logger.exception("Could not read existing results from Google Sheet.")

    local_path = config.OUTPUT_DIR / "results.csv"
    if local_path.is_file():
        try:
            return pd.read_csv(local_path, keep_default_na=False, na_values=[""])
        except Exception:
            logger.exception("Could not read existing local results.")

    return None


def merge_results(
    existing: pd.DataFrame | None,
    new: pd.DataFrame,
) -> pd.DataFrame:
    """Merge *new* rows into *existing*, deduplicating on Email (new wins)."""
    if existing is None or existing.empty:
        return new

    all_cols = list(dict.fromkeys(list(existing.columns) + list(new.columns)))
    existing = existing.reindex(columns=all_cols).fillna(NA_VALUE)
    new = new.reindex(columns=all_cols).fillna(NA_VALUE)

    new_emails = set(new["Email"].str.strip().str.lower())
    kept = existing[~existing["Email"].str.strip().str.lower().isin(new_emails)]
    merged = pd.concat([kept, new], ignore_index=True)

    skill_cols = _skill_columns(merged)
    empty_cols = [c for c in skill_cols if not merged[c].apply(_has_skill).any()]
    if empty_cols:
        merged = merged.drop(columns=empty_cols)

    return merged


# ---------------------------------------------------------------------------
# Sheet value preparation
# ---------------------------------------------------------------------------

def _prepare_sheet_values(df: pd.DataFrame) -> list[list[Any]]:
    """Convert a DataFrame to a list-of-lists suitable for gspread upload."""
    header = df.columns.tolist()
    rows = []
    for _, row in df.iterrows():
        rows.append([
            "" if pd.isna(row[col]) else str(row[col]) if not isinstance(row[col], (int, float)) else row[col]
            for col in header
        ])
    return [header] + rows


# ---------------------------------------------------------------------------
# Skills Long (sparse) – PRIMARY output format
# ---------------------------------------------------------------------------

_SKILLS_LONG_COLUMNS = [
    "Email", "Name", "Category", "Skill", "Level", "Context", "Related_Skills",
]


def build_skills_long_from_results(results: list[dict[str, Any]]) -> pd.DataFrame:
    """Build the sparse long-format directly from extraction results.

    This preserves the ``context`` field that is lost in the wide CSV.
    Columns: Email, Name, Category, Skill, Level, Context, Related_Skills.
    """
    records: list[dict[str, str]] = []
    for r in results:
        email = r.get("email", "")
        name = r.get("name", "")
        ext = r.get("extraction", {})
        skills = ext.get("skills", {})
        for category, items in skills.items():
            if not isinstance(items, dict):
                continue
            for skill_name, value in items.items():
                level, context = _extract_level_context(value)
                if level and level in PROFICIENCY_LEVELS:
                    related = get_related_skills(skill_name)
                    records.append({
                        "Email": email,
                        "Name": name,
                        "Category": category,
                        "Skill": skill_name,
                        "Level": level,
                        "Context": context,
                        "Related_Skills": ";".join(related) if related else "",
                    })
    return pd.DataFrame(records, columns=_SKILLS_LONG_COLUMNS)


def build_skills_long(df: pd.DataFrame) -> pd.DataFrame:
    """Build sparse long-format from the wide DataFrame.

    Falls back to this when we only have the wide CSV (e.g. upload-only mode).
    Context defaults to 'professional' since it is not stored in the wide format.
    """
    skill_cols = _skill_columns(df)
    records: list[dict[str, str]] = []
    for _, row in df.iterrows():
        email = str(row.get("Email", ""))
        name = str(row.get("Name", ""))
        for col in skill_cols:
            if _has_skill(row[col]):
                parts = col.split(" | ", maxsplit=1)
                cat = parts[0] if len(parts) == 2 else ""
                skill = parts[1] if len(parts) == 2 else col
                related = get_related_skills(skill)
                records.append({
                    "Email": email,
                    "Name": name,
                    "Category": cat,
                    "Skill": skill,
                    "Level": str(row[col]),
                    "Context": "professional",
                    "Related_Skills": ";".join(related) if related else "",
                })
    return pd.DataFrame(records, columns=_SKILLS_LONG_COLUMNS)


def _extract_level_context(value: Any) -> tuple[str, str]:
    """Pull (level, context) from either the structured or legacy format."""
    if isinstance(value, dict):
        return (
            str(value.get("level", "Intermediate")),
            str(value.get("context", "professional")),
        )
    return (str(value), "professional")


# ---------------------------------------------------------------------------
# Expert skill lookup helper
# ---------------------------------------------------------------------------

def get_expert_skills(
    skills_long_df: pd.DataFrame,
    email: str,
    *,
    min_level: str = "Beginner",
) -> pd.DataFrame:
    """Extract the skills for a single person from the sparse DataFrame.

    Returns rows for *email*, filtered to skills at or above *min_level*.
    Defaults to returning all skills (Beginner+).
    """
    rank = {lvl: i for i, lvl in enumerate(reversed(PROFICIENCY_LEVELS))}
    threshold = rank.get(min_level, 0)
    person = skills_long_df[
        skills_long_df["Email"].str.strip().str.lower() == email.strip().lower()
    ].copy()
    person["_rank"] = person["Level"].map(rank)
    return (
        person[person["_rank"] >= threshold]
        .drop(columns=["_rank"])
        .sort_values(["Category", "Level"], ascending=[True, False])
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Domains sheet
# ---------------------------------------------------------------------------

def build_domains(df: pd.DataFrame) -> pd.DataFrame:
    """Extract unique domain expertise entries."""
    skill_cols = _skill_columns(df)
    domain_cols = [c for c in skill_cols if c.lower().startswith("domain expertise")]
    domains: set[str] = set()
    for col in domain_cols:
        parts = col.split(" | ", maxsplit=1)
        if len(parts) == 2 and df[col].apply(_has_skill).any():
            domains.add(parts[1].strip())
    return pd.DataFrame(sorted(domains), columns=["Domain"])


# ---------------------------------------------------------------------------
# Filtered category sheet
# ---------------------------------------------------------------------------

def build_category_sheet(
    df: pd.DataFrame,
    category: str,
    min_people: int = 2,
) -> pd.DataFrame:
    """Build a filtered view showing only skills matching *category*.

    Columns are stripped to just the skill name. Only people with at least
    one skill in the category are included. Values are proficiency levels.

    *min_people* drops skills that fewer than N people have (removes noise
    from LLM miscategorisation).
    """
    skill_cols = _skill_columns(df)
    cat_lower = category.lower()
    matching = [c for c in skill_cols if c.split(" | ")[0].lower().startswith(cat_lower)]

    if not matching:
        logger.warning("No skill columns match category '%s'", category)
        return pd.DataFrame()

    if min_people > 1:
        matching = [
            c for c in matching if df[c].apply(_has_skill).sum() >= min_people
        ]
        if not matching:
            logger.warning("No skill columns with >= %d people for '%s'", min_people, category)
            return pd.DataFrame()

    rename = {}
    seen_names: dict[str, int] = {}
    for col in matching:
        parts = col.split(" | ", maxsplit=1)
        short = parts[1] if len(parts) == 2 else col
        if short in seen_names:
            seen_names[short] += 1
            subcat = parts[0].split(" - ", maxsplit=1)
            suffix = subcat[1] if len(subcat) == 2 else subcat[0]
            short = f"{short} ({suffix})"
        else:
            seen_names[short] = 1
        rename[col] = short

    sub = df[["Name", "Email"] + matching].copy()
    sub = sub.rename(columns=rename)

    has_any = sub.drop(columns=["Name", "Email"]).apply(
        lambda row: any(_has_skill(v) for v in row), axis=1
    )
    sub = sub[has_any].reset_index(drop=True)

    return sub


# ---------------------------------------------------------------------------
# Skill level summary sheet
# ---------------------------------------------------------------------------

def build_skill_level_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-skill counts by proficiency level."""
    skill_cols = _skill_columns(df)
    records: list[dict[str, Any]] = []
    for col in skill_cols:
        parts = col.split(" | ", maxsplit=1)
        cat = parts[0] if len(parts) == 2 else ""
        skill = parts[1] if len(parts) == 2 else col
        counts = {level: 0 for level in PROFICIENCY_LEVELS}
        total = 0
        for val in df[col]:
            s = str(val).strip()
            if s in counts:
                counts[s] += 1
                total += 1
        if total > 0:
            records.append({
                "Category": cat,
                "Skill": skill,
                **{f"{lvl}_Count": counts[lvl] for lvl in PROFICIENCY_LEVELS},
                "Total_Count": total,
            })
    cols = ["Category", "Skill"] + [f"{lvl}_Count" for lvl in PROFICIENCY_LEVELS] + ["Total_Count"]
    out = pd.DataFrame(records, columns=cols)
    return out.sort_values("Total_Count", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Stats sheet
# ---------------------------------------------------------------------------

def build_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Summary statistics across all candidates."""
    sections: list[pd.DataFrame] = []

    # -- Score distribution --
    for metric in ("Overall Score", "Domain Expertise Rating"):
        if metric in df.columns:
            vals = pd.to_numeric(df[metric], errors="coerce").dropna()
            if len(vals):
                for stat_name, stat_val in [
                    ("Min", int(vals.min())),
                    ("Max", int(vals.max())),
                    ("Mean", round(vals.mean(), 1)),
                    ("Median", int(vals.median())),
                ]:
                    sections.append({
                        "Section": "Score Distribution",
                        "Metric": f"{metric} - {stat_name}",
                        "Value": stat_val,
                    })

    # -- Education breakdown --
    if "Education Level" in df.columns:
        edu = df["Education Level"].fillna("Unknown").astype(str)
        for level, count in edu.value_counts().items():
            sections.append({
                "Section": "Education Breakdown",
                "Metric": level,
                "Value": count,
            })

    # -- Experience brackets --
    if "Years of Experience" in df.columns:
        yoe = pd.to_numeric(df["Years of Experience"], errors="coerce").dropna()
        brackets = {"0-2 years": 0, "3-5 years": 0, "6-10 years": 0, "10+ years": 0}
        for v in yoe:
            if v <= 2:
                brackets["0-2 years"] += 1
            elif v <= 5:
                brackets["3-5 years"] += 1
            elif v <= 10:
                brackets["6-10 years"] += 1
            else:
                brackets["10+ years"] += 1
        for k, v in brackets.items():
            sections.append({"Section": "Experience Brackets", "Metric": k, "Value": v})

    # -- Top 20 skills --
    skill_cols = _skill_columns(df)
    skill_counts: dict[str, int] = {}
    for col in skill_cols:
        cnt = int(df[col].apply(_has_skill).sum())
        if cnt > 0:
            parts = col.split(" | ", maxsplit=1)
            label = parts[1] if len(parts) == 2 else col
            skill_counts[label] = skill_counts.get(label, 0) + cnt
    for sk, cnt in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        sections.append({"Section": "Top 20 Skills", "Metric": sk, "Value": cnt})

    # -- Category coverage --
    cat_people: dict[str, int] = {}
    for col in skill_cols:
        cat = col.split(" | ")[0]
        people_with = int(df[col].apply(_has_skill).sum())
        cat_people[cat] = max(cat_people.get(cat, 0), people_with)
    for cat, cnt in sorted(cat_people.items(), key=lambda x: x[1], reverse=True):
        sections.append({"Section": "Category Coverage", "Metric": cat, "Value": cnt})

    if sections:
        return pd.DataFrame(sections)[["Section", "Metric", "Value"]]
    return pd.DataFrame(columns=["Section", "Metric", "Value"])


# ---------------------------------------------------------------------------
# Write to CSV + Google Sheets
# ---------------------------------------------------------------------------

def write_results(df: pd.DataFrame, gs_client: Any | None) -> Path:
    """Write *df* to local CSV and optionally to Google Sheets. Returns local path."""
    local_path = config.OUTPUT_DIR / "results.csv"
    df.to_csv(local_path, index=False)
    logger.info("Results written to %s (%d rows)", local_path, len(df))

    if config.google_enabled and gs_client and config.OUTPUT_SHEET_ID:
        try:
            sheet = gs_client.open_by_key(config.OUTPUT_SHEET_ID)
            wks = sheet.get_worksheet_by_id(int(config.OUTPUT_SHEET_GID))
            if wks is None:
                wks = sheet.sheet1
            wks.clear()
            data = _prepare_sheet_values(df)
            wks.update(range_name="A1", values=data, value_input_option="USER_ENTERED")
            logger.info("Results uploaded to Google Sheet %s", config.OUTPUT_SHEET_ID)
        except Exception:
            logger.exception(
                "Failed to upload to Google Sheet – local CSV is still available at %s",
                local_path,
            )

    return local_path


def build_skill_families(skills_long_df: pd.DataFrame) -> pd.DataFrame:
    """Show which skill families each candidate has coverage in.

    Output columns: Family, Members, Email, Name, Matching_Skills.
    One row per (family, candidate) pair where the candidate has at least one
    member of that family.
    """
    records: list[dict[str, str]] = []
    for family_name, members in sorted(SKILL_FAMILIES.items()):
        members_set = set(members)
        members_str = ", ".join(members)
        for email, group in skills_long_df.groupby("Email"):
            person_skills = set(group["Skill"])
            overlap = person_skills & members_set
            if overlap:
                name = group["Name"].iloc[0]
                records.append({
                    "Family": family_name,
                    "Members": members_str,
                    "Email": str(email),
                    "Name": name,
                    "Matching_Skills": ";".join(sorted(overlap)),
                })
    return pd.DataFrame(
        records,
        columns=["Family", "Members", "Email", "Name", "Matching_Skills"],
    )


def write_extra_sheets(
    df: pd.DataFrame,
    gs_client: Any | None,
    category: str = "Data Science",
    *,
    results: list[dict[str, Any]] | None = None,
) -> None:
    """Write all secondary sheets (local CSV + Google Sheets tabs).

    If *results* is provided, the sparse long-format is built directly from
    the extraction results (preserving context).  Otherwise it falls back to
    building from the wide DataFrame.
    """
    if results is not None:
        skills_long_df = build_skills_long_from_results(results)
    else:
        skills_long_df = build_skills_long(df)

    domains_df = build_domains(df)
    category_df = build_category_sheet(df, category)
    skill_levels_df = build_skill_level_summary(df)
    stats_df = build_stats(df)
    skill_families_df = build_skill_families(skills_long_df)

    cat_slug = category.lower().replace(" ", "_")

    _save_csv(skills_long_df, "skills_long.csv", "Skills long-format (primary)")
    _save_csv(domains_df, "domains.csv", "Domains")
    _save_csv(category_df, f"{cat_slug}.csv", f"{category} filtered")
    _save_csv(skill_levels_df, "skill_levels.csv", "Skill levels")
    _save_csv(stats_df, "stats.csv", "Stats")
    _save_csv(skill_families_df, "skill_families.csv", "Skill families")

    if not (config.google_enabled and gs_client and config.OUTPUT_SHEET_ID):
        return

    try:
        sheet = gs_client.open_by_key(config.OUTPUT_SHEET_ID)
        _write_tab(sheet, "Skills_Long", skills_long_df)
        _write_tab(sheet, "Domains", domains_df)
        if not category_df.empty:
            _write_tab(sheet, category, category_df)
        _write_tab(sheet, "Skill_Levels", skill_levels_df)
        _write_tab(sheet, "Stats", stats_df)
        _write_tab(sheet, "Skill_Families", skill_families_df)
        logger.info("Extra sheets uploaded.")
    except Exception:
        logger.exception("Failed to write extra sheets to Google Sheets.")


def _save_csv(df: pd.DataFrame, filename: str, label: str) -> None:
    path = config.OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    logger.info("%s written to %s (%d entries)", label, path, len(df))


def _write_tab(sheet: Any, title: str, df: pd.DataFrame) -> None:
    """Create or replace a worksheet tab with the given DataFrame contents."""
    try:
        wks = sheet.worksheet(title)
        wks.clear()
    except Exception:
        wks = sheet.add_worksheet(
            title=title,
            rows=max(len(df) + 1, 2),
            cols=max(len(df.columns), 1),
        )

    data = [df.columns.tolist()] + df.fillna("").values.tolist()
    if len(data) > 1:
        wks.update(range_name="A1", values=data, value_input_option="USER_ENTERED")
