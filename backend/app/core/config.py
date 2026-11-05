from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = PROJECT_ROOT / "backend" / ".env"


def _resolve_sqlite_url(url: str) -> str:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url

    raw_path = url[len(prefix) :]
    if not raw_path or raw_path == ":memory:" or raw_path.startswith("file:"):
        return url

    path = Path(raw_path)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return f"{prefix}{path.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "MechTech API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "testing", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_v1_prefix: str = "/api/v1"

    data_root: Path = PROJECT_ROOT / "data"
    database_url: str = "sqlite:///./data/db/mechtech.db"

    session_cookie_name: str = "mechtech_session"
    csrf_cookie_name: str = "mechtech_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    session_ttl_hours: int = 12
    session_cookie_secure: bool = False
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    simulator_api_key: str | None = None
    device_api_key_header: str = "X-Device-Key"

    readings_batch_max: int = Field(default=100, ge=1, le=1000)
    reading_future_tolerance_seconds: int = Field(default=300, ge=0)
    reading_query_max_limit: int = Field(default=1000, ge=1, le=10000)
    reading_query_max_range_days: int = Field(default=31, ge=1, le=366)
    temperature_min_c: float = -40.0
    temperature_max_c: float = 200.0
    vibration_min: float = -100.0
    vibration_max: float = 100.0

    stale_data_threshold_seconds: int = Field(default=60, ge=1)
    anomaly_temperature_warning_c: float = 75.0
    anomaly_temperature_critical_c: float = 90.0
    anomaly_vibration_warning: float = 0.5
    anomaly_vibration_critical: float = 0.75

    feature_window_size: int = Field(default=12, ge=2, le=1000)
    analysis_window_max: int = Field(default=100, ge=2, le=1000)
    feature_window_seconds: float = Field(default=10.0, gt=0, le=3600)
    feature_stride_seconds: float = Field(default=5.0, gt=0, le=3600)
    feature_sample_interval_seconds: float = Field(default=1.0, gt=0, le=3600)
    feature_min_samples: int = Field(default=8, ge=2, le=1000)
    statistical_baseline_z_threshold: float = Field(default=3.0, gt=0, le=20)

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("simulator_api_key", mode="before")
    @classmethod
    def blank_api_key_is_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("data_root", mode="after")
    @classmethod
    def resolve_data_root(cls, value: Path) -> Path:
        return value if value.is_absolute() else (PROJECT_ROOT / value).resolve()

    @field_validator("database_url", mode="after")
    @classmethod
    def resolve_database_url(cls, value: str) -> str:
        return _resolve_sqlite_url(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
