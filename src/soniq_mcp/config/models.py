"""Typed configuration models for SoniqMCP."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


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

    model_config = {"str_strip_whitespace": True}
