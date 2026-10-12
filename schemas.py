"""Pydantic models for structured CV extraction output."""

from __future__ import annotations

from typing import Any, Optional, Union

from pydantic import BaseModel, Field, model_validator


VALID_LEVELS = {"Beginner", "Intermediate", "Advanced", "Expert"}
VALID_CONTEXTS = {"professional", "academic", "hobby"}


class SkillEntry(BaseModel):
    """A single skill with proficiency level and work context."""

    level: str = Field(
        description="One of: Beginner, Intermediate, Advanced, Expert.",
    )
    context: str = Field(
        default="professional",
        description=(
            "Where the skill was primarily used: "
            "'professional' (work experience, production systems), "
            "'academic' (PhD/Masters research, publications), or "
            "'hobby' (Kaggle, side-projects, hackathons, tutorials)."
        ),
    )


# Type that the LLM may return: either the new structured form or the legacy
# plain-string form ("Advanced").
SkillValue = Union[SkillEntry, str]


class CVExtraction(BaseModel):
    """Structured output from the LLM skill extraction.

    ``skills`` accepts both the new format (``{"level": …, "context": …}``)
    and the legacy flat string (``"Advanced"``).  The validator normalizes
    legacy strings into ``SkillEntry`` objects so downstream code always sees
    the structured form.
    """

    skills: dict[str, dict[str, SkillEntry]] = Field(
        default_factory=dict,
        description=(
            "Nested mapping of category -> {skill_name: SkillEntry}. "
            "SkillEntry has 'level' (Beginner|Intermediate|Advanced|Expert) "
            "and 'context' (professional|academic|hobby)."
        ),
    )
    years_of_experience: Optional[int] = None
    education_level: Optional[str] = None
    education_field: Optional[str] = None
    domain_expertise_rating: int = Field(ge=1, le=10)
    overall_score: int = Field(ge=0, le=100)
    summary: str = ""
    reasoning: str = Field(
        default="",
        description="Model's justification for scores and skill-level assessments.",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_skills(cls, data: Any) -> Any:
        """Accept legacy ``{"category": {"skill": "Advanced"}}`` format and
        convert each plain-string value into ``{"level": <value>, "context": "professional"}``."""
        skills = data.get("skills")
        if not isinstance(skills, dict):
            return data
        coerced: dict[str, dict[str, Any]] = {}
        for category, items in skills.items():
            if not isinstance(items, dict):
                continue
            cat_skills: dict[str, Any] = {}
            for skill_name, value in items.items():
                if isinstance(value, str):
                    cat_skills[skill_name] = {
                        "level": value,
                        "context": "professional",
                    }
                elif isinstance(value, dict):
                    cat_skills[skill_name] = value
                else:
                    cat_skills[skill_name] = {
                        "level": str(value),
                        "context": "professional",
                    }
            coerced[category] = cat_skills
        data["skills"] = coerced
        return data
