"""Canonical skill taxonomy: names, categories, aliases, and transferability families.

This module serves two purposes:
1. Post-LLM normalization – map messy LLM-produced skill names to canonical
   (name, category) pairs so that duplicates collapse into a single column.
2. Skill family / transferability lookup – expose which skills are closely
   related so that downstream consumers can infer adjacent competencies.
"""

from __future__ import annotations

from typing import NamedTuple

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class CanonicalSkill(NamedTuple):
    name: str
    category: str


# ---------------------------------------------------------------------------
# Canonical skill registry
#
# Keys are *lowercase* lookup tokens (the canonical name lower-cased, plus
# every alias lower-cased).  Values are the (canonical_name, category) pair.
#
# The _RAW list is easier to maintain; it's compiled into the fast lookup dict
# at module load time.
# ---------------------------------------------------------------------------

_RAW_SKILLS: list[tuple[str, str, list[str]]] = [
    # ── Programming Languages ──────────────────────────────────────────────
    ("Python", "Programming Languages", ["python", "py", "python3"]),
    ("SQL", "Programming Languages", ["sql", "structured query language"]),
    ("R", "Programming Languages", ["r", "r language", "rlang"]),
    ("Java", "Programming Languages", ["java"]),
    ("JavaScript", "Programming Languages", ["javascript", "js"]),
    ("TypeScript", "Programming Languages", ["typescript", "ts"]),
    ("C++", "Programming Languages", ["c++", "cpp"]),
    ("C", "Programming Languages", ["c"]),
    ("C#", "Programming Languages", ["c#", "csharp"]),
    ("Scala", "Programming Languages", ["scala"]),
    ("Go", "Programming Languages", ["go", "golang"]),
    ("Rust", "Programming Languages", ["rust"]),
    ("Julia", "Programming Languages", ["julia"]),
    ("MATLAB", "Programming Languages", ["matlab"]),
    ("Kotlin", "Programming Languages", ["kotlin"]),
    ("Swift", "Programming Languages", ["swift"]),
    ("PHP", "Programming Languages", ["php"]),
    ("Ruby", "Programming Languages", ["ruby"]),
    ("Bash", "Programming Languages", ["bash", "shell", "shell scripting"]),
    ("SAS", "Programming Languages", ["sas", "sas programming"]),
    ("Stata", "Programming Languages", ["stata"]),
    ("Perl", "Programming Languages", ["perl"]),
    ("Fortran", "Programming Languages", ["fortran"]),
    ("CUDA", "Programming Languages", ["cuda"]),
    ("Solidity", "Programming Languages", ["solidity"]),
    ("VBA", "Programming Languages", ["vba"]),
    ("LaTeX", "Programming Languages", ["latex"]),
    ("Stan", "Programming Languages", ["stan"]),
    ("Hive", "Programming Languages", ["hive", "hiveql"]),

    # ── Data Science - Machine Learning ────────────────────────────────────
    ("Machine Learning", "Data Science - Machine Learning", ["machine learning", "ml"]),
    ("Supervised Learning", "Data Science - Machine Learning", ["supervised learning"]),
    ("Unsupervised Learning", "Data Science - Machine Learning", ["unsupervised learning"]),
    ("Reinforcement Learning", "Data Science - Machine Learning", ["reinforcement learning", "rl"]),
    ("Feature Engineering", "Data Science - Machine Learning", ["feature engineering"]),
    ("Predictive Modeling", "Data Science - Machine Learning", [
        "predictive modeling", "predictive modelling", "predictive analytics",
    ]),
    ("Classification", "Data Science - Machine Learning", ["classification"]),
    ("Regression", "Data Science - Machine Learning", [
        "regression", "regression modeling", "regression analysis",
    ]),
    ("Clustering", "Data Science - Machine Learning", [
        "clustering", "cluster analysis", "clustering algorithms",
    ]),
    ("Anomaly Detection", "Data Science - Machine Learning", ["anomaly detection"]),
    ("Recommendation Systems", "Data Science - Machine Learning", [
        "recommendation systems", "recommender systems", "collaborative filtering",
        "content-based filtering",
    ]),
    ("XGBoost", "Data Science - Machine Learning", ["xgboost"]),
    ("LightGBM", "Data Science - Machine Learning", ["lightgbm"]),
    ("CatBoost", "Data Science - Machine Learning", ["catboost"]),
    ("Random Forest", "Data Science - Machine Learning", ["random forest"]),
    ("Gradient Boosting", "Data Science - Machine Learning", [
        "gradient boosting", "gradient boosting machines", "gradient boosting trees", "gbm",
    ]),
    ("Decision Trees", "Data Science - Machine Learning", ["decision tree", "decision trees"]),
    ("SVM", "Data Science - Machine Learning", [
        "svm", "support vector machine", "support vector machines",
    ]),
    ("K-Means", "Data Science - Machine Learning", [
        "k-means", "k-means clustering", "kmeans",
    ]),
    ("PCA", "Data Science - Machine Learning", ["pca", "principal component analysis"]),
    ("Dimensionality Reduction", "Data Science - Machine Learning", ["dimensionality reduction"]),
    ("Ensemble Methods", "Data Science - Machine Learning", ["ensemble methods"]),
    ("Model Evaluation", "Data Science - Machine Learning", [
        "model evaluation", "model validation", "cross-validation",
    ]),
    ("Hyperparameter Tuning", "Data Science - Machine Learning", [
        "hyperparameter tuning", "hyperparameter optimization",
    ]),
    ("AutoML", "Data Science - Machine Learning", ["automl", "auto-sklearn", "autokeras"]),
    ("Transfer Learning", "Data Science - Machine Learning", ["transfer learning"]),
    ("Forecasting", "Data Science - Machine Learning", [
        "forecasting", "time series forecasting", "time-series forecasting",
        "demand forecasting",
    ]),
    ("Time Series Analysis", "Data Science - Machine Learning", [
        "time series", "time series analysis", "time series modeling",
    ]),
    ("Causal Inference", "Data Science - Machine Learning", [
        "causal inference", "causal reasoning",
    ]),
    ("A/B Testing", "Data Science - Machine Learning", ["a/b testing", "ab testing"]),
    ("Bayesian Methods", "Data Science - Machine Learning", [
        "bayesian methods", "bayesian modeling", "bayesian modelling",
        "bayesian optimization", "bayesian neural networks",
    ]),
    ("Federated Learning", "Data Science - Machine Learning", ["federated learning"]),
    ("Active Learning", "Data Science - Machine Learning", ["active learning"]),
    ("Model Deployment", "Data Science - Machine Learning", [
        "model deployment", "model serving",
    ]),
    ("Explainable AI", "Data Science - Machine Learning", [
        "explainable ai", "xai", "shap", "lime",
    ]),
    ("t-SNE", "Data Science - Machine Learning", [
        "t-sne", "tsne", "t-distributed stochastic neighbor embedding",
    ]),
    ("UMAP", "Data Science - Machine Learning", [
        "umap", "uniform manifold approximation",
    ]),
    ("DBSCAN", "Data Science - Machine Learning", [
        "dbscan", "density-based clustering",
    ]),
    ("Hierarchical Clustering", "Data Science - Machine Learning", [
        "hierarchical clustering", "agglomerative clustering", "dendrograms",
    ]),
    ("Isolation Forest", "Data Science - Machine Learning", [
        "isolation forest", "isolation forests",
    ]),
    ("ARIMA", "Data Science - Machine Learning", [
        "arima", "sarima", "sarimax", "arma",
    ]),
    ("Graph Algorithms", "Data Science - Machine Learning", [
        "graph algorithms", "graph analytics", "network analysis",
        "community detection", "pagerank",
    ]),

    # ── Data Science - Deep Learning ──────────────────────────────────────
    ("Deep Learning", "Data Science - Deep Learning", ["deep learning", "dl"]),
    ("Neural Networks", "Data Science - Deep Learning", [
        "neural networks", "artificial neural networks",
    ]),
    ("CNN", "Data Science - Deep Learning", [
        "cnn", "cnns", "convolutional neural networks",
    ]),
    ("RNN", "Data Science - Deep Learning", [
        "rnn", "rnns", "recurrent neural networks",
    ]),
    ("LSTM", "Data Science - Deep Learning", [
        "lstm", "bi-lstm", "bidirectional lstm",
    ]),
    ("GRU", "Data Science - Deep Learning", ["gru"]),
    ("Transformer Models", "Data Science - Deep Learning", [
        "transformer models", "transformers", "attention models",
    ]),
    ("GANs", "Data Science - Deep Learning", [
        "gans", "generative adversarial networks",
    ]),
    ("Autoencoders", "Data Science - Deep Learning", [
        "autoencoders", "variational autoencoders", "vae",
    ]),
    ("Graph Neural Networks", "Data Science - Deep Learning", [
        "graph neural networks", "gnn", "gnns",
    ]),
    ("Diffusion Models", "Data Science - Deep Learning", ["diffusion models"]),
    ("Object Detection", "Data Science - Deep Learning", [
        "object detection", "yolo", "yolov3", "yolov8",
    ]),
    ("Image Segmentation", "Data Science - Deep Learning", [
        "image segmentation", "semantic segmentation", "instance segmentation",
    ]),
    ("Fine-Tuning", "Data Science - Deep Learning", ["fine-tuning", "fine tuning"]),
    ("Model Quantization", "Data Science - Deep Learning", [
        "model quantization", "model compression", "pruning",
    ]),
    ("Multi-GPU Training", "Data Science - Deep Learning", [
        "multi-gpu training", "distributed training", "multi-gpu systems",
    ]),
    ("Self-Supervised Learning", "Data Science - Deep Learning", ["self-supervised learning"]),
    ("Multimodal Learning", "Data Science - Deep Learning", [
        "multimodal learning", "multimodal models", "multimodal fusion",
        "vision-language models", "multi-modal",
    ]),
    ("Cross-Modal Learning", "Data Science - Deep Learning", [
        "cross-modal learning", "cross-modal retrieval", "cross-modal alignment",
    ]),

    # ── Data Science - NLP ────────────────────────────────────────────────
    ("NLP", "Data Science - NLP", [
        "nlp", "natural language processing", "natural language understanding",
    ]),
    ("Sentiment Analysis", "Data Science - NLP", ["sentiment analysis"]),
    ("Text Classification", "Data Science - NLP", ["text classification"]),
    ("Named Entity Recognition", "Data Science - NLP", [
        "named entity recognition", "ner", "entity recognition", "entity extraction",
    ]),
    ("Topic Modeling", "Data Science - NLP", ["topic modeling"]),
    ("Machine Translation", "Data Science - NLP", [
        "machine translation", "neural machine translation", "language translation",
    ]),
    ("Question Answering", "Data Science - NLP", ["question answering", "qa"]),
    ("Text Summarization", "Data Science - NLP", [
        "text summarization", "summarization", "abstractive summarization",
        "summarisation",
    ]),
    ("Information Extraction", "Data Science - NLP", ["information extraction"]),
    ("Information Retrieval", "Data Science - NLP", [
        "information retrieval", "search relevance",
    ]),
    ("Speech Recognition", "Data Science - NLP", [
        "speech recognition", "speech-to-text", "speech analytics", "asr",
    ]),
    ("Conversational AI", "Data Science - NLP", [
        "conversational ai", "chatbots", "dialogue systems",
    ]),
    ("Semantic Search", "Data Science - NLP", ["semantic search"]),
    ("Embeddings", "Data Science - NLP", [
        "embeddings", "word2vec", "sentence-bert", "sbert",
        "semantic embeddings",
    ]),

    # ── Data Science - Computer Vision ────────────────────────────────────
    ("Computer Vision", "Data Science - Computer Vision", ["computer vision", "cv"]),
    ("Image Classification", "Data Science - Computer Vision", ["image classification"]),
    ("Image Processing", "Data Science - Computer Vision", [
        "image processing", "image analysis",
    ]),
    ("OCR", "Data Science - Computer Vision", [
        "ocr", "optical character recognition", "tesseract", "tesseract ocr",
    ]),
    ("Face Recognition", "Data Science - Computer Vision", [
        "face recognition", "facial recognition",
    ]),
    ("Medical Imaging", "Data Science - Computer Vision", [
        "medical imaging", "medical image analysis", "ct imaging",
    ]),
    ("Remote Sensing", "Data Science - Computer Vision", [
        "remote sensing", "satellite imagery analysis",
    ]),
    ("Pose Estimation", "Data Science - Computer Vision", ["pose estimation"]),

    # ── Data Science - Generative AI ──────────────────────────────────────
    ("Large Language Models", "Data Science - Generative AI", [
        "large language models", "llm", "llms",
    ]),
    ("Prompt Engineering", "Data Science - Generative AI", ["prompt engineering"]),
    ("RAG", "Data Science - Generative AI", [
        "rag", "retrieval-augmented generation", "retrieval augmented generation",
    ]),
    ("LLM Fine-Tuning", "Data Science - Generative AI", [
        "llm fine-tuning", "llm fine tuning", "sft", "supervised fine-tuning",
        "instruction tuning",
    ]),
    ("LoRA", "Data Science - Generative AI", ["lora", "qlora", "peft"]),
    ("RLHF", "Data Science - Generative AI", [
        "rlhf", "reinforcement learning from human feedback", "dpo",
    ]),
    ("Agentic AI", "Data Science - Generative AI", [
        "agentic ai", "agentic systems", "agentic workflows", "ai agents",
        "agent orchestration", "multi-agent systems", "multi-agent reasoning",
    ]),
    ("Generative AI", "Data Science - Generative AI", [
        "generative ai", "genai", "generative ai systems",
    ]),
    ("Stable Diffusion", "Data Science - Generative AI", ["stable diffusion"]),
    ("Vector Databases", "Data Science - Generative AI", [
        "vector databases", "vector database", "vector indexing",
    ]),
    ("AI Safety", "Data Science - Generative AI", [
        "ai safety", "ai ethics", "ai governance", "responsible ai",
        "red-teaming", "red teaming", "adversarial testing", "constitutional ai",
    ]),

    # ── Data Science - Statistics ─────────────────────────────────────────
    ("Statistical Modeling", "Data Science - Statistics", [
        "statistical modeling", "statistical modelling", "statistical methods",
        "statistical analysis", "applied statistics",
    ]),
    ("Hypothesis Testing", "Data Science - Statistics", ["hypothesis testing"]),
    ("Experimental Design", "Data Science - Statistics", [
        "experimental design", "design of experiments", "experimentation",
        "experimentation design",
    ]),
    ("Regression Analysis", "Data Science - Statistics", [
        "linear regression", "logistic regression",
    ]),
    ("Econometrics", "Data Science - Statistics", [
        "econometrics", "structural econometric modeling",
    ]),
    ("Bayesian Statistics", "Data Science - Statistics", [
        "bayesian statistics", "bayesian mcmc", "bayesian updating",
    ]),
    ("Probability", "Data Science - Statistics", [
        "probability", "probability and statistics",
    ]),
    ("Exploratory Data Analysis", "Data Science - Statistics", [
        "exploratory data analysis", "eda", "data analysis",
    ]),
    ("Data Visualization", "Data Science - Statistics", [
        "data visualization", "data visualisation", "data storytelling",
    ]),

    # ── Data Science - Data Engineering ───────────────────────────────────
    ("Data Pipelines", "Data Science - Data Engineering", [
        "data pipelines", "data pipeline", "pipeline development",
        "data processing pipelines", "pipeline automation",
        "automated data pipelines", "scalable pipelines",
    ]),
    ("ETL", "Data Science - Data Engineering", [
        "etl", "etl pipelines", "etl processes", "etl/elt", "elt",
    ]),
    ("Data Warehousing", "Data Science - Data Engineering", [
        "data warehousing", "data modeling", "data modeling & design",
        "medallion architecture",
    ]),
    ("Data Cleaning", "Data Science - Data Engineering", [
        "data cleaning", "data cleansing", "data wrangling",
        "data manipulation", "data preprocessing", "data processing",
    ]),
    ("Data Quality", "Data Science - Data Engineering", [
        "data quality", "data quality & monitoring", "data validation",
        "data validation & testing", "data testing", "data reliability",
    ]),
    ("Data Governance", "Data Science - Data Engineering", [
        "data governance", "data lineage", "data contracts",
        "master data management",
    ]),
    ("Feature Store", "Data Science - Data Engineering", [
        "feature store", "feature stores",
    ]),
    ("Streaming", "Data Science - Data Engineering", [
        "streaming", "streaming analytics", "real-time data processing",
    ]),
    ("Web Scraping", "Data Science - Data Engineering", [
        "web scraping", "web crawling",
    ]),
    ("Data Drift Detection", "Data Science - Data Engineering", [
        "data drift detection", "data drift", "concept drift",
        "distribution shift", "dataset shift",
    ]),
    ("Experiment Tracking", "Data Science - Data Engineering", [
        "experiment tracking", "experiment management",
        "experiment versioning", "ml experiment tracking",
    ]),
    ("Model Monitoring", "Data Science - Data Engineering", [
        "model monitoring", "model performance monitoring",
        "production model monitoring", "model observability",
    ]),

    # ── Tools & Frameworks ────────────────────────────────────────────────
    ("Pandas", "Tools & Frameworks", ["pandas", "pd"]),
    ("Polars", "Tools & Frameworks", ["polars"]),
    ("NumPy", "Tools & Frameworks", ["numpy", "np"]),
    ("SciPy", "Tools & Frameworks", ["scipy"]),
    ("Scikit-learn", "Tools & Frameworks", [
        "scikit-learn", "sklearn", "scikit learn",
    ]),
    ("PyTorch", "Tools & Frameworks", [
        "pytorch", "torch",
    ]),
    ("TensorFlow", "Tools & Frameworks", ["tensorflow", "tf"]),
    ("Keras", "Tools & Frameworks", ["keras", "keras/tensorflow"]),
    ("JAX", "Tools & Frameworks", ["jax"]),
    ("Hugging Face", "Tools & Frameworks", [
        "hugging face", "huggingface", "hugging face transformers",
    ]),
    ("OpenCV", "Tools & Frameworks", ["opencv"]),
    ("SpaCy", "Tools & Frameworks", ["spacy"]),
    ("NLTK", "Tools & Frameworks", ["nltk"]),
    ("Gensim", "Tools & Frameworks", ["gensim"]),
    ("LangChain", "Tools & Frameworks", ["langchain"]),
    ("LangGraph", "Tools & Frameworks", ["langgraph"]),
    ("LlamaIndex", "Tools & Frameworks", ["llamaindex", "llama index"]),
    ("MLflow", "Tools & Frameworks", ["mlflow"]),
    ("Weights & Biases", "Tools & Frameworks", ["weights & biases", "wandb", "w&b"]),
    ("Apache Spark", "Tools & Frameworks", [
        "apache spark", "spark", "pyspark", "spark mllib",
    ]),
    ("Apache Airflow", "Tools & Frameworks", ["apache airflow", "airflow"]),
    ("Apache Kafka", "Tools & Frameworks", ["apache kafka", "kafka"]),
    ("Prefect", "Tools & Frameworks", ["prefect"]),
    ("Dagster", "Tools & Frameworks", ["dagster"]),
    ("dbt", "Tools & Frameworks", ["dbt"]),
    ("Dask", "Tools & Frameworks", ["dask"]),
    ("Ray", "Tools & Frameworks", ["ray", "ray serve"]),
    ("FAISS", "Tools & Frameworks", ["faiss"]),
    ("Pinecone", "Tools & Frameworks", ["pinecone"]),
    ("Weaviate", "Tools & Frameworks", ["weaviate"]),
    ("ChromaDB", "Tools & Frameworks", ["chromadb", "chroma db", "chroma"]),
    ("Qdrant", "Tools & Frameworks", ["qdrant"]),
    ("Matplotlib", "Tools & Frameworks", ["matplotlib"]),
    ("Seaborn", "Tools & Frameworks", ["seaborn"]),
    ("Plotly", "Tools & Frameworks", ["plotly"]),
    ("D3.js", "Tools & Frameworks", ["d3.js", "d3"]),
    ("Tableau", "Tools & Frameworks", ["tableau"]),
    ("Power BI", "Tools & Frameworks", ["power bi", "powerbi"]),
    ("Looker", "Tools & Frameworks", ["looker", "looker studio"]),
    ("Streamlit", "Tools & Frameworks", ["streamlit"]),
    ("FastAPI", "Tools & Frameworks", ["fastapi"]),
    ("Flask", "Tools & Frameworks", ["flask"]),
    ("Django", "Tools & Frameworks", ["django"]),
    ("React", "Tools & Frameworks", ["react", "react.js", "reactjs"]),
    ("Node.js", "Tools & Frameworks", ["node.js", "nodejs", "node"]),
    ("Next.js", "Tools & Frameworks", ["next.js", "nextjs"]),
    ("Excel", "Tools & Frameworks", [
        "excel", "ms excel", "microsoft excel", "excel macros",
    ]),
    ("Jupyter", "Tools & Frameworks", [
        "jupyter", "jupyter notebook", "jupyter notebooks", "jupyterhub",
    ]),
    ("Git", "Tools & Frameworks", ["git"]),
    ("GitHub", "Tools & Frameworks", ["github"]),
    ("GitLab", "Tools & Frameworks", ["gitlab"]),
    ("ONNX", "Tools & Frameworks", ["onnx"]),
    ("TensorRT", "Tools & Frameworks", ["tensorrt", "tensorrt-llm"]),
    ("vLLM", "Tools & Frameworks", ["vllm"]),
    ("Triton", "Tools & Frameworks", ["triton", "triton inference server"]),
    ("OpenAI API", "Tools & Frameworks", [
        "openai api", "openai", "chatgpt api", "gpt-4", "gpt-4.1",
    ]),
    ("Anthropic Claude", "Tools & Frameworks", [
        "anthropic claude", "claude", "claude sonnet",
    ]),
    ("Google Gemini", "Tools & Frameworks", [
        "google gemini", "gemini", "gemini api",
    ]),
    ("Ollama", "Tools & Frameworks", ["ollama"]),
    ("CrewAI", "Tools & Frameworks", ["crewai"]),
    ("AutoGen", "Tools & Frameworks", ["autogen"]),
    ("Selenium", "Tools & Frameworks", ["selenium"]),
    ("Beautiful Soup", "Tools & Frameworks", [
        "beautiful soup", "beautifulsoup", "bs4",
    ]),
    ("Scrapy", "Tools & Frameworks", ["scrapy"]),
    ("Prophet", "Tools & Frameworks", ["prophet", "neuralprophet"]),
    ("Statsmodels", "Tools & Frameworks", ["statsmodels"]),
    ("PyMC", "Tools & Frameworks", ["pymc"]),
    ("Great Expectations", "Tools & Frameworks", ["great expectations"]),
    ("Pydantic", "Tools & Frameworks", ["pydantic"]),
    ("Neo4j", "Tools & Frameworks", ["neo4j"]),
    ("Snowflake", "Tools & Frameworks", ["snowflake"]),
    ("Databricks", "Tools & Frameworks", ["databricks"]),
    ("SPSS", "Tools & Frameworks", ["spss"]),
    ("SageMaker", "Tools & Frameworks", ["sagemaker", "aws sagemaker", "amazon sagemaker"]),
    ("H2O", "Tools & Frameworks", ["h2o"]),
    ("PyCaret", "Tools & Frameworks", ["pycaret"]),
    ("DVC", "Tools & Frameworks", ["dvc", "data version control"]),
    ("Feast", "Tools & Frameworks", ["feast"]),
    ("Evidently", "Tools & Frameworks", ["evidently", "evidently ai"]),
    ("Kubeflow", "Tools & Frameworks", ["kubeflow"]),

    # ── Cloud & Infrastructure ────────────────────────────────────────────
    ("AWS", "Cloud & Infrastructure", [
        "aws", "amazon web services",
    ]),
    ("Azure", "Cloud & Infrastructure", [
        "azure", "microsoft azure",
    ]),
    ("GCP", "Cloud & Infrastructure", [
        "gcp", "google cloud", "google cloud platform",
    ]),
    ("Docker", "Cloud & Infrastructure", ["docker", "containerization", "containerisation"]),
    ("Kubernetes", "Cloud & Infrastructure", ["kubernetes", "k8s"]),
    ("Terraform", "Cloud & Infrastructure", ["terraform"]),
    ("CI/CD", "Cloud & Infrastructure", [
        "ci/cd", "ci/cd pipelines", "continuous integration",
        "continuous deployment",
    ]),
    ("Jenkins", "Cloud & Infrastructure", ["jenkins"]),
    ("GitHub Actions", "Cloud & Infrastructure", ["github actions"]),
    ("Linux", "Cloud & Infrastructure", [
        "linux", "linux command line", "unix",
    ]),
    ("PostgreSQL", "Cloud & Infrastructure", [
        "postgresql", "postgres",
    ]),
    ("MySQL", "Cloud & Infrastructure", ["mysql"]),
    ("MongoDB", "Cloud & Infrastructure", ["mongodb"]),
    ("Redis", "Cloud & Infrastructure", ["redis"]),
    ("Elasticsearch", "Cloud & Infrastructure", ["elasticsearch"]),
    ("Cassandra", "Cloud & Infrastructure", ["cassandra"]),
    ("BigQuery", "Cloud & Infrastructure", [
        "bigquery", "google bigquery",
    ]),
    ("Redshift", "Cloud & Infrastructure", [
        "redshift", "amazon redshift", "aws redshift",
    ]),
    ("REST APIs", "Cloud & Infrastructure", ["rest apis", "restful apis"]),
    ("GraphQL", "Cloud & Infrastructure", ["graphql"]),
    ("HPC", "Cloud & Infrastructure", [
        "hpc", "high-performance computing", "hpc clusters",
    ]),
    ("MLOps", "Cloud & Infrastructure", ["mlops"]),
    ("Grafana", "Cloud & Infrastructure", ["grafana"]),
    ("Prometheus", "Cloud & Infrastructure", ["prometheus"]),
    ("Helm", "Cloud & Infrastructure", ["helm"]),
    ("CloudFormation", "Cloud & Infrastructure", ["cloudformation"]),
    ("Heroku", "Cloud & Infrastructure", ["heroku"]),
    ("Vertex AI", "Cloud & Infrastructure", ["vertex ai", "google vertex ai"]),
    ("Azure ML", "Cloud & Infrastructure", [
        "azure ml", "azure machine learning",
    ]),

    # ── Software Engineering ──────────────────────────────────────────────
    ("API Development", "Software Engineering", ["api development"]),
    ("Backend Development", "Software Engineering", ["backend development"]),
    ("Frontend Development", "Software Engineering", [
        "frontend development", "front-end development",
    ]),
    ("Full-Stack Development", "Software Engineering", ["full-stack development"]),
    ("Microservices", "Software Engineering", [
        "microservices", "microservices architecture",
    ]),
    ("System Design", "Software Engineering", [
        "system design", "system architecture",
    ]),
    ("Testing", "Software Engineering", [
        "testing", "unit testing", "integration testing",
        "software testing", "testing & debugging",
    ]),
    ("Agile", "Software Engineering", ["agile", "agile/scrum", "scrum"]),
    ("Distributed Systems", "Software Engineering", ["distributed systems"]),
    ("Performance Optimization", "Software Engineering", ["performance optimization"]),
    ("Web Development", "Software Engineering", ["web development"]),
    ("Embedded Systems", "Software Engineering", [
        "embedded systems", "embedded software",
    ]),
    ("OOP", "Software Engineering", [
        "oop", "object-oriented design", "object-oriented programming",
    ]),
    ("Version Control", "Software Engineering", ["version control"]),
    ("Code Review", "Software Engineering", ["code review", "code reviews"]),
    ("Technical Documentation", "Software Engineering", [
        "technical documentation", "documentation",
    ]),
    ("Production Systems", "Software Engineering", [
        "production systems", "production deployment",
    ]),
    ("Dashboard Development", "Software Engineering", [
        "dashboard development", "dashboard automation",
    ]),
    ("Workflow Automation", "Software Engineering", [
        "workflow automation", "automation", "automation scripting",
    ]),
]


