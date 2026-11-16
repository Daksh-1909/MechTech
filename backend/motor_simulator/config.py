"""Simulator configuration (Pydantic settings).

All settings are overridable via environment variables or a .env file.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class SimulatorConfig(BaseSettings):
    """Runtime configuration for the motor simulator runner."""

    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="SIM_",
    )

    # Target API
    api_base_url: str = Field(default="http://localhost:8000/api/v1")
    api_key: str | None = Field(default=None, description="X-Device-Key header value if configured.")

    # Simulation parameters
    equipment_id: str = Field(description="UUID of the equipment to simulate readings for.")
    scenario: str = Field(default="normal", description="Scenario key: normal|overheating|bearing_wear|combined|noisy_sensor")
    seed: int = Field(default=42, ge=0)
    interval_seconds: float = Field(default=5.0, gt=0, le=3600)
    max_steps: int | None = Field(default=None, ge=1, description="Stop after N steps (None = run forever).")
    duration_seconds: float | None = Field(default=None, gt=0, description="Stop after N seconds of wall-clock time.")

    # HTTP settings
    request_timeout_seconds: float = Field(default=10.0, gt=0)
    dry_run: bool = Field(default=False, description="Generate readings without sending them to the API.")

