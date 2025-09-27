import yaml
from functools import lru_cache
from pydantic import BaseModel
from typing import List, Dict, Any

class DatabaseSettings(BaseModel):
    url: str

class AuthSettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

class MaintenanceSettings(BaseModel):
    purge_retention_days: int

class ModelsSettings(BaseModel):
    generator: str
    generator_filename: str
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

@lru_cache()
def get_settings() -> Settings:
    with open("src/config.yaml", "r") as f:
        config_data = yaml.safe_load(f)
    return Settings(**config_data)
