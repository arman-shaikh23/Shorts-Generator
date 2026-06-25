import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache

class Settings(BaseSettings):
    # Service metadata
    SERVICE_NAME: str = "reelforge-backend"
    SERVICE_ENV: str = "development"
    SERVICE_VERSION: str = "17.16.0"

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
    # Optional Azure Blob offload for final rendered reels
    ENABLE_AZURE_BLOB_OUTPUT: bool = False
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_BLOB_OUTPUT_CONTAINER: str = "reels"
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

    # Structured logging
    ENABLE_STRUCTLOG: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"
    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: str = "logs/reelforge_debug.log"

    # Better Stack log shipping (optional)
    ENABLE_BETTER_STACK: bool = False
    BETTER_STACK_SOURCE_TOKEN: str = ""

    # Rate limiting
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 180
    RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE: int = 30
    RATE_LIMIT_GENERATION_REQUESTS_PER_MINUTE: int = 20
    RATE_LIMIT_EXCLUDE_PATHS: str = (
        "/api/v1/health,/favicon.ico,/favicon.svg,/openapi.json,/docs,/redoc,/assets,/outputs,/data"
    )
    RATE_LIMIT_TRUST_PROXY: bool = False
    RATE_LIMIT_MAX_KEYS: int = 10000

    # Startup and worker resilience
    STARTUP_RETRY_ATTEMPTS: int = 5
    STARTUP_RETRY_BASE_DELAY_SEC: int = 2
    STARTUP_RETRY_MAX_DELAY_SEC: int = 15

    # Alerts (webhook, optional)
    ENABLE_ALERTS: bool = False
    ALERT_WEBHOOK_URL: str = ""
    ALERT_COOLDOWN_SEC: int = 300
    ALERT_HTTP_TIMEOUT_SEC: float = 5.0
    ALERT_MIN_CONSECUTIVE_BACKGROUND_FAILURES: int = 2

    # OpenTelemetry (optional)
    ENABLE_OTEL: bool = False
    OTEL_SERVICE_NAME: str = "reelforge-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_OTLP_HEADERS: str = ""
    OTEL_EXPORTER_TIMEOUT_SEC: float = 5.0
    OTEL_ENABLE_CONSOLE_EXPORTER: bool = False
    OTEL_INSTRUMENT_FASTAPI: bool = True
    OTEL_INSTRUMENT_HTTPX: bool = True
    OTEL_INSTRUMENT_PYMONGO: bool = True
    OTEL_INSTRUMENT_LOGGING: bool = True

    # Prometheus metrics
    ENABLE_PROMETHEUS_METRICS: bool = True
    PROMETHEUS_METRICS_PATH: str = "/metrics"

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

    @field_validator(
        "ENABLE_REDIS_CACHE",
        "ENABLE_STRUCTLOG",
        "LOG_TO_FILE",
        "ENABLE_BETTER_STACK",
        "ENABLE_RATE_LIMITING",
        "RATE_LIMIT_TRUST_PROXY",
        "ENABLE_ALERTS",
        "ENABLE_OTEL",
        "OTEL_ENABLE_CONSOLE_EXPORTER",
        "OTEL_INSTRUMENT_FASTAPI",
        "OTEL_INSTRUMENT_HTTPX",
        "OTEL_INSTRUMENT_PYMONGO",
        "OTEL_INSTRUMENT_LOGGING",
        "ENABLE_PROMETHEUS_METRICS",
        "PIPELINE_SHADOW_MODE",
        "ENABLE_STABILITY_V2",
        "ENABLE_TRIM_V2",
        "ENABLE_STORY_V2",
        "ENABLE_SCORING_V2",
        "ENABLE_DEDUP_V2",
        "ENABLE_TRANSITION_V2",
        "ENABLE_AZURE_BLOB_OUTPUT",
        mode="before",
    )
    @classmethod
    def _coerce_boolish(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "ture", "1", "yes", "y", "on"}:
                return True
            if normalized in {"false", "flase", "0", "no", "n", "off"}:
                return False
        return value

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