# ---------------------------------------------------------------------------
# Build fast lookup: lowercase token -> CanonicalSkill
# ---------------------------------------------------------------------------

SKILL_LOOKUP: dict[str, CanonicalSkill] = {}

for _name, _category, _aliases in _RAW_SKILLS:
    _cs = CanonicalSkill(name=_name, category=_category)
    SKILL_LOOKUP[_name.lower()] = _cs
    for _alias in _aliases:
        SKILL_LOOKUP[_alias.lower()] = _cs


# ---------------------------------------------------------------------------
# Skill families (transferability groups)
#
# Each key is a family name; the value lists *canonical* skill names that are
# closely related / transferable.
# ---------------------------------------------------------------------------

SKILL_FAMILIES: dict[str, list[str]] = {
    "dataframe_libs": ["Pandas", "Polars", "Dask", "NumPy"],
    "deep_learning_frameworks": ["PyTorch", "TensorFlow", "JAX", "Keras"],
    "gradient_boosting": ["XGBoost", "LightGBM", "CatBoost"],
    "ml_libraries": ["Scikit-learn", "PyCaret", "H2O", "AutoML"],
    "cloud_providers": ["AWS", "Azure", "GCP"],
    "container_orchestration": ["Docker", "Kubernetes", "Helm"],
    "sql_databases": ["PostgreSQL", "MySQL", "BigQuery", "Redshift", "Snowflake"],
    "nosql_databases": ["MongoDB", "Redis", "Elasticsearch", "Cassandra", "Neo4j"],
    "vector_databases": ["FAISS", "Pinecone", "Weaviate", "ChromaDB", "Qdrant"],
    "bi_tools": ["Tableau", "Power BI", "Looker"],
    "data_viz_python": ["Matplotlib", "Seaborn", "Plotly"],
    "orchestrators": ["Apache Airflow", "Prefect", "Dagster"],
    "streaming": ["Apache Kafka", "Streaming"],
    "nlp_libraries": ["SpaCy", "NLTK", "Gensim", "Hugging Face"],
    "llm_providers": ["OpenAI API", "Anthropic Claude", "Google Gemini", "Ollama"],
    "agent_frameworks": ["LangChain", "LangGraph", "LlamaIndex", "CrewAI", "AutoGen"],
    "experiment_tracking": ["MLflow", "Weights & Biases"],
    "web_frameworks_python": ["FastAPI", "Flask", "Django", "Streamlit"],
    "web_frameworks_js": ["React", "Node.js", "Next.js"],
    "iac_tools": ["Terraform", "CloudFormation"],
    "ci_cd": ["CI/CD", "Jenkins", "GitHub Actions"],
    "web_scraping": ["Beautiful Soup", "Scrapy", "Selenium"],
    "statistical_languages": ["R", "SAS", "Stata", "SPSS"],
    "version_control": ["Git", "GitHub", "GitLab"],
    "time_series": ["Forecasting", "Time Series Analysis", "Prophet", "Statsmodels"],
    "bayesian": ["Bayesian Methods", "Bayesian Statistics", "PyMC", "Stan"],
    "nlp_tasks": [
        "Sentiment Analysis", "Text Classification", "Named Entity Recognition",
        "Topic Modeling", "Text Summarization", "Question Answering",
    ],
    "cv_tasks": [
        "Image Classification", "Object Detection", "Image Segmentation",
        "OCR", "Face Recognition", "Pose Estimation",
    ],
    "generative_ai": [
        "Large Language Models", "RAG", "Prompt Engineering",
        "LLM Fine-Tuning", "LoRA", "RLHF", "Agentic AI",
    ],
    "data_engineering": [
        "Data Pipelines", "ETL", "Data Warehousing", "Apache Spark",
        "dbt", "Feature Store",
    ],
    "model_serving": ["vLLM", "Triton", "TensorRT", "ONNX", "SageMaker", "Ray"],
    "dimensionality_reduction": ["PCA", "Dimensionality Reduction", "t-SNE", "UMAP"],
    "clustering_methods": [
        "Clustering", "K-Means", "DBSCAN", "Hierarchical Clustering",
    ],
    "anomaly_detection": ["Anomaly Detection", "Isolation Forest", "Autoencoders"],
    "time_series_methods": [
        "Time Series Analysis", "Forecasting", "ARIMA",
        "Prophet", "Statsmodels",
    ],
    "graph_ml": ["Graph Neural Networks", "Graph Algorithms", "Neo4j"],
    "drift_monitoring": [
        "Data Drift Detection", "Model Monitoring", "Evidently",
        "Grafana", "Prometheus",
    ],
    "feature_stores": ["Feature Store", "Feast", "Databricks"],
}

