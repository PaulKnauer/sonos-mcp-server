"""Volume adapter facade over the shared SoCo adapter."""

from __future__ import annotations

from soniq_mcp.adapters.soco_adapter import SoCoAdapter


class VolumeAdapter:
    """Compatibility adapter that delegates to ``SoCoAdapter``."""

    def __init__(self, soco_adapter: SoCoAdapter | None = None) -> None:
        self._adapter = soco_adapter or SoCoAdapter()

    def get_volume(self, ip_address: str) -> int:
        """Return the current volume for the zone at ``ip_address``.

        Args:
            ip_address: LAN IP of the Sonos speaker.

        Returns:
            Current volume level (0-100).

        Raises:
            VolumeError: on any SoCo failure.
        """
        return self._adapter.get_volume(ip_address)

    def set_volume(self, ip_address: str, volume: int) -> None:
        """Set the volume for the zone at ``ip_address``.

        Args:
            ip_address: LAN IP of the Sonos speaker.
            volume: Target volume level (0-100).

        Raises:
            VolumeError: on any SoCo failure.
        """
        self._adapter.set_volume(ip_address, volume)

    def get_mute(self, ip_address: str) -> bool:
        """Return the current mute state for the zone at ``ip_address``.

        Args:
            ip_address: LAN IP of the Sonos speaker.

        Returns:
            True if the zone is muted.

        Raises:
            VolumeError: on any SoCo failure.
        """
        return self._adapter.get_mute(ip_address)

    def set_mute(self, ip_address: str, muted: bool) -> None:
        """Set the mute state for the zone at ``ip_address``.

        Args:
            ip_address: LAN IP of the Sonos speaker.
            muted: True to mute, False to unmute.

        Raises:
            VolumeError: on any SoCo failure.
        """
        self._adapter.set_mute(ip_address, muted)
