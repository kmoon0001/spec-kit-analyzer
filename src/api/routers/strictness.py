# Strictness Level API Router
# Adjustable strictness levels without complicating threading/API

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strictness", tags=["strictness"])

# Strictness level models
class StrictnessLevel(BaseModel):
    level_name: str
    accuracy_threshold: float
    confidence_threshold: float
    fact_checking: str
    ensemble_agreement: float
    validation_passes: int
    processing_time_target: str
    use_cached_results: bool
    description: str

class StrictnessRequest(BaseModel):
    level_name: str

class StrictnessResponse(BaseModel):
    current_level: str
    level_config: StrictnessLevel
    performance_metrics: dict
    success: bool

# Available strictness levels
STRICTNESS_LEVELS = {
    "ultra_fast": StrictnessLevel(
        level_name="Ultra-Fast Review",
        accuracy_threshold=0.90,
        confidence_threshold=0.85,
        fact_checking="light",
        ensemble_agreement=0.7,
        validation_passes=3,
        processing_time_target="5-10s",
        use_cached_results=True,
        description="Quick review for preliminary analysis"
    ),
    "balanced": StrictnessLevel(
        level_name="Balanced Review",
        accuracy_threshold=0.92,
        confidence_threshold=0.90,
        fact_checking="standard",
        ensemble_agreement=0.8,
        validation_passes=4,
        processing_time_target="10-15s",
        use_cached_results=True,
        description="Optimal balance of speed and accuracy"
    ),
    "thorough": StrictnessLevel(
        level_name="Thorough Review",
        accuracy_threshold=0.95,
        confidence_threshold=0.93,
        fact_checking="comprehensive",
        ensemble_agreement=0.85,
        validation_passes=5,
        processing_time_target="15-25s",
        use_cached_results=False,
        description="Comprehensive analysis for critical cases"
    ),
    "clinical_grade": StrictnessLevel(
        level_name="Clinical-Grade Review",
        accuracy_threshold=0.99,
        confidence_threshold=0.96,
        fact_checking="maximum",
        ensemble_agreement=0.9,
        validation_passes=6,
        processing_time_target="25-40s",
        use_cached_results=False,
        description="Maximum accuracy for critical clinical decisions"
    )
}

# Current strictness level (default: balanced)
current_strictness_level = "balanced"

@router.get("/levels", response_model=dict[str, StrictnessLevel])
async def get_available_levels():
    """Get all available strictness levels"""
    return STRICTNESS_LEVELS

@router.get("/current", response_model=StrictnessResponse)
async def get_current_level():
    """Get current strictness level configuration"""
    try:
        level_config = STRICTNESS_LEVELS[current_strictness_level]

        # Mock performance metrics (in real implementation, get from database)
        performance_metrics = {
            "accuracy_rate": 0.92,
            "processing_time_avg": 12.5,
            "success_rate": 0.95,
            "cache_hit_rate": 0.85
        }

        return StrictnessResponse(
            current_level=current_strictness_level,
            level_config=level_config,
            performance_metrics=performance_metrics,
            success=True
        )

    except Exception as e:
        logger.error(f"Error getting current strictness level: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current strictness level") from e

@router.post("/set", response_model=StrictnessResponse)
async def set_strictness_level(request: StrictnessRequest):
    """Set strictness level"""
    global current_strictness_level

    try:
        if request.level_name not in STRICTNESS_LEVELS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strictness level. Available levels: {list(STRICTNESS_LEVELS.keys())}"
            )

        # Update current level
        current_strictness_level = request.level_name
        level_config = STRICTNESS_LEVELS[current_strictness_level]

        # Log the change
        logger.info(f"Strictness level changed to: {current_strictness_level}")

        # Mock performance metrics
        performance_metrics = {
            "accuracy_rate": level_config.accuracy_threshold,
            "processing_time_avg": float(level_config.processing_time_target.split('-')[0]),
            "success_rate": 0.95,
            "cache_hit_rate": 0.85 if level_config.use_cached_results else 0.0
        }

        return StrictnessResponse(
            current_level=current_strictness_level,
            level_config=level_config,
            performance_metrics=performance_metrics,
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting strictness level: {e}")
        raise HTTPException(status_code=500, detail="Failed to set strictness level") from e

@router.get("/performance", response_model=dict)
async def get_performance_metrics():
    """Get performance metrics for all strictness levels"""
    try:
        # Mock performance data (in real implementation, get from database)
        performance_data = {
            "ultra_fast": {
                "accuracy_rate": 0.90,
                "processing_time_avg": 7.5,
                "success_rate": 0.92,
                "cache_hit_rate": 0.90
            },
            "balanced": {
                "accuracy_rate": 0.92,
                "processing_time_avg": 12.5,
                "success_rate": 0.95,
                "cache_hit_rate": 0.85
            },
            "thorough": {
                "accuracy_rate": 0.95,
                "processing_time_avg": 20.0,
                "success_rate": 0.97,
                "cache_hit_rate": 0.70
            },
            "clinical_grade": {
                "accuracy_rate": 0.99,
                "processing_time_avg": 32.5,
                "success_rate": 0.98,
                "cache_hit_rate": 0.60
            }
        }

        return performance_data

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics") from e

@router.get("/recommendation", response_model=dict)
async def get_recommended_level():
    """Get recommended strictness level based on performance data"""
    try:
        # Mock recommendation logic (in real implementation, use actual performance data)
        recommendation = {
            "recommended_level": "balanced",
            "reason": "Optimal balance of accuracy and performance",
            "accuracy_boost": 0.02,
            "performance_impact": "minimal"
        }

        return recommendation

    except Exception as e:
        logger.error(f"Error getting recommendation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendation") from e

# Helper function to get current strictness configuration
def get_current_strictness_config() -> StrictnessLevel:
    """Get current strictness level configuration for use in other modules"""
    return STRICTNESS_LEVELS[current_strictness_level]

# Helper function to check if strictness level supports feature
def supports_feature(feature: str) -> bool:
    """Check if current strictness level supports a specific feature"""
    config = get_current_strictness_config()

    feature_support = {
        "cached_results": config.use_cached_results,
        "comprehensive_fact_checking": config.fact_checking in ["comprehensive", "maximum"],
        "maximum_fact_checking": config.fact_checking == "maximum",
        "high_ensemble_agreement": config.ensemble_agreement >= 0.85,
        "multiple_validation_passes": config.validation_passes >= 5
    }

    return feature_support.get(feature, False)
