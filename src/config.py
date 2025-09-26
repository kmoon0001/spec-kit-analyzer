import os
import yaml
from functools import lru_cache
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field

# --- Configuration Models ---

class DatabaseConfig(BaseModel):
    url: str = Field(default="sqlite:///./test.db")

class AuthConfig(BaseModel):
    secret_key: str = Field(default="a_very_secret_key")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

class MaintenanceConfig(BaseModel):
    purge_retention_days: int = Field(default=30, description="Days to retain old reports before purging.")

class ModelsConfig(BaseModel):
    generator: str
    generator_filename: Optional[str] = None
    retriever: str
    fact_checker: str
    doc_classifier_prompt: str
    analysis_prompt_template: str
    ner_primary_model: str # Explicitly define the primary model
    ner_ensemble: List[str] = Field(default_factory=list)
    nlg_prompt_template: str = ""

class RetrievalSettingsConfig(BaseModel):
    similarity_top_k: int = 5

class AppConfig(BaseModel):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    maintenance: MaintenanceConfig = Field(default_factory=MaintenanceConfig)
    models: ModelsConfig
    llm_settings: Dict[str, Any] = Field(default_factory=dict)
    retrieval_settings: RetrievalSettingsConfig = Field(default_factory=RetrievalSettingsConfig)

# --- Configuration Loading ---

def load_config_from_yaml(path: str = "config.yaml") -> dict:
    """Loads configuration from a YAML file."""
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f) or {} # Return empty dict if file is empty
    # If the config file doesn't exist, Pydantic will use defaults or fail on missing required fields.
    return {}

@lru_cache()
def get_config() -> AppConfig:
    """
    Loads, validates, and caches the application configuration.
    Raises pydantic.ValidationError if the configuration is invalid.
    """
    config_data = load_config_from_yaml()
    return AppConfig.model_validate(config_data)