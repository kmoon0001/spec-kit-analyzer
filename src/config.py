import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from functools import lru_cache
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv


class DatabaseSettings(BaseModel):
    url: str


class AuthSettings(BaseModel):
    secret_key: str
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
        for attr in [
            "temp_upload_dir",
            "rule_dir",
            "medical_dictionary",
            "analysis_prompt_template",
            "nlg_prompt_template",
            "doc_classifier_prompt",
        ]:
            setattr(self, attr, (PROJECT_ROOT / getattr(self, attr)).resolve())

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
class AnalysisSettings(BaseModel):
    confidence_threshold: float = Field(
        0.7, description="Minimum confidence score for a finding to be considered valid."
    )
    deterministic_focus: str = Field(
        "- Treatment frequency documented\n- Goals reviewed or adjusted\n- Medical necessity justified",
        description="Default focus points for compliance analysis.",
    )

class MaintenanceSettings(BaseModel):
    purge_retention_days: int
    purge_interval_days: int = 1

class Settings(BaseModel):
    api_url: str
    use_ai_mocks: bool = False
    enable_director_dashboard: bool = False
    database: DatabaseSettings
    auth: AuthSettings
    maintenance: MaintenanceSettings
paths: PathsSettings
    llm: LLMSettings
    retrieval: RetrievalSettings
    analysis: AnalysisSettings
    models: ModelsSettings
    maintenance: MaintenanceSettings
    use_ai_mocks: bool = False
    temp_upload_dir: str
    api_url: str
    rule_dir: str

@lru_cache()
def get_settings() -> Settings:
    # Load environment variables from .env file
    load_dotenv()

    # Using a relative path from the project root is safer.
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Override secret_key from environment variable if it exists
    secret_key = os.environ.get("SECRET_KEY")
    if secret_key:
        config["auth"]["secret_key"] = secret_key

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

    print(config_data) # Debug line from main
    return Settings(**config_data)
