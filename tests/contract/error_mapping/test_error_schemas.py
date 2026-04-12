"""Contract tests: error response schemas are well-formed (AC: 3, 4)."""

from __future__ import annotations

from soniq_mcp.domain.exceptions import (
    AudioSettingsValidationError,
    ErrorCategory,
    PlaybackError,
    PlaybackValidationError,
    QueueError,
    SonosDiscoveryError,
)
from soniq_mcp.schemas.errors import ErrorResponse


class TestErrorResponseSchema:
    def test_volume_cap_error_has_required_fields(self) -> None:
        err = ErrorResponse.from_volume_cap(requested=90, cap=80)
        assert err.category == ErrorCategory.VALIDATION
        assert "90" in err.error
        assert "80" in err.error
        assert err.field == "volume"
        assert err.suggestion is not None

    def test_tool_not_permitted_error_names_tool(self) -> None:
        err = ErrorResponse.from_tool_not_permitted("ping")
        assert err.category == ErrorCategory.CONFIGURATION
        assert "ping" in err.error
        assert err.field == "tools_disabled"
        assert err.suggestion is not None

    def test_error_response_serialises_to_dict(self) -> None:
        err = ErrorResponse(error="something went wrong")
        d = err.model_dump()
        assert d["category"] == ErrorCategory.OPERATION
        assert d["error"] == "something went wrong"
        assert d["field"] is None

    def test_error_response_no_internal_paths(self) -> None:
        err = ErrorResponse.from_volume_cap(75, 50)
        assert "/workdir" not in err.error
        assert "/workdir" not in (err.suggestion or "")

    def test_discovery_error_uses_connectivity_category(self) -> None:
        err = ErrorResponse.from_discovery_error(SonosDiscoveryError("network unreachable"))
        assert err.category == ErrorCategory.CONNECTIVITY
        assert err.field == "sonos_network"

    def test_operational_errors_preserve_operation_category(self) -> None:
        err = ErrorResponse.from_queue_error(QueueError("queue is busy"))
        assert err.category == ErrorCategory.OPERATION
        assert err.field == "queue"

    def test_audio_settings_validation_error_uses_validation_category(self) -> None:
        err = ErrorResponse.from_audio_settings_error(
            AudioSettingsValidationError("bass must be in the range -10..10, got 11.")
        )
        assert err.category == ErrorCategory.VALIDATION
        assert err.field == "audio_settings"

    def test_playback_validation_error_uses_validation_category(self) -> None:
        err = ErrorResponse.from_playback_error(
            PlaybackValidationError("Invalid minutes value '5'. Expected a non-negative integer.")
        )
        assert err.category == ErrorCategory.VALIDATION
        assert err.field == "playback"

    def test_error_response_redacts_urls_hosts_and_paths(self) -> None:
        err = ErrorResponse.from_playback_error(
            PlaybackError(
                "Request to http://192.168.1.20:1400/media at /Users/paul/.config/secret.env failed"
            )
        )
        assert "<redacted-url>" in err.error
        assert "<redacted-path>" in err.error
        assert "192.168.1.20" not in err.error
        assert "/Users/paul/.config/secret.env" not in err.error

    def test_alarm_error_uses_operation_category(self) -> None:
        from soniq_mcp.domain.exceptions import AlarmError

        err = ErrorResponse.from_alarm_error(AlarmError("SoCo alarm failed"))
        assert err.category == ErrorCategory.OPERATION
        assert err.field == "alarm"
        assert err.suggestion is not None

    def test_alarm_validation_error_uses_validation_category(self) -> None:
        from soniq_mcp.domain.exceptions import AlarmValidationError

        err = ErrorResponse.from_alarm_error(AlarmValidationError("Invalid recurrence 'MONTHLY'"))
        assert err.category == ErrorCategory.VALIDATION
        assert err.field == "alarm"

    def test_alarm_error_redacts_sensitive_data(self) -> None:
        from soniq_mcp.domain.exceptions import AlarmError

        err = ErrorResponse.from_alarm_error(
            AlarmError("Alarm failed at http://192.168.1.20:1400/alarms")
        )
        assert "192.168.1.20" not in err.error
        assert "<redacted" in err.error

    def test_playlist_error_uses_operation_category(self) -> None:
        from soniq_mcp.domain.exceptions import PlaylistError

        err = ErrorResponse.from_playlist_error(PlaylistError("SoCo playlist failed"))
        assert err.category == ErrorCategory.OPERATION
        assert err.field == "playlist"
        assert err.suggestion is not None

    def test_playlist_validation_error_uses_validation_category(self) -> None:
        from soniq_mcp.domain.exceptions import PlaylistValidationError

        err = ErrorResponse.from_playlist_error(
            PlaylistValidationError("Playlist 'SQ:99' was not found.")
        )
        assert err.category == ErrorCategory.VALIDATION
        assert err.field == "playlist"

    def test_playlist_unsupported_operation_error_uses_operation_category(self) -> None:
        from soniq_mcp.domain.exceptions import PlaylistUnsupportedOperationError

        err = ErrorResponse.from_playlist_error(
            PlaylistUnsupportedOperationError("Rename not supported")
        )
        assert err.category == ErrorCategory.OPERATION
        assert err.field == "playlist"

    def test_playlist_error_redacts_sensitive_data(self) -> None:
        from soniq_mcp.domain.exceptions import PlaylistError

        err = ErrorResponse.from_playlist_error(
            PlaylistError("Playlist failed at http://192.168.1.20:1400/playlists")
        )
        assert "192.168.1.20" not in err.error
        assert "<redacted" in err.error

    def test_library_error_uses_operation_category(self) -> None:
        from soniq_mcp.domain.exceptions import LibraryError

        err = ErrorResponse.from_library_error(LibraryError("SoCo library failed"))
        assert err.category == ErrorCategory.OPERATION
        assert err.field == "library"
        assert err.suggestion is not None

    def test_library_validation_error_uses_validation_category(self) -> None:
        from soniq_mcp.domain.exceptions import LibraryValidationError

        err = ErrorResponse.from_library_error(LibraryValidationError("Invalid category"))
        assert err.category == ErrorCategory.VALIDATION
        assert err.field == "library"

    def test_library_error_redacts_sensitive_data(self) -> None:
        from soniq_mcp.domain.exceptions import LibraryError

        err = ErrorResponse.from_library_error(
            LibraryError("Library failed at http://192.168.1.20:1400/library")
        )
        assert "192.168.1.20" not in err.error
        assert "<redacted" in err.error
