"""Volume adapter for SoniqMCP.

Encapsulates all SoCo volume and mute operations. This is the ONLY module
that imports ``soco`` for volume/mute. Higher layers (service, tools) must
not import soco directly.
"""

from __future__ import annotations

from soniq_mcp.domain.exceptions import VolumeError


class VolumeAdapter:
    """Thin wrapper around SoCo volume and mute properties.

    All SoCo exceptions are caught and re-raised as ``VolumeError``
    so that SoCo types never leak into service or tool layers.
    """

    def get_volume(self, ip_address: str) -> int:
        """Return the current volume for the zone at ``ip_address``.

        Args:
            ip_address: LAN IP of the Sonos speaker.

        Returns:
            Current volume level (0-100).

        Raises:
            VolumeError: on any SoCo failure.
        """
        try:
            import soco  # noqa: PLC0415

            zone = soco.SoCo(ip_address)
            return zone.volume
        except Exception as exc:
            raise VolumeError(f"Failed to get volume from {ip_address}: {exc}") from exc

    def set_volume(self, ip_address: str, volume: int) -> None:
        """Set the volume for the zone at ``ip_address``.

        Args:
            ip_address: LAN IP of the Sonos speaker.
            volume: Target volume level (0-100).

        Raises:
            VolumeError: on any SoCo failure.
        """
        try:
            import soco  # noqa: PLC0415

            zone = soco.SoCo(ip_address)
            zone.volume = volume
        except Exception as exc:
            raise VolumeError(f"Failed to set volume on {ip_address}: {exc}") from exc

    def get_mute(self, ip_address: str) -> bool:
        """Return the current mute state for the zone at ``ip_address``.

        Args:
            ip_address: LAN IP of the Sonos speaker.

        Returns:
            True if the zone is muted.

        Raises:
            VolumeError: on any SoCo failure.
        """
        try:
            import soco  # noqa: PLC0415

            zone = soco.SoCo(ip_address)
            return zone.mute
        except Exception as exc:
            raise VolumeError(f"Failed to get mute state from {ip_address}: {exc}") from exc

    def set_mute(self, ip_address: str, muted: bool) -> None:
        """Set the mute state for the zone at ``ip_address``.

        Args:
            ip_address: LAN IP of the Sonos speaker.
            muted: True to mute, False to unmute.

        Raises:
            VolumeError: on any SoCo failure.
        """
        try:
            import soco  # noqa: PLC0415

            zone = soco.SoCo(ip_address)
            zone.mute = muted
        except Exception as exc:
            raise VolumeError(f"Failed to set mute on {ip_address}: {exc}") from exc
