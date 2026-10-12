"""Post-LLM normalization: deduplicate, canonicalize, and merge skills.

This module sits between the raw LLM extraction and the output writers.
Even when the LLM prompt instructs correct placement, the model may still
produce duplicates or case variants.  The normalizer guarantees clean output.
"""

from __future__ import annotations

import logging
from typing import Any

from skill_taxonomy import CanonicalSkill, normalize_skill

logger = logging.getLogger(__name__)

PROFICIENCY_RANK = {
    "Expert": 4,
    "Advanced": 3,
    "Intermediate": 2,
    "Beginner": 1,
}

CONTEXT_RANK = {
    "professional": 3,
    "academic": 2,
    "hobby": 1,
}


def _best_level(a: str, b: str) -> str:
    """Return the higher of two proficiency levels."""
    return a if PROFICIENCY_RANK.get(a, 0) >= PROFICIENCY_RANK.get(b, 0) else b


def _best_context(a: str, b: str) -> str:
    """Return the stronger of two contexts (professional > academic > hobby)."""
    return a if CONTEXT_RANK.get(a, 0) >= CONTEXT_RANK.get(b, 0) else b


def normalize_extraction(extraction: dict[str, Any]) -> dict[str, Any]:
    """Normalize an entire extraction dict in-place and return it.

    Handles both the new structured format and the legacy flat-string format:
      - new:    ``{"category": {"skill": {"level": "Advanced", "context": "professional"}}}``
      - legacy: ``{"category": {"skill": "Advanced"}}``

    Steps:
    1. Parse each (category, skill, level, context) tuple from the skills dict.
    2. Canonicalize the skill name and category via the taxonomy.
    3. When a skill appears more than once (across categories or under variant
       names), keep the highest proficiency level and strongest context.
    4. Rebuild the ``skills`` dict with canonical keys.
    """
    raw_skills = extraction.get("skills", {})
    if not isinstance(raw_skills, dict):
        return extraction

    # Collect all (canonical_key -> best level, best context)
    merged: dict[CanonicalSkill, tuple[str, str]] = {}

    for category, items in raw_skills.items():
        if not isinstance(items, dict):
            continue
        for skill_name, value in items.items():
            level, context = _parse_skill_value(value)
            canonical = normalize_skill(category, skill_name)

            if canonical in merged:
                prev_level, prev_context = merged[canonical]
                merged[canonical] = (
                    _best_level(prev_level, level),
                    _best_context(prev_context, context),
                )
            else:
                merged[canonical] = (level, context)

    n_before = sum(
        len(v) for v in raw_skills.values() if isinstance(v, dict)
    )
    n_after = len(merged)
    if n_before != n_after:
        logger.info(
            "  → Normalizer: %d raw skills → %d canonical (merged %d duplicates)",
            n_before, n_after, n_before - n_after,
        )

    # Rebuild grouped by canonical category
    grouped: dict[str, dict[str, dict[str, str]]] = {}
    for cs, (level, context) in merged.items():
        grouped.setdefault(cs.category, {})[cs.name] = {
            "level": level,
            "context": context,
        }

    extraction["skills"] = grouped
    return extraction


def _parse_skill_value(value: Any) -> tuple[str, str]:
    """Extract (level, context) from either format."""
    if isinstance(value, dict):
        level = str(value.get("level", "Intermediate"))
        context = str(value.get("context", "professional"))
    elif isinstance(value, str):
        level = value
        context = "professional"
    else:
        level = str(value)
        context = "professional"

    if level not in PROFICIENCY_RANK:
        level = "Intermediate"
    if context not in CONTEXT_RANK:
        context = "professional"
    return level, context


def normalize_results_batch(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize the extraction inside each worker result dict."""
    for r in results:
        ext = r.get("extraction")
        if ext and isinstance(ext, dict):
            r["extraction"] = normalize_extraction(ext)
    return results
