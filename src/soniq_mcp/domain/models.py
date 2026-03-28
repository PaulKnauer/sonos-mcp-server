"""Domain models for SoniqMCP.

Lightweight dataclasses representing core Sonos domain concepts.
These are transport-agnostic and shared across service and tool layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Room:
    """A single addressable Sonos zone/room.

    Attributes:
        name: Human-readable room name (e.g. "Living Room").
        uid: Unique zone identifier (e.g. "RINCON_...").
        ip_address: LAN IP address of the speaker.
        is_coordinator: True if this zone is a group coordinator.
        group_coordinator_uid: UID of the group coordinator, or None if
            this zone is not part of a group or is itself the coordinator.
    """

    name: str
    uid: str
    ip_address: str
    is_coordinator: bool
    group_coordinator_uid: str | None = field(default=None)


@dataclass(frozen=True)
class Speaker:
    """A single Sonos speaker/device in the household topology."""

    name: str
    uid: str
    ip_address: str
    room_name: str
    room_uid: str | None = field(default=None)
    model_name: str | None = field(default=None)
    is_visible: bool = field(default=True)


@dataclass(frozen=True)
class SystemTopology:
    """Snapshot of the full Sonos household topology.

    Attributes:
        rooms: All discovered rooms/zones.
        speakers: All discovered speakers/devices in the household.
        coordinator_count: Number of group coordinators found.
        total_count: Total number of zones found.
        speaker_count: Total number of speakers found.
    """

    rooms: tuple[Room, ...]
    speakers: tuple[Speaker, ...]
    coordinator_count: int
    total_count: int
    speaker_count: int

    @classmethod
    def from_rooms(
        cls,
        rooms: list[Room],
        speakers: list[Speaker] | None = None,
    ) -> "SystemTopology":
        """Build a topology snapshot from discovered rooms and speakers."""
        derived_speakers = speakers
        if derived_speakers is None:
            derived_speakers = [
                Speaker(
                    name=room.name,
                    uid=room.uid,
                    ip_address=room.ip_address,
                    room_name=room.name,
                    room_uid=room.uid,
                    is_visible=True,
                )
                for room in rooms
            ]
        return cls(
            rooms=tuple(rooms),
            speakers=tuple(derived_speakers),
            coordinator_count=sum(1 for r in rooms if r.is_coordinator),
            total_count=len(rooms),
            speaker_count=len(derived_speakers),
        )


@dataclass(frozen=True)
class PlaybackState:
    """Current transport state of a Sonos zone.

    Attributes:
        transport_state: SoCo transport state string —
            "PLAYING", "PAUSED_PLAYBACK", "STOPPED", or "TRANSITIONING".
        room_name: Human-readable name of the room.
    """

    transport_state: str
    room_name: str


@dataclass(frozen=True)
class TrackInfo:
    """Currently playing track details for a Sonos zone.

    All fields are optional — Sonos returns empty strings for many fields
    when nothing is playing or streaming radio is active.
    """

    title: str | None = field(default=None)
    artist: str | None = field(default=None)
    album: str | None = field(default=None)
    duration: str | None = field(default=None)
    position: str | None = field(default=None)
    uri: str | None = field(default=None)
    album_art_uri: str | None = field(default=None)
    queue_position: int | None = field(default=None)
