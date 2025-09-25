import os
from pydantic import BaseModel, Field
import yaml

class DatabaseConfig(BaseModel):
    url: str = Field(..., env="DATABASE_URL")

class AuthConfig(BaseModel):
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(..., env="ALGORITHM")
    access_token_expire_minutes: int = Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES")

class AppConfig(BaseModel):
    database: DatabaseConfig
    auth: AuthConfig

def load_config_from_yaml(path: str = "config.yaml") -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)
    return {}

def get_config() -> AppConfig:
    config_data = load_config_from_yaml()
    # This will now raise a validation error if env vars are not set
    return AppConfig.parse_obj(config_data)

config = get_config()
