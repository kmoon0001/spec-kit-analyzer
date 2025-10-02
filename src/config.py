import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class PathsSettings(BaseModel):
    temp_upload_dir: str
    api_url: str
    rule_dir: str


class DatabaseSettings(BaseModel):
    url: str
    echo: bool = False


class AuthSettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


class MaintenanceSettings(BaseModel):
    purge_retention_days: int
    purge_interval_days: int = 1


class GeneratorProfile(BaseModel):
    repo: str
    filename: str
    revision: Optional[str] = None
    min_system_gb: Optional[float] = None
    max_system_gb: Optional[float] = None


class ChatModelSettings(BaseModel):
    repo: str
    filename: str
    revision: Optional[str] = None
    model_type: Optional[str] = None
    context_length: Optional[int] = None
    generation_params: Optional[Dict[str, Any]] = None


class PhiScrubberModelSettings(BaseModel):
    general: str
    biomedical: str


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
    phi_scrubber: Optional[PhiScrubberModelSettings] = None


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
        0.7,
        description="Minimum confidence score for a finding to be considered valid.",
    )
    deterministic_focus: str = Field(
        "- Treatment frequency documented\n- Goals reviewed or adjusted\n- Medical necessity justified",
        description="Default focus points for compliance analysis.",
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    enable_director_dashboard: bool = False
    database: DatabaseSettings
    auth: AuthSettings
    maintenance: MaintenanceSettings
    paths: PathsSettings
    llm: LLMSettings
    retrieval: RetrievalSettings
    analysis: AnalysisSettings
    models: ModelsSettings
    use_ai_mocks: bool = False

    # This field will be populated from the SECRET_KEY in the .env file
    SECRET_KEY: Optional[str] = None


@lru_cache()
def get_settings() -> Settings:
    """
    Initializes and returns the application settings.

    It loads a base configuration from 'config.yaml' and then overrides
    it with any settings defined in a .env file or environment variables.
    """
    with open("config.yaml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Initialize settings. pydantic-settings will load from .env and environment
    settings = Settings(**config_data)

    # Manually override the secret key if it was loaded from the environment
    if settings.SECRET_KEY:
        settings.auth.secret_key = settings.SECRET_KEY

    return settings