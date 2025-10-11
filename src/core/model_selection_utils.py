import logging
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

from src.config import Settings

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]

def _system_memory_gb() -> float:
    try:
        return psutil.virtual_memory().total / (1024**3)
    except Exception:
        # Fallback to a conservative default when system inspection fails
        return 16.0

def _find_best_profile(profiles: dict, mem_gb: float) -> tuple[str, dict] | None:
    best_fit = None
    for name, profile in profiles.items():
        if not (profile.get("repo") and profile.get("filename")):
            continue
        min_gb, max_gb = profile.get("min_system_gb"), profile.get("max_system_gb")
        if (min_gb and mem_gb < float(min_gb)) or (max_gb and mem_gb > float(max_gb)):
            continue
        if best_fit is None or (profile.get("min_system_gb") or 0.0) >= (best_fit[1].get("min_system_gb") or 0.0):
            best_fit = (name, profile)
    return best_fit

def select_generator_profile(models_cfg: dict) -> tuple[str, str, str | None]:
    profiles = models_cfg.get("generator_profiles") or {}
    if isinstance(profiles, dict) and profiles:
        mem_gb = _system_memory_gb()
        name, profile = _find_best_profile(profiles, mem_gb) or next(iter(profiles.items()), (None, None))
        if profile:
            logger.info("Selected generator profile %s (system memory {mem_gb} GB)", name)
            return profile.get("repo", ""), profile.get("filename", ""), profile.get("revision")
    return (
        models_cfg.get("generator", ""),
        models_cfg.get("generator_filename", ""),
        models_cfg.get("generator_revision"))

def resolve_local_model_path(settings: Settings) -> str | None:
    path_str = getattr(settings.models, "generator_local_path", None)
    if not path_str:
        return None

    candidate = Path(path_str)
    path = candidate if candidate.is_absolute() else (ROOT_DIR / path_str).resolve()
    if path.exists():
        return str(path)

    logger.warning("Configured generator_local_path does not exist: %s", path)
    return None
