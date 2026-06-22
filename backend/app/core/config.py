import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "realestate_shorts"
    MONGO_MAX_POOL_SIZE: int = 100
    MONGO_MIN_POOL_SIZE: int = 5
    MONGO_MAX_IDLE_TIME_MS: int = 45000
    MONGO_WAIT_QUEUE_TIMEOUT_MS: int = 10000
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 5000

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
    # Streaming upload controls
    UPLOAD_STREAM_CHUNK_SIZE: int = 1048576
    MAX_VIDEO_UPLOAD_BYTES: int = 10737418240
    MAX_MUSIC_UPLOAD_BYTES: int = 104857600
    YTDLP_COOKIES_FILE: str = ""
    YOUTUBE_MAX_DURATION_SEC: int = 0

    # Shared outbound HTTP connection pool
    HTTP_POOL_MAX_CONNECTIONS: int = 100
    HTTP_POOL_MAX_KEEPALIVE_CONNECTIONS: int = 20
    HTTP_CONNECT_TIMEOUT_SEC: float = 10.0
    HTTP_READ_TIMEOUT_SEC: float = 300.0
    HTTP_WRITE_TIMEOUT_SEC: float = 30.0
    HTTP_POOL_TIMEOUT_SEC: float = 30.0

    # Redis cache (feature-flagged)
    ENABLE_REDIS_CACHE: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 100
    REDIS_CONNECT_TIMEOUT_SEC: float = 2.0
    REDIS_READ_TIMEOUT_SEC: float = 2.0
    CACHE_DEFAULT_TTL_SEC: int = 60
    CACHE_TTL_PROJECTS_SEC: int = 60
    CACHE_TTL_PROJECT_DETAIL_SEC: int = 60
    CACHE_TTL_HISTORY_SEC: int = 90
    CACHE_TTL_UPLOADS_SEC: int = 30
    CACHE_TTL_DASHBOARD_STATS_SEC: int = 30
    CACHE_TTL_MUSIC_LIBRARY_SEC: int = 300
    CACHE_VERSION_TTL_SEC: int = 2592000

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
