"""Audio settings service for SoniqMCP.

Handles get/set of bass, treble, and loudness EQ settings for Sonos zones.
All validation occurs here before adapter writes are attempted.
"""

from __future__ import annotations

from soniq_mcp.domain.exceptions import AudioSettingsError
from soniq_mcp.domain.models import AudioSettingsState

_EQ_MIN = -10
_EQ_MAX = 10


class AudioSettingsService:
    """Service for reading and writing Sonos audio EQ settings."""

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def get_audio_settings(self, room_name: str) -> AudioSettingsState:
        """Return the current bass, treble, and loudness for the named room.

        Args:
            room_name: Human-readable Sonos room name.

        Returns:
            ``AudioSettingsState`` with current EQ values.

        Raises:
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
            AudioSettingsError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        return self._adapter.get_audio_settings(room.ip_address, room_name)

    def set_bass(self, room_name: str, level: int) -> AudioSettingsState:
        """Set the bass level for the named room and return the resulting state.

        Args:
            room_name: Human-readable Sonos room name.
            level: Bass level, must be an integer in [-10, 10].

        Returns:
            Updated ``AudioSettingsState`` reflecting authoritative device state.

        Raises:
            AudioSettingsError: If level is out of range or not an integer.
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
        """
        self._validate_eq_level(level, "bass")
        room = self._room_service.get_room(room_name)
        self._adapter.set_bass(room.ip_address, level)
        return self._adapter.get_audio_settings(room.ip_address, room_name)

    def set_treble(self, room_name: str, level: int) -> AudioSettingsState:
        """Set the treble level for the named room and return the resulting state.

        Args:
            room_name: Human-readable Sonos room name.
            level: Treble level, must be an integer in [-10, 10].

        Returns:
            Updated ``AudioSettingsState`` reflecting authoritative device state.

        Raises:
            AudioSettingsError: If level is out of range or not an integer.
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
        """
        self._validate_eq_level(level, "treble")
        room = self._room_service.get_room(room_name)
        self._adapter.set_treble(room.ip_address, level)
        return self._adapter.get_audio_settings(room.ip_address, room_name)

    def set_loudness(self, room_name: str, enabled: bool) -> AudioSettingsState:
        """Set loudness compensation for the named room and return resulting state.

        Args:
            room_name: Human-readable Sonos room name.
            enabled: True to enable loudness, False to disable.

        Returns:
            Updated ``AudioSettingsState`` reflecting authoritative device state.

        Raises:
            AudioSettingsError: If enabled is not a boolean.
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
        """
        if not isinstance(enabled, bool):
            raise AudioSettingsError(
                f"loudness must be a boolean, got {type(enabled).__name__!r}."
            )
        room = self._room_service.get_room(room_name)
        self._adapter.set_loudness(room.ip_address, enabled)
        return self._adapter.get_audio_settings(room.ip_address, room_name)

    @staticmethod
    def _validate_eq_level(level: int, field: str) -> None:
        """Validate that level is an integer in the inclusive range [-10, 10].

        Raises:
            AudioSettingsError: If validation fails.
        """
        if not isinstance(level, int) or isinstance(level, bool):
            raise AudioSettingsError(
                f"{field} must be an integer, got {type(level).__name__!r}."
            )
        if level < _EQ_MIN or level > _EQ_MAX:
            raise AudioSettingsError(
                f"{field} must be in the range {_EQ_MIN}..{_EQ_MAX}, got {level}."
            )
