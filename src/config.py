import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


class DatabaseSettings(BaseModel):
    url: str


class AuthSettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


class MaintenanceSettings(BaseModel):
    purge_retention_days: int

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Resolve all paths relative to the project root to make them absolute.
        for attr in [
            "temp_upload_dir",
            "rule_dir",
            "medical_dictionary",
            "analysis_prompt_template",
            "nlg_prompt_template",
            "doc_classifier_prompt",
        ]:
            setattr(self, attr, (PROJECT_ROOT / getattr(self, attr)).resolve())

class GeneratorProfile(BaseModel):
    repo: str
    filename: str
    min_system_gb: Optional[float] = None
    max_system_gb: Optional[float] = None


class ChatModelSettings(BaseModel):
    repo: str
    filename: str
    model_type: Optional[str] = None
    context_length: Optional[int] = None
    generation_params: Optional[Dict[str, Any]] = None


class ModelsSettings(BaseModel):
    generator: Optional[str] = None
    generator_filename: Optional[str] = None
    generator_profiles: Optional[Dict[str, GeneratorProfile]] = None
    chat: Optional[ChatModelSettings] = None
    retriever: str
    fact_checker: str
    ner_ensemble: List[str]
    doc_classifier_prompt: str
    analysis_prompt_template: str
    nlg_prompt_template: str


class LLMSettings(BaseModel):
    model_type: str
    context_length: int
    generation_params: Dict[str, Any]


class RetrievalSettings(BaseModel):
    similarity_top_k: int
    dense_model_name: str
    rrf_k: int

class AnalysisSettings(BaseModel):
    confidence_threshold: float = Field(
        0.7, description="Minimum confidence score for a finding to be considered valid."
    )
    deterministic_focus: str

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Load deterministic_focus from file
        deterministic_focus_path = PROJECT_ROOT / "src/resources/deterministic_focus.txt"
        if deterministic_focus_path.is_file():
            with open(deterministic_focus_path, "r", encoding="utf-8") as f:
                self.deterministic_focus = f.read()
        else:
            self.deterministic_focus = (
                "- Treatment frequency documented\n"
                "- Goals reviewed or adjusted\n"
                "- Medical necessity justified"
            ) # Fallback to hardcoded if file not found

class MaintenanceSettings(BaseModel):
    purge_retention_days: int
    purge_interval_days: int = 1

class Settings(BaseModel):
    database: DatabaseSettings
    auth: AuthSettings
    maintenance: MaintenanceSettings
    models: ModelsSettings
    llm_settings: LLMSettings
    retrieval_settings: RetrievalSettings
    temp_upload_dir: str
    api_url: str
    rule_dir: str
    use_ai_mocks: Optional[bool] = False


@lru_cache()
def get_settings() -> Settings:
    # Using a relative path from the project root is safer.
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return Settings(**config)

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

    # Load deterministic_focus from file and add to config_data
    deterministic_focus_path = PROJECT_ROOT / "src/resources/deterministic_focus.txt"
    if deterministic_focus_path.is_file():
        with open(deterministic_focus_path, "r", encoding="utf-8") as f:
            config_data.setdefault("analysis", {})["deterministic_focus"] = f.read()
    else:
        # Fallback to hardcoded if file not found
        config_data.setdefault("analysis", {})["deterministic_focus"] = (
            "- Treatment frequency documented\n"
            "- Goals reviewed or adjusted\n"
            "- Medical necessity justified"
        )

    return Settings(**config_data)