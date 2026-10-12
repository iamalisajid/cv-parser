"""Fine-grained subdomain expertise scoring computed from existing skill data.

Each subdomain maps to a set of *technique skills* (full weight) and *tool
skills* (partial weight).  A worker's score in a subdomain reflects both depth
(proficiency * context) and breadth (number of relevant skills).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.database import Skill

# ---------------------------------------------------------------------------
# Weights (reuse the same scale as domain_scoring)
# ---------------------------------------------------------------------------

PROFICIENCY_WEIGHT = {"Expert": 4, "Advanced": 3, "Intermediate": 2, "Beginner": 1}
CONTEXT_WEIGHT = {"professional": 1.0, "academic": 0.8, "hobby": 0.5}
MAX_PROFICIENCY = PROFICIENCY_WEIGHT["Expert"]

TOOL_DISCOUNT = 0.4  # tools contribute partial evidence of subdomain mastery

# ---------------------------------------------------------------------------
# Subdomain definitions: {"skills": [...], "tools": [...]}
#
# "skills" = technique / concept canonical names  (full weight)
# "tools"  = library / framework canonical names  (TOOL_DISCOUNT weight)
# ---------------------------------------------------------------------------

SUBDOMAINS: dict[str, dict[str, list[str]]] = {
    # ── Core ML Process (1-6) ─────────────────────────────────────────────
    "Data Cleaning": {
        "skills": [
            "Data Cleaning", "Data Quality", "ETL", "Data Pipelines",
        ],
        "tools": ["Pandas", "Great Expectations", "Polars", "dbt"],
    },
    "Feature Engineering": {
        "skills": [
            "Feature Engineering", "Feature Store", "Dimensionality Reduction",
        ],
        "tools": ["Scikit-learn", "Pandas", "Polars"],
    },
    "EDA": {
        "skills": [
            "Exploratory Data Analysis", "Data Visualization",
            "Statistical Modeling",
        ],
        "tools": [
            "Matplotlib", "Seaborn", "Plotly", "Tableau", "Power BI",
            "Looker", "D3.js",
        ],
    },
    "Model Selection": {
        "skills": [
            "Supervised Learning", "Unsupervised Learning", "Classification",
            "Regression", "Predictive Modeling", "Model Evaluation", "AutoML",
        ],
        "tools": ["Scikit-learn", "PyCaret", "H2O"],
    },
    "Training & Hyperparameter Tuning": {
        "skills": [
            "Hyperparameter Tuning", "Transfer Learning", "Fine-Tuning",
            "Multi-GPU Training", "Deep Learning",
        ],
        "tools": [
            "PyTorch", "TensorFlow", "JAX", "Keras",
            "Weights & Biases", "MLflow", "Ray",
        ],
    },
    "Evaluation & Error Analysis": {
        "skills": [
            "Model Evaluation", "A/B Testing", "Explainable AI",
            "Causal Inference", "Hypothesis Testing", "Experimental Design",
        ],
        "tools": ["MLflow", "Weights & Biases"],
    },

    # ── ML Techniques (7-10) ──────────────────────────────────────────────
    "Ensemble Methods": {
        "skills": [
            "Ensemble Methods", "Gradient Boosting", "Random Forest",
            "Decision Trees",
        ],
        "tools": ["XGBoost", "LightGBM", "CatBoost", "Scikit-learn"],
    },
    "Dimensionality Reduction": {
        "skills": [
            "PCA", "Dimensionality Reduction", "t-SNE", "UMAP",
            "Autoencoders",
        ],
        "tools": ["Scikit-learn"],
    },
    "Clustering": {
        "skills": [
            "Clustering", "K-Means", "DBSCAN", "Hierarchical Clustering",
            "Unsupervised Learning",
        ],
        "tools": ["Scikit-learn"],
    },
    "Anomaly Detection": {
        "skills": [
            "Anomaly Detection", "Isolation Forest", "Autoencoders",
        ],
        "tools": ["Scikit-learn", "PyTorch"],
    },

    # ── Specialized Domains (11-15) ───────────────────────────────────────
    "Time Series": {
        "skills": [
            "Time Series Analysis", "Forecasting", "ARIMA",
        ],
        "tools": ["Prophet", "Statsmodels"],
    },
    "NLP": {
        "skills": [
            "NLP", "Sentiment Analysis", "Text Classification",
            "Named Entity Recognition", "Topic Modeling",
            "Machine Translation", "Question Answering",
            "Text Summarization", "Information Extraction",
            "Information Retrieval", "Speech Recognition",
            "Conversational AI", "Semantic Search", "Embeddings",
        ],
        "tools": ["SpaCy", "NLTK", "Gensim", "Hugging Face"],
    },
    "Computer Vision": {
        "skills": [
            "Computer Vision", "Image Classification", "Image Processing",
            "OCR", "Face Recognition", "Medical Imaging",
            "Remote Sensing", "Pose Estimation",
            "Object Detection", "Image Segmentation", "CNN",
        ],
        "tools": ["OpenCV"],
    },
    "Graph ML": {
        "skills": [
            "Graph Neural Networks", "Graph Algorithms",
        ],
        "tools": ["Neo4j", "PyTorch"],
    },
    "Multimodal Learning": {
        "skills": [
            "Multimodal Learning", "Cross-Modal Learning",
            "Computer Vision", "NLP", "Embeddings",
            "Transformer Models",
        ],
        "tools": ["PyTorch", "Hugging Face"],
    },

    # ── MLOps (16-19) ─────────────────────────────────────────────────────
    "Model Deployment & Serving": {
        "skills": [
            "Model Deployment", "Model Quantization", "REST APIs", "MLOps",
        ],
        "tools": [
            "vLLM", "Triton", "TensorRT", "ONNX", "SageMaker",
            "Ray", "Docker", "FastAPI", "Kubeflow",
        ],
    },
    "Monitoring & Drift Detection": {
        "skills": [
            "Data Drift Detection", "Model Monitoring", "Data Quality",
            "MLOps",
        ],
        "tools": [
            "Grafana", "Prometheus", "Great Expectations", "Evidently",
        ],
    },
    "CI/CD for ML Pipelines": {
        "skills": [
            "CI/CD", "MLOps", "Data Pipelines", "Experiment Tracking",
        ],
        "tools": [
            "MLflow", "Weights & Biases", "GitHub Actions", "Jenkins",
            "DVC", "Kubeflow",
        ],
    },
    "Feature Stores": {
        "skills": [
            "Feature Store", "Data Pipelines",
        ],
        "tools": ["Feast", "Databricks", "SageMaker"],
    },
}

# ---------------------------------------------------------------------------
# Tier groupings (for frontend rendering)
# ---------------------------------------------------------------------------

SUBDOMAIN_TIERS: dict[str, list[str]] = {
    "Core ML Process": [
        "Data Cleaning", "Feature Engineering", "EDA",
        "Model Selection", "Training & Hyperparameter Tuning",
        "Evaluation & Error Analysis",
    ],
    "ML Techniques": [
        "Ensemble Methods", "Dimensionality Reduction",
        "Clustering", "Anomaly Detection",
    ],
    "Specialized Domains": [
        "Time Series", "NLP", "Computer Vision",
        "Graph ML", "Multimodal Learning",
    ],
    "MLOps": [
        "Model Deployment & Serving", "Monitoring & Drift Detection",
        "CI/CD for ML Pipelines", "Feature Stores",
    ],
}

# Reverse lookup: subdomain name -> tier name
_SUBDOMAIN_TO_TIER: dict[str, str] = {}
for _tier, _subs in SUBDOMAIN_TIERS.items():
    for _s in _subs:
        _SUBDOMAIN_TO_TIER[_s] = _tier


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _skill_name_set(names: list[str]) -> set[str]:
    """Build a case-insensitive lookup set."""
    return {n.lower() for n in names}


def compute_subdomain_score(skills: list[Skill], subdomain: str) -> int:
    """Return a 0-100 score for a worker's expertise in *subdomain*.

    Technique skills receive full proficiency/context weight; tool skills
    receive ``TOOL_DISCOUNT`` of that weight.
    """
    defn = SUBDOMAINS.get(subdomain)
    if not defn:
        return 0

    skill_names = _skill_name_set(defn["skills"])
    tool_names = _skill_name_set(defn["tools"])

    total_weighted = 0.0
    matched = 0

    for s in skills:
        s_lower = s.skill_name.lower()
        is_skill = s_lower in skill_names
        is_tool = s_lower in tool_names

        if not is_skill and not is_tool:
            continue

        prof = PROFICIENCY_WEIGHT.get(s.proficiency, 1)
        ctx = CONTEXT_WEIGHT.get(s.context, 0.5)
        weight = prof * ctx

        if is_tool and not is_skill:
            weight *= TOOL_DISCOUNT

        total_weighted += weight
        matched += 1

    if matched == 0:
        return 0

    total_possible_skills = len(defn["skills"]) + len(defn["tools"])
    max_possible = matched * MAX_PROFICIENCY * 1.0
    raw = (total_weighted / max_possible) * 100 if max_possible else 0

    breadth_bonus = min(matched / max(total_possible_skills * 0.5, 1), 1.0) * 15
    score = raw * 0.85 + breadth_bonus

    return min(int(round(score)), 100)


def compute_all_subdomain_scores(
    skills: list[Skill],
) -> list[dict[str, Any]]:
    """Compute scores for every subdomain, returned with tier metadata."""
    results: list[dict[str, Any]] = []
    for subdomain in SUBDOMAINS:
        score = compute_subdomain_score(skills, subdomain)
        results.append({
            "subdomain": subdomain,
            "tier": _SUBDOMAIN_TO_TIER.get(subdomain, ""),
            "score": score,
        })
    return results


def compute_all_subdomain_scores_for_worker(
    db: Session, worker_id: int,
) -> list[dict[str, Any]]:
    """Fetch skills from DB and compute all subdomain scores for a worker."""
    skills = db.query(Skill).filter(Skill.worker_id == worker_id).all()
    return compute_all_subdomain_scores(skills)


def list_subdomains() -> list[dict[str, Any]]:
    """Return subdomain names grouped by tier."""
    result: list[dict[str, Any]] = []
    for tier, subs in SUBDOMAIN_TIERS.items():
        for sub in subs:
            result.append({"subdomain": sub, "tier": tier})
    return result
