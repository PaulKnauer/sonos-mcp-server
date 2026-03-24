"""Configuration package for SoniqMCP.

Public surface:
  - ``SoniqConfig``        — the validated config model
  - ``load_config()``      — loads and normalises config from env/overrides
  - ``run_preflight()``    — validates config and raises before bad startup
  - ``ConfigValidationError`` — raised on invalid config
"""

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import (
    ExposurePosture,
    LogLevel,
    SoniqConfig,
    TransportMode,
)
from soniq_mcp.config.validation import ConfigValidationError, run_preflight

__all__ = [
    "ConfigValidationError",
    "ExposurePosture",
    "LogLevel",
    "SoniqConfig",
    "TransportMode",
    "load_config",
    "run_preflight",
]
