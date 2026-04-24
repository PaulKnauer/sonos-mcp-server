"""Typed configuration models for SoniqMCP.

Scoped to single-household Sonos use. Multi-tenant and multi-household
concerns are explicitly out of scope. Later stories add HTTP transport
and expanded exposure posture values.

Story 1.4 extends the base model with safety controls:
- ``max_volume_pct``: hard cap on volume actions (default 80)
- ``tools_disabled``: explicit list of tool names to suppress at startup
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

KNOWN_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "ping",
        "server_info",
        "list_rooms",
        "get_system_topology",
        "play",
        "pause",
        "stop",
        "next_track",
        "previous_track",
        "get_playback_state",
        "get_track_info",
        "get_volume",
        "set_volume",
        "adjust_volume",
        "mute",
        "unmute",
        "get_mute",
        "list_favourites",
        "play_favourite",
        "list_playlists",
        "play_playlist",
        "create_playlist",
        "update_playlist",
        "delete_playlist",
        "get_queue",
        "add_to_queue",
        "remove_from_queue",
        "clear_queue",
        "play_from_queue",
        "get_group_topology",
        "join_group",
        "unjoin_room",
        "party_mode",
        "get_group_volume",
        "set_group_volume",
        "adjust_group_volume",
        "group_mute",
        "group_unmute",
        "group_rooms",
        "get_play_mode",
        "set_play_mode",
        "seek",
        "get_sleep_timer",
        "set_sleep_timer",
        "get_eq_settings",
        "set_bass",
        "set_treble",
        "set_loudness",
        "switch_to_line_in",
        "switch_to_tv",
        "list_alarms",
        "create_alarm",
        "update_alarm",
        "delete_alarm",
        "browse_library",
        "play_library_item",
    }
)


class AuthMode(StrEnum):
    """Supported authentication modes."""

    NONE = "none"
    STATIC = "static"
    OIDC = "oidc"


class TransportMode(StrEnum):
    """Supported server transport modes."""

    STDIO = "stdio"
    HTTP = "http"


class ExposurePosture(StrEnum):
    """Allowed network exposure postures."""

    LOCAL = "local"
    HOME_NETWORK = "home-network"


class LogLevel(StrEnum):
    """Standard Python log levels accepted by the server."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class SoniqConfig(BaseModel):
    """Validated runtime configuration for SoniqMCP."""

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
    http_host: str = Field(
        default="127.0.0.1",
        description="Bind address for HTTP transport. Use '0.0.0.0' for home-network access.",
    )
    http_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Bind port for HTTP transport (1-65535).",
    )
    auth_mode: AuthMode = Field(
        default=AuthMode.NONE,
        description="Authentication mode: none, static, or oidc.",
    )
    auth_token: SecretStr | None = Field(
        default=None,
        description="Static bearer token for auth_mode=static.",
    )
    oidc_issuer: str | None = Field(
        default=None,
        description="OIDC issuer URL for auth_mode=oidc.",
    )
    oidc_audience: str | None = Field(
        default=None,
        description="OIDC audience for JWT validation.",
    )
    oidc_jwks_uri: str | None = Field(
        default=None,
        description="JWKS URI for OIDC token verification.",
    )
    oidc_ca_bundle: str | None = Field(
        default=None,
        description="Path to CA bundle for OIDC HTTPS connections.",
    )
    oidc_resource_url: str | None = Field(
        default=None,
        description="OIDC resource server URL.",
    )

    model_config = {"str_strip_whitespace": True, "extra": "forbid"}

    @field_validator("max_volume_pct")
    @classmethod
    def validate_volume_cap(cls, value: int) -> int:
        if value < 0 or value > 100:
            raise ValueError(f"max_volume_pct must be 0-100, got {value}")
        return value

    @field_validator("tools_disabled")
    @classmethod
    def validate_tools_disabled(cls, value: list[str]) -> list[str]:
        unknown_tools = [tool_name for tool_name in value if tool_name not in KNOWN_TOOL_NAMES]
        if unknown_tools:
            allowed_tools = ", ".join(sorted(KNOWN_TOOL_NAMES))
            unknown_values = ", ".join(unknown_tools)
            raise ValueError(
                f"tools_disabled contains unknown tool(s): {unknown_values}. "
                f"Allowed values: {allowed_tools}."
            )
        return value

    @model_validator(mode="after")
    def validate_auth_config(self) -> SoniqConfig:
        """Enforce auth mode consistency."""
        if (
            self.auth_mode == AuthMode.OIDC
            and self.transport != TransportMode.STDIO
            and not self.oidc_issuer
        ):
            raise ValueError("auth_mode=oidc requires oidc_issuer to be set.")
        return self

    @model_validator(mode="after")
    def validate_http_exposure_combination(self) -> SoniqConfig:
        """Enforce safe HTTP bind/exposure combinations."""
        if self.transport != TransportMode.HTTP:
            return self

        loopback_hosts = {"127.0.0.1", "localhost", "::1"}

        if self.exposure == ExposurePosture.LOCAL and self.http_host not in loopback_hosts:
            raise ValueError(
                "LOCAL exposure requires a loopback http_host "
                "(127.0.0.1, localhost, or ::1). "
                "Use exposure=home-network for a non-loopback bind."
            )

        if self.exposure == ExposurePosture.HOME_NETWORK and self.http_host in loopback_hosts:
            raise ValueError(
                "HOME_NETWORK exposure requires a non-loopback http_host. "
                "Use http_host=0.0.0.0 or a specific LAN address."
            )

        return self
