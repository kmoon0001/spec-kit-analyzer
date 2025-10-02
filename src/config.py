from functools import lru_cache
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class PathsSettings(BaseModel):
    temp_upload_dir: str
    api_url: str
    rule_dir: str
    medical_dictionary: str = "src/resources/medical_dictionary.txt"


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
    general: str
    biomedical: str


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
    phi_scrubber: Optional[PhiScrubberModelSettings] = None


class LLMSettings(BaseModel):
    model_type: str
    context_length: int
    generation_params: Dict[str, Any]


class RetrievalSettings(BaseModel):
    similarity_top_k: int
    dense_model_name: str
    rrf_k: int


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
        0.7,
        description="Minimum confidence score for a finding to be considered valid.",
    )
    deterministic_focus: str = Field(
        "- Treatment frequency documented\n- Goals reviewed or adjusted\n- Medical necessity justified",
        description="Default focus points for compliance analysis.",
    )


class Settings(BaseModel):

    enable_director_dashboard: bool = False
    database: DatabaseSettings
    auth: AuthSettings
    maintenance: MaintenanceSettings
    paths: PathsSettings
    llm: LLMSettings
    retrieval: RetrievalSettings
    analysis: AnalysisSettings
    models: ModelsSettings
    habits_framework: HabitsFrameworkSettings = HabitsFrameworkSettings()
    use_ai_mocks: bool = False

    # This field will be populated from the SECRET_KEY in the .env file
    SECRET_KEY: Optional[str] = None


@lru_cache()
def get_settings() -> Settings:
    """
    Initializes and returns the application settings.

    It loads a base configuration from 'config.yaml' and then overrides
    it with any settings defined in a .env file or environment variables.
    """
    with open("config.yaml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Initialize settings. pydantic-settings will load from .env and environment
    settings = Settings(**config_data)

    # Manually override the secret key if it was loaded from the environment
    if settings.SECRET_KEY:
        settings.auth.secret_key = settings.SECRET_KEY

    return settings