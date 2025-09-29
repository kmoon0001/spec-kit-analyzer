
import yaml
from functools import lru_cache
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class DatabaseSettings(BaseModel):
    url: str


class AuthSettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


class MaintenanceSettings(BaseModel):
    purge_retention_days: int


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
    enable_habit_coaching: bool = False
    enable_director_dashboard: bool = False


@lru_cache()
def get_settings() -> Settings:
    # Using a relative path from the project root is safer.
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return Settings(**config)
