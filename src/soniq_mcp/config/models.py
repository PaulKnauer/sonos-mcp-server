"""Typed configuration models for SoniqMCP.

Scoped to single-household Sonos use.  Multi-tenant and multi-household
concerns are explicitly out of scope.  Later stories add HTTP transport
and expanded exposure posture values.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TransportMode(str, Enum):
    """Supported server transport modes."""
    STDIO = "stdio"


class ExposurePosture(str, Enum):
    """Allowed network exposure postures.

    Story 1.4 will extend this with additional values.
    """
    LOCAL = "local"


class LogLevel(str, Enum):
    """Standard Python log levels accepted by the server."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class SoniqConfig(BaseModel):
    """Validated runtime configuration for SoniqMCP.

    All fields have safe defaults so an empty environment still starts
    correctly.  Optional fields are None when not provided.
    """

    transport: TransportMode = Field(
        default=TransportMode.STDIO,
        description="Server transport mode.",
    )
    exposure: ExposurePosture = Field(
        default=ExposurePosture.LOCAL,
        description="Network exposure posture.",
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Application log level.",
    )
    default_room: str | None = Field(
        default=None,
        description="Optional default Sonos room name.",
    )
    config_file: str | None = Field(
        default=None,
        description="Optional path to an external configuration file.",
    )

    model_config = {"str_strip_whitespace": True, "extra": "forbid"}