# Reverse index: canonical skill name -> list of family names it belongs to
_SKILL_TO_FAMILIES: dict[str, list[str]] = {}
for _fam, _members in SKILL_FAMILIES.items():
    for _m in _members:
        _SKILL_TO_FAMILIES.setdefault(_m, []).append(_fam)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_skill(category: str, skill_name: str) -> CanonicalSkill:
    """Map a (category, skill_name) pair to its canonical form.

    Looks up by lowercased skill_name first. Falls back to returning the
    original values unchanged (allowing the LLM to create new skills outside
    the taxonomy).
    """
    key = skill_name.strip().lower()
    if key in SKILL_LOOKUP:
        return SKILL_LOOKUP[key]
    return CanonicalSkill(name=skill_name.strip(), category=category.strip())


def get_related_skills(skill_name: str) -> list[str]:
    """Return canonical names of skills that are transferable / closely related.

    If the skill belongs to one or more families, returns all *other* members
    of those families (deduplicated, sorted).
    """
    canonical = normalize_skill("", skill_name).name
    families = _SKILL_TO_FAMILIES.get(canonical, [])
    related: set[str] = set()
    for fam in families:
        related.update(SKILL_FAMILIES[fam])
    related.discard(canonical)
    return sorted(related)


def get_family_names(skill_name: str) -> list[str]:
    """Return the family names a skill belongs to."""
    canonical = normalize_skill("", skill_name).name
    return _SKILL_TO_FAMILIES.get(canonical, [])


def canonical_skill_names_for_prompt() -> str:
    """Return a compact text block listing canonical skills grouped by category.

    Suitable for embedding in the LLM system prompt as a reference.
    """
    by_cat: dict[str, list[str]] = {}
    seen: set[str] = set()
    for name, category, _ in _RAW_SKILLS:
        if name not in seen:
            by_cat.setdefault(category, []).append(name)
            seen.add(name)

    lines: list[str] = []
    for cat in sorted(by_cat):
        skills_str = ", ".join(by_cat[cat])
        lines.append(f"  {cat}: {skills_str}")
    return "\n".join(lines)
