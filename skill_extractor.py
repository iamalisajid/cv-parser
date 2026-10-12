"""Extract skills, scores, and metadata from CV text using OpenAI GPT-5.4-mini."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

import config
from schemas import CVExtraction
from skill_taxonomy import canonical_skill_names_for_prompt

logger = logging.getLogger(__name__)

_CANONICAL_SKILLS_BLOCK = canonical_skill_names_for_prompt()

SYSTEM_PROMPT = """\
You are an expert HR technical analyst. Given the full text of a candidate's CV / resume, extract structured information in JSON.

You MUST return valid JSON with exactly this schema (no markdown fences, no extra keys):

{{
  "skills": {{
    "<Category>": {{
      "<Skill>": {{
        "level": "<Beginner|Intermediate|Advanced|Expert>",
        "context": "<professional|academic|hobby>"
      }}
    }}
  }},
  "years_of_experience": <int or null>,
  "education_level": "<highest degree e.g. PhD, Masters, Bachelors, or null>",
  "education_field": "<field of study or null>",
  "domain_expertise_rating": <1-10 int>,
  "overall_score": <0-100 int>,
  "summary": "<2-sentence candidate summary>",
  "reasoning": "<Explain your scoring rationale, skill level assessments, and any assumptions made>"
}}

Rules for the "skills" object:

PROFICIENCY LEVELS – assign based on evidence in the CV:
  * Expert: published research, led teams, 5+ years deep experience in that skill.
  * Advanced: significant project work, 2-5 years focused usage.
  * Intermediate: used in multiple projects or 1-2 years of experience.
  * Beginner: mentioned or used in coursework / single project.

CONTEXT – classify WHERE the skill was primarily used:
  * "professional": Full-time or contract work, production systems, client projects,
    deployed products. Look for company names, job titles, business impact statements.
  * "academic": PhD/Masters research, thesis work, publications, conference papers,
    university lab work. Look for research group names, publication venues, thesis mentions.
  * "hobby": Kaggle competitions, personal side-projects, hackathons, tutorials,
    open-source hobby work, MOOCs. Sections typically labeled "Other Projects",
    "Personal Projects", "Side Projects", "Competitions" often indicate hobby context.
  IMPORTANT: Carefully distinguish actual work experience (professional) or research
  (academic) from hobby/Kaggle/tutorial projects. A Kaggle notebook using PyTorch is
  NOT the same as deploying PyTorch models in production for 3 years.
  If a skill is used in multiple contexts, pick the STRONGEST one (professional > academic > hobby).

CATEGORIES – always try to use these parent categories:
  "Data Science - Machine Learning", "Data Science - Deep Learning",
  "Data Science - NLP", "Data Science - Computer Vision",
  "Data Science - Data Engineering", "Data Science - Statistics",
  "Data Science - Generative AI", "Software Engineering",
  "Programming Languages", "Tools & Frameworks", "Domain Expertise",
  "Cloud & Infrastructure"
  You may add additional categories if the CV warrants it.

CATEGORY RULES:
  * "Data Science - *" categories are ONLY for analytical techniques, modeling methods,
    and statistical skills (e.g. "Clustering", "Anomaly Detection", "Forecasting").
  * Libraries and tools (PyTorch, Pandas, Scikit-learn, LangChain, etc.) go under
    "Tools & Frameworks", NOT under Data Science categories.
  * Infrastructure tools (Docker, Kubernetes, CI/CD, databases) go under
    "Cloud & Infrastructure".
  * "Data Science - Data Engineering" is for data pipeline TECHNIQUES
    (ETL, Data Pipelines, Data Warehousing, Streaming) – NOT for the tools that
    implement them (Spark -> Tools & Frameworks, Airflow -> Tools & Frameworks).

DEDUPLICATION – each skill MUST appear exactly ONCE in its single most appropriate
  category. Do NOT list the same skill (e.g. "Pandas") under multiple categories.

CANONICAL NAMES – use these exact skill names when applicable (case-sensitive):
{canonical_skills}

  For skills not in this list, use a concise, title-cased name.
  Only include skills the candidate demonstrably has based on the CV text.

Scoring guidance:
- overall_score (0-100): holistic rating considering depth and breadth of technical skills, education quality, publication record, and years of experience.
- domain_expertise_rating (1-10): depth of specialisation in their primary domain.
- years_of_experience: total professional experience in years (approximate from dates).

Reasoning guidance:
- In the "reasoning" field, briefly explain why you assigned the overall_score, domain_expertise_rating, and notable skill levels. Mention key evidence from the CV.
  Also note which skills were rated with hobby/academic context and why.
""".format(canonical_skills=_CANONICAL_SKILLS_BLOCK)

USER_PROMPT_TEMPLATE = """\
Analyse the following CV and return the JSON as specified.

--- CV TEXT START ---
{cv_text}
--- CV TEXT END ---
"""

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def _call_openai(cv_text: str) -> dict[str, Any]:
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    prompt_chars = len(cv_text)
    logger.info("  → Sending %d chars to GPT-5.4-mini …", prompt_chars)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(cv_text=cv_text)},
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            t0 = time.time()
            response = client.chat.completions.create(
                model="gpt-5.4-mini",
                messages=messages,
                response_format={"type": "json_object"},
                reasoning_effort="medium",
            )
            elapsed = time.time() - t0
            usage = response.usage
            tokens_in = usage.prompt_tokens if usage else "?"
            tokens_out = usage.completion_tokens if usage else "?"
            logger.info(
                "  → OpenAI response in %.1fs  (tokens: %s in / %s out)",
                elapsed, tokens_in, tokens_out,
            )
            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)

            try:
                validated = CVExtraction.model_validate(parsed)
                result = validated.model_dump()
            except ValidationError as ve:
                logger.warning("  ⚠ Pydantic validation issue, using raw: %s", ve)
                result = parsed

            skills = result.get("skills", {})
            n_categories = len(skills)
            n_skills = sum(len(v) for v in skills.values() if isinstance(v, dict))
            logger.info(
                "  → Extracted %d skills across %d categories  |  score=%s  yoe=%s",
                n_skills, n_categories,
                result.get("overall_score", "?"),
                result.get("years_of_experience", "?"),
            )
            return result
        except json.JSONDecodeError:
            logger.warning("  ✗ Invalid JSON from OpenAI (attempt %d/%d)", attempt, MAX_RETRIES)
        except Exception:
            logger.exception("  ✗ OpenAI API error (attempt %d/%d)", attempt, MAX_RETRIES)
        if attempt < MAX_RETRIES:
            logger.info("  → Retrying in %ds …", RETRY_DELAY_SECONDS * attempt)
            time.sleep(RETRY_DELAY_SECONDS * attempt)

    return {}


def extract_skills(cv_text: str) -> dict[str, Any]:
    """Send CV text to GPT-5.4-mini and return the structured extraction result.

    Returns an empty dict on failure after retries.
    """
    if not cv_text.strip():
        logger.warning("Empty CV text – skipping LLM call.")
        return {}

    if not config.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set – cannot extract skills.")
        return {}

    result = _call_openai(cv_text)
    if not result:
        logger.error("Skill extraction returned empty after %d retries.", MAX_RETRIES)
    return result
