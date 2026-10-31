"""SoCo snapshot adapter for non-destructive playback capture and restore.

Wraps ``soco.snapshot.Snapshot`` and serializes the captured state to a
plain dict so higher layers can hold it without touching SoCo objects.
Higher layers must not import ``soco`` directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from soniq_mcp.domain.exceptions import SnapshotError

# Snapshot attributes carried across the capture/restore boundary.
_STATE_FIELDS: tuple[str, ...] = (
    "media_uri",
    "is_coordinator",
    "is_playing_queue",
    "is_playing_cloud_queue",
    "volume",
    "mute",
    "bass",
    "treble",
    "loudness",
    "play_mode",
    "cross_fade",
    "playlist_position",
    "track_position",
    "media_metadata",
    "transport_state",
)


@dataclass(frozen=True)
class _QueuedUri:
    """Minimal queue entry accepted by ``Snapshot._restore_queue``."""

    uri: str


class SnapshotAdapter:
    """Capture and restore Sonos playback state by zone IP."""

    def capture(self, ip_address: str, include_queue: bool) -> dict[str, Any]:
        """Capture the current playback state of a zone.

        Args:
            ip_address: LAN IP of the Sonos zone.
            include_queue: True to also capture the queue contents (slow for
                large queues; restored one track at a time).

        Returns:
            Plain dict of captured state. ``queue`` is present (as a list of
            URIs) only when ``include_queue`` is True.

        Raises:
            SnapshotError: If SoCo raises any exception.
        """
        try:
            from soco.snapshot import Snapshot  # noqa: PLC0415

            snap = Snapshot(self._make_device(ip_address), snapshot_queue=include_queue)
            snap.snapshot()
            state: dict[str, Any] = {name: getattr(snap, name) for name in _STATE_FIELDS}
            if include_queue:
                state["queue"] = [
                    self._get_didl_uri(item) for batch in snap.queue or [] for item in batch
                ]
            return state
        except Exception as exc:
            raise SnapshotError(f"Failed to capture snapshot: {exc}") from exc

    def restore(
        self,
        ip_address: str,
        state: dict[str, Any],
        fade: bool,
        restore_volume: bool = True,
    ) -> None:
        """Restore a previously captured playback state.

        A room that was stopped or paused stays stopped or paused; only a
        room that was playing resumes playback.

        Args:
            ip_address: LAN IP of the Sonos zone.
            state: Dict returned by :meth:`capture`.
            fade: True to ramp the volume up from zero instead of jumping.
            restore_volume: False to leave the current volume untouched.

        Raises:
            SnapshotError: If SoCo raises any exception.
        """
        try:
            from soco.snapshot import Snapshot  # noqa: PLC0415

            device = self._make_device(ip_address)
            snap = Snapshot(device, snapshot_queue=False)
            for name in _STATE_FIELDS:
                setattr(snap, name, state.get(name))
            snap.playlist_position = int(state.get("playlist_position") or 0)
            queue = state.get("queue")
            if queue is not None:
                snap.queue = [[_QueuedUri(uri) for uri in queue if uri]]
            if not restore_volume:
                # Re-apply the current level so Snapshot leaves volume as-is.
                snap.volume = device.volume
                fade = False
            snap.restore(fade=fade)
        except Exception as exc:
            raise SnapshotError(f"Failed to restore snapshot: {exc}") from exc

    @staticmethod
    def _get_didl_uri(obj: Any) -> str:
        """Extract a playable URI from a SoCo DIDL object (never ``.uri``)."""
        try:
            return obj.get_uri()
        except (IndexError, AttributeError):
            return ""

    @staticmethod
    def _make_device(ip_address: str) -> Any:
        import soco  # noqa: PLC0415

        return soco.SoCo(ip_address)
