from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
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
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    # SQLite-specific settings
    sqlite_optimizations: bool = True
    connection_timeout: int = 20


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
    general_model: Optional[str] = None
    biomedical_model: Optional[str] = None
    replacement_token: str = "<PHI>"


class ModelsSettings(BaseModel):
    generator: Optional[str] = None
    generator_filename: Optional[str] = None
    generator_local_path: Optional[str] = None
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
    generation_params: Dict[str, Any] = {
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


class HabitsReportIntegration(BaseModel):
    """Settings for habits integration in reports."""

    show_habit_tags: bool = True
    show_personal_development_section: bool = True
    show_habit_tooltips: bool = True
    habit_section_expanded_by_default: bool = False


class HabitsDashboardIntegration(BaseModel):
    """Settings for habits integration in dashboard."""

    show_growth_journey_tab: bool = True
    show_weekly_focus_widget: bool = True
    show_habit_progression_charts: bool = True
    show_peer_comparison: bool = False


class HabitsAIFeatures(BaseModel):
    """AI-powered habits features settings."""

    use_ai_mapping: bool = False
    use_ai_coaching: bool = False
    personalized_strategies: bool = True


class HabitsGamification(BaseModel):
    """Gamification and motivation settings."""

    enabled: bool = True
    show_badges: bool = True
    show_streaks: bool = True
    show_milestones: bool = True
    notifications_enabled: bool = False


class HabitsEducation(BaseModel):
    """Educational content settings."""

    show_habit_resources: bool = True
    show_clinical_examples: bool = True
    show_improvement_strategies: bool = True
    show_templates: bool = True


class HabitsPrivacy(BaseModel):
    """Privacy and data settings."""

    track_progression: bool = True
    anonymous_analytics: bool = True
    share_achievements: bool = False


class HabitsAdvanced(BaseModel):
    """Advanced habits framework settings."""

    habit_confidence_threshold: float = 0.6
    focus_area_threshold: float = 0.20
    mastery_threshold: float = 0.05
    weekly_focus_enabled: bool = True
    auto_suggest_templates: bool = True


class HabitsFrameworkSettings(BaseModel):
    """Complete 7 Habits framework configuration."""

    enabled: bool = True
    visibility_level: str = "moderate"  # "subtle", "moderate", or "prominent"
    report_integration: HabitsReportIntegration = HabitsReportIntegration()
    dashboard_integration: HabitsDashboardIntegration = HabitsDashboardIntegration()
    ai_features: HabitsAIFeatures = HabitsAIFeatures()
    gamification: HabitsGamification = HabitsGamification()
    education: HabitsEducation = HabitsEducation()
    privacy: HabitsPrivacy = HabitsPrivacy()
    advanced: HabitsAdvanced = HabitsAdvanced()

    def is_subtle(self) -> bool:
        """Check if visibility is set to subtle."""
        return self.visibility_level.lower() == "subtle"

    def is_moderate(self) -> bool:
        """Check if visibility is set to moderate."""
        return self.visibility_level.lower() == "moderate"

    def is_prominent(self) -> bool:
        """Check if visibility is set to prominent."""
        return self.visibility_level.lower() == "prominent"


class AnalysisSettings(BaseModel):
    confidence_threshold: float = Field(
        0.75,
        description="Minimum confidence score for a finding to be considered valid.",
    )
    deterministic_focus: str = Field(
        "- Treatment frequency documented\n- Goals reviewed or adjusted\n- Medical necessity justified",
        description="Default focus points for compliance analysis.",
    )
    max_document_length: int = Field(
        50000,
        description="Maximum document length in characters for processing.",
    )
    chunk_overlap: int = Field(
        100,
        description="Overlap between text chunks for context preservation.",
    )
    parallel_processing: bool = Field(
        True,
        description="Enable parallel analysis processing where possible.",
    )


class PerformanceSettings(BaseModel):
    """Performance and caching configuration."""

    # Memory management
    max_cache_memory_mb: int = 2048
    embedding_cache_size: int = 1000
    ner_cache_size: int = 500
    llm_cache_size: int = 200

    # Processing optimization
    use_gpu: bool = False
    model_quantization: bool = True
    batch_size: int = 4
    max_workers: int = 2

    # Timeouts and limits
    analysis_timeout_minutes: int = 10
    model_load_timeout_minutes: int = 5
    api_request_timeout_seconds: int = 30


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    file_rotation: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5


class SecuritySettings(BaseModel):
    """Security configuration."""

    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    enable_cors: bool = False
    allowed_file_extensions: List[str] = [".pdf", ".docx", ".txt", ".doc"]
    max_file_size_mb: int = 50


class FeatureSettings(BaseModel):
    """Feature flags configuration."""

    enable_ocr: bool = True
    enable_batch_processing: bool = True
    enable_export: bool = True
    enable_chat: bool = True
    enable_dashboard_analytics: bool = True


class Settings(BaseSettings):
    """Top-level application settings composed from config.yaml and environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    use_ai_mocks: bool = False
    enable_director_dashboard: bool = True
    database: DatabaseSettings = Field(
        default_factory=lambda: DatabaseSettings(url="sqlite:///./letsgo.db")
    )
    auth: AuthSettings = Field(
        default_factory=lambda: AuthSettings(
            secret_key="your-super-secret-jwt-key-change-this-in-production",
            algorithm="HS256",
            access_token_expire_minutes=30,
        )
    )
    maintenance: MaintenanceSettings = Field(
        default_factory=lambda: MaintenanceSettings(purge_retention_days=30)
    )
    paths: PathsSettings = Field(
        default_factory=lambda: PathsSettings(
            temp_upload_dir="./temp",
            api_url="http://localhost:8001",
            rule_dir="./src/resources",
        )
    )
    models: ModelsSettings
    llm: LLMSettings
    retrieval: RetrievalSettings
    analysis: AnalysisSettings
    habits_framework: HabitsFrameworkSettings = Field(
        default_factory=HabitsFrameworkSettings
    )
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)
    host: str = "127.0.0.1"
    port: int = 8001
    log_level: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """
    Initializes and returns the application settings.

    It loads a base configuration from 'config.yaml' and then overrides
    it with any settings defined in a .env file or environment variables.
    """
    # Construct the path to the config file relative to this file's location
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Initialize settings. pydantic-settings will load from .env and environment
    settings = Settings(**config_data)

    # Manually override the secret key if it was loaded from the environment
    secret_override = getattr(settings, "SECRET_KEY", None)
    if secret_override:
        settings.auth.secret_key = secret_override

    return settings


# Create the single settings instance used across the app
settings = get_settings()

