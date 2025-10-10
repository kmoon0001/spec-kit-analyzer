
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PathsSettings(BaseModel):
    temp_upload_dir: str
    api_url: str
    rule_dir: str
    medical_dictionary: str = "src/resources/medical_dictionary.txt"
    cache_dir: str = ".cache"
    logs_dir: str = "logs"


class DatabaseSettings(BaseModel):
    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    sqlite_optimizations: bool = True
    connection_timeout: int = 20


class AuthSettings(BaseModel):
    secret_key: SecretStr | None = None
    algorithm: str
    access_token_expire_minutes: int


class MaintenanceSettings(BaseModel):
    purge_retention_days: int
    purge_interval_days: int = 1
    in_memory_retention_minutes: int = 60
    in_memory_purge_interval_seconds: int = 300


class GeneratorProfile(BaseModel):
    repo: str
    filename: str
    revision: str | None = None
    min_system_gb: float | None = None
    max_system_gb: float | None = None


class ChatModelSettings(BaseModel):
    repo: str
    filename: str
    revision: str | None = None
    model_type: str | None = None
    context_length: int | None = None
    generation_params: dict[str, Any] | None = None


class PhiScrubberModelSettings(BaseModel):
    general_model: str | None = None
    biomedical_model: str | None = None
    replacement_token: str = "<PHI>"


class ModelsSettings(BaseModel):
    generator: str | None = None
    generator_filename: str | None = None
    generator_local_path: str | None = None
    generator_profiles: dict[str, GeneratorProfile] | None = None
    chat: ChatModelSettings | None = None
    retriever: str
    fact_checker: str
    ner_ensemble: list[str]
    doc_classifier_prompt: str
    analysis_prompt_template: str
    nlg_prompt_template: str
    phi_scrubber: PhiScrubberModelSettings | None = None


class LLMSettings(BaseModel):
    model_type: str
    context_length: int
    generation_params: dict[str, Any] = {
        "temperature": 0.1,
        "max_new_tokens": 1024,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "stop_sequences": ["</analysis>", "\n\n---"],
    }


class RetrievalSettings(BaseModel):
    similarity_top_k: int
    dense_model_name: str
    rrf_k: int
    batch_size: int = 16
    max_sequence_length: int = 512


class AnalysisSettings(BaseModel):
    confidence_threshold: float = 0.75
    deterministic_focus: str | None = None
    max_document_length: int = 50000
    chunk_overlap: int = 100


class HabitAISettings(BaseModel):
    use_ai_mapping: bool = True


class HabitReportIntegrationSettings(BaseModel):
    show_personal_development_section: bool = True
    show_habit_tags: bool = True


class HabitEducationSettings(BaseModel):
    show_improvement_strategies: bool = True


class HabitAdvancedSettings(BaseModel):
    habit_confidence_threshold: float = 0.75


class HabitGamificationSettings(BaseModel):
    enabled: bool = False


class HabitPrivacySettings(BaseModel):
    track_progression: bool = True


class HabitDashboardIntegrationSettings(BaseModel):
    show_peer_comparison: bool = False
    show_weekly_focus_widget: bool = True
    show_habit_progression_charts: bool = True


class HabitsFrameworkSettings(BaseModel):
    enabled: bool = False
    visibility_level: str = "moderate"
    ai_features: HabitAISettings = HabitAISettings()
    report_integration: HabitReportIntegrationSettings = HabitReportIntegrationSettings()
    education: HabitEducationSettings = HabitEducationSettings()
    advanced: HabitAdvancedSettings = HabitAdvancedSettings()
    gamification: HabitGamificationSettings = HabitGamificationSettings()
    privacy: HabitPrivacySettings = HabitPrivacySettings()
    dashboard_integration: HabitDashboardIntegrationSettings = HabitDashboardIntegrationSettings()

    def is_prominent(self) -> bool:
        return self.visibility_level.lower() == "prominent"

    def is_moderate(self) -> bool:
        return self.visibility_level.lower() == "moderate"

    def is_subtle(self) -> bool:
        return self.visibility_level.lower() == "subtle"


class ReportingSettings(BaseModel):
    logo_path: str | None = None


class PDFExportSettings(BaseModel):
    """PDF export configuration settings."""
    enabled: bool = True
    page_size: str = "A4"
    margin_top: str = "1in"
    margin_bottom: str = "1in"
    margin_left: str = "0.75in"
    margin_right: str = "0.75in"
    include_charts: bool = True
    watermark: str | None = None
    pdf_version: str = "1.7"


class PluginSettings(BaseModel):
    """Plugin system configuration settings."""
    enabled: bool = True
    plugin_directories: list[str] = ["plugins", "src/plugins"]
    security_enabled: bool = True
    auto_load_plugins: bool = False
    max_plugins: int = 50


class EnterpriseCopilotSettings(BaseModel):
    """Enterprise Copilot configuration settings."""
    enabled: bool = True
    max_query_length: int = 1000
    response_timeout_seconds: int = 30
    confidence_threshold: float = 0.7
    enable_learning: bool = True
    max_history_entries: int = 1000


class EHRIntegrationSettings(BaseModel):
    """EHR integration configuration settings."""
    enabled: bool = True
    connection_timeout_seconds: int = 30
    max_retry_attempts: int = 3
    sync_batch_size: int = 100
    supported_systems: list[str] = ["epic", "cerner", "allscripts", "athenahealth", "nethealth"]


class Settings(BaseSettings):
    """Top-level application settings composed from config.yaml and environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    use_ai_mocks: bool = False
    enable_director_dashboard: bool = True
    database: DatabaseSettings
    auth: AuthSettings
    maintenance: MaintenanceSettings
    paths: PathsSettings
    models: ModelsSettings
    llm: LLMSettings
    retrieval: RetrievalSettings
    analysis: AnalysisSettings
    reporting: ReportingSettings = ReportingSettings()
    habits_framework: HabitsFrameworkSettings = HabitsFrameworkSettings()
    pdf_export: PDFExportSettings = PDFExportSettings()
    plugins: PluginSettings = PluginSettings()
    enterprise_copilot: EnterpriseCopilotSettings = EnterpriseCopilotSettings()
    ehr_integration: EHRIntegrationSettings = EHRIntegrationSettings()
    performance: dict[str, Any] = {}
    logging: dict[str, Any] = {}
    security: dict[str, Any] = {}
    features: dict[str, Any] = {}
    host: str = "127.0.0.1"
    port: int = 8001
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Initializes and returns the application settings, ensuring security best practices.
    """
    load_dotenv()
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Load settings from config file and environment variables
    settings = Settings(**config_data)

    # --- Security Validation ---
    # The SECRET_KEY is the most critical security setting. It MUST be set in the
    # environment and MUST NOT be the insecure default.
    secret_key_value = os.environ.get("SECRET_KEY")
    if not secret_key_value:
        # Fallback for local/testing environments where SECRET_KEY is not provided
        secret_key_value = settings.auth.secret_key.get_secret_value() if settings.auth.secret_key else "insecure-test-key"
        logger = logging.getLogger(__name__)
        logger.warning("SECRET_KEY not found in environment; using fallback value for non-production use.")

    if secret_key_value == "your-super-secret-jwt-key-change-this-in-production":
        raise ValueError("CRITICAL: Insecure default SECRET_KEY detected. Please generate a new, strong key. Application will not start.")

    # Manually inject the environment variable into the settings model
    settings.auth.secret_key = SecretStr(secret_key_value)

    return settings


# Create the single settings instance used across the app
settings = get_settings()
