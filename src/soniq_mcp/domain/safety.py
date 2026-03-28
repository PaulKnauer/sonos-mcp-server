"""Domain safety rule evaluation for SoniqMCP.

Rules are transport-agnostic and reusable by all tool handlers
introduced in later stories.  No Sonos SDK calls are made here.
"""

from __future__ import annotations

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import ToolNotPermitted, VolumeCapExceeded


def check_volume(requested: int, config: SoniqConfig) -> int:
    """Validate and return a safe volume level.

    Clamps are NOT applied silently — a ``VolumeCapExceeded`` error is
    raised so the caller (and the AI agent) is aware of the limit.

    Args:
        requested: Target volume (0-100).
        config: Active server configuration.

    Returns:
        The requested volume if within the configured cap.

    Raises:
        VolumeCapExceeded: if ``requested`` > ``config.max_volume_pct``.
        ValueError: if ``requested`` is outside the 0-100 range.
    """
    if not (0 <= requested <= 100):
        raise ValueError(f"Volume must be 0-100, got {requested}")
    if requested > config.max_volume_pct:
        raise VolumeCapExceeded(requested, config.max_volume_pct)
    return requested


def is_tool_permitted(tool_name: str, config: SoniqConfig) -> bool:
    """Return True if the named tool is allowed under the current config.

    Args:
        tool_name: The MCP tool name to check.
        config: Active server configuration.
    """
    return tool_name not in config.tools_disabled


def assert_tool_permitted(tool_name: str, config: SoniqConfig) -> None:
    """Raise ``ToolNotPermitted`` if the tool is disabled.

    Args:
        tool_name: The MCP tool name to check.
        config: Active server configuration.

    Raises:
        ToolNotPermitted: if the tool appears in ``config.tools_disabled``.
    """
    if not is_tool_permitted(tool_name, config):
        raise ToolNotPermitted(tool_name)


def validate_exposure_posture(config: SoniqConfig) -> list[str]:
    """Validate the exposure posture and return any warnings.

    Returns a list of human-readable warning strings (empty = OK).
    ``local`` and ``home-network`` are both supported; any other value
    triggers an unsupported-posture warning.
    """
    warnings: list[str] = []
    from soniq_mcp.config.models import ExposurePosture

    loopback_hosts = {"127.0.0.1", "localhost", "::1"}

    if config.exposure == ExposurePosture.HOME_NETWORK:
        warnings.append(
            f"home-network exposure: server will bind to {config.http_host}:{config.http_port} — "
            "ensure this host is reachable only from your trusted home network."
        )
    elif config.exposure == ExposurePosture.LOCAL and config.http_host not in loopback_hosts:
        warnings.append(
            f"local exposure with non-loopback bind {config.http_host}:{config.http_port} is unsafe; "
            "use a loopback host or switch to home-network exposure."
        )
    elif config.exposure != ExposurePosture.LOCAL:
        warnings.append(
            f"exposure '{config.exposure.value}' is not yet fully supported; "
            "defaulting to local-only behaviour."
        )
    return warnings
