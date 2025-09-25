import os
import yaml
from pydantic import BaseModel
from typing import List, Optional

class ModelsConfig(BaseModel):
    ner_model: str
    retriever: str
    llm_repo_id: str
    llm_filename: str
    prompt_template: str
    quantization: str

class RetrievalSettingsConfig(BaseModel):
    similarity_top_k: int

class IterativeRetrievalConfig(BaseModel):
    max_iterations: int

class PathsConfig(BaseModel):
    index_dir: str
    docs_dir: str

class OCRConfig(BaseModel):
    preprocessing: bool
    deskew: bool
    resolution: int

class Settings(BaseModel):
    app_name: str
    environment: str
    db_path: str
    encryption_key: str
    ocr_engine: str
    nlp_models: List[str]
    rubric_path: str
    report_path: str
    report_retention_hours: int
    auto_update: bool
    analytics_path: str
    phi_scrubber: str
    ui_mode: str
    section_headers: List[str]
    ocr: OCRConfig
    models: ModelsConfig
    retrieval_settings: RetrievalSettingsConfig
    iterative_retrieval: IterativeRetrievalConfig
    paths: PathsConfig
    api_url: Optional[str] = "http://127.0.0.1:8000"

def get_settings() -> Settings:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Convert keys to lowercase
    config_data_lower = {k.lower(): v for k, v in config_data.items()}

    return Settings(**config_data_lower)

settings = get_settings()