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

class AppConfig(BaseModel):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)

def load_config_from_yaml(path: str = "config.yaml") -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)
    return {}

@lru_cache()
def get_config() -> AppConfig:
    config_data = load_config_from_yaml()
    return AppConfig.model_validate(config_data)