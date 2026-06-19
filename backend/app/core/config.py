import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "realestate_shorts"

    # JWT
    JWT_SECRET: str = "dev_secret_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gemini
    GEMINI_API_KEY: str = ""

    # File paths
    DOWNLOADS_DIR: str = "downloads"
    OUTPUTS_DIR: str = "outputs"

    # Reel quality v2 feature flags (safe rollout)
    PIPELINE_SHADOW_MODE: bool = False
    ENABLE_STABILITY_V2: bool = False
    ENABLE_TRIM_V2: bool = False
    ENABLE_STORY_V2: bool = False
    ENABLE_SCORING_V2: bool = False
    ENABLE_DEDUP_V2: bool = False
    ENABLE_TRANSITION_V2: bool = False

    # Reel quality v2 thresholds
    V2_MIN_TRIM_CONFIDENCE: float = 0.6
    V2_MIN_STORY_CONFIDENCE: float = 0.55

    # Reel quality v2 scoring weights
    V2_STABILITY_WEIGHT: float = 0.15
    V2_CINEMATIC_WEIGHT: float = 0.15
    V2_STORY_WEIGHT: float = 0.1
    V2_ROOM_UNIQUENESS_WEIGHT: float = 0.05
    V2_TRANSITION_WEIGHT: float = 0.05

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
