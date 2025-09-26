import os
from pydantic import BaseModel, Field
import yaml
from functools import lru_cache

class DatabaseConfig(BaseModel):
    url: str = Field(default="sqlite:///./test.db")

class AuthConfig(BaseModel):
    secret_key: str = Field(default="a_very_secret_key")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

class RetrieverConfig(BaseModel):
    dense_model_name: str = Field(default="pritamdeka/S-PubMedBert-MS-MARCO", description="The name of the sentence transformer model for dense retrieval.")
    rrf_k: int = Field(default=60, description="The 'k' parameter for Reciprocal Rank Fusion (RRF) to balance keyword and semantic search.")

class Settings(BaseModel):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)

def load_config_from_yaml(path: str = "config.yaml") -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            # Return an empty dict if the file is empty to prevent errors
            return yaml.safe_load(f) or {}
    return {}

@lru_cache()
def get_settings() -> Settings:
    """
    Loads the application settings from the YAML file.
    The result is cached to avoid repeated file I/O.
    """
    config_data = load_config_from_yaml()
    return Settings.model_validate(config_data)

settings = get_settings()
