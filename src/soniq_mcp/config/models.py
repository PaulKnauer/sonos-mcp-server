"""Typed configuration models for SoniqMCP.

Story 1.4 extends the base model with safety controls:
- ``max_volume_pct``: hard cap on volume actions (default 80)
- ``tools_disabled``: explicit list of tool names to suppress at startup
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TransportMode(str, Enum):
    STDIO = "stdio"


class ExposurePosture(str, Enum):
    LOCAL = "local"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class SoniqConfig(BaseModel):
    transport: TransportMode = Field(default=TransportMode.STDIO)
    exposure: ExposurePosture = Field(default=ExposurePosture.LOCAL)
    log_level: LogLevel = Field(default=LogLevel.INFO)
    default_room: str | None = Field(default=None)
    config_file: str | None = Field(default=None)

    # Story 1.4: safety controls
    max_volume_pct: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Hard cap on volume actions (0-100). Default: 80.",
    )
    tools_disabled: list[str] = Field(
        default_factory=list,
        description="Tool names to suppress at startup.",
    )

    model_config = {"str_strip_whitespace": True}

    @field_validator("max_volume_pct")
    @classmethod
    def validate_volume_cap(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError(f"max_volume_pct must be 0-100, got {v}")
        return v
