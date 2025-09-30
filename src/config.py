import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# --- Path Configuration ---
# Use pathlib to build robust, OS-agnostic paths. This makes the application
# runnable from any directory.
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"

# --- Pydantic Model Definitions ---

class DatabaseSettings(BaseModel):
    url: str
    echo: bool = False

class AuthSettings(BaseModel):
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str
    access_token_expire_minutes: int

class PathsSettings(BaseModel):
    temp_upload_dir: Path
    rule_dir: Path
    medical_dictionary: Path
    analysis_prompt_template: Path
    nlg_prompt_template: Path
    doc_classifier_prompt: Path

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Resolve all paths relative to the project root to make them absolute.
        self.temp_upload_dir = (PROJECT_ROOT / self.temp_upload_dir).resolve()
        self.rule_dir = (PROJECT_ROOT / self.rule_dir).resolve()
        self.medical_dictionary = (PROJECT_ROOT / self.medical_dictionary).resolve()
        self.analysis_prompt_template = (
            PROJECT_ROOT / self.analysis_prompt_template
        ).resolve()
        self.nlg_prompt_template = (
            PROJECT_ROOT / self.nlg_prompt_template
        ).resolve()
        self.doc_classifier_prompt = (
            PROJECT_ROOT / self.doc_classifier_prompt
        ).resolve()

class LLMSettings(BaseModel):
    repo: str
    filename: str
    model_type: str = "llama"
    context_length: int = 2048
    generation_params: Dict[str, Any] = {"temperature": 0.1, "max_new_tokens": 2048}

class RetrievalSettings(BaseModel):
    dense_model_name: str
    similarity_top_k: int
    rrf_k: int

class AnalysisSettings(BaseModel):
    confidence_threshold: float = Field(
        0.7, description="Minimum confidence score for a finding to be considered valid."
    )
    deterministic_focus: str = Field(
        "- Treatment frequency documented\n- Goals reviewed or adjusted\n- Medical necessity justified",
        description="Default focus points for compliance analysis.",
    )

class PhiScrubberModelSettings(BaseModel):
    general: str
    biomedical: str

class ModelsSettings(BaseModel):
    fact_checker: str
    ner_ensemble: List[str]
    phi_scrubber: PhiScrubberModelSettings

class MaintenanceSettings(BaseModel):
    purge_retention_days: int
    purge_interval_days: int = 1

class Settings(BaseModel):
    api_url: str
    use_ai_mocks: bool = False
    database: DatabaseSettings
    auth: AuthSettings
    paths: PathsSettings
    llm: LLMSettings
    retrieval: RetrievalSettings
    analysis: AnalysisSettings
    models: ModelsSettings
    maintenance: MaintenanceSettings

# --- Settings Loader ---

@lru_cache()
def get_settings() -> Settings:
    """
    Loads settings from a YAML file and environment variables.

    This function implements a layered configuration approach:
    1.  Loads configuration from the default YAML file.
    2.  Overrides sensitive values (like SECRET_KEY and DATABASE_URL) with
        environment variables if they are set.
    The result is cached for performance.
    """
    load_dotenv()

    if not DEFAULT_CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {DEFAULT_CONFIG_PATH}")

    with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Allow environment variables to override key settings.
    secret_key_env = os.environ.get("SECRET_KEY")
    if secret_key_env:
        config_data.setdefault("auth", {})["secret_key"] = secret_key_env

    db_url_env = os.environ.get("DATABASE_URL")
    if db_url_env:
        config_data.setdefault("database", {})["url"] = db_url_env

    return Settings(**config_data)