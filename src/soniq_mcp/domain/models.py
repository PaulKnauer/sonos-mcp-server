"""Domain models for SoniqMCP.

Lightweight dataclasses representing core Sonos domain concepts.
These are transport-agnostic and shared across service and tool layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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
    supports_line_in: bool = field(default=False)
    supports_tv: bool = field(default=False)


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
    ) -> SystemTopology:
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


@dataclass(frozen=True)
class QueueItem:
    """A single item in a Sonos zone's playback queue.

    Attributes:
        position: 1-based position in the queue.
        uri: Content URI for the queue item.
        title: Track title, or None if not available.
        artist: Artist name, or None if not available.
        album: Album name, or None if not available.
        album_art_uri: Album art URI, or None if not available.
    """

    position: int
    uri: str
    title: str | None = field(default=None)
    artist: str | None = field(default=None)
    album: str | None = field(default=None)
    album_art_uri: str | None = field(default=None)


@dataclass(frozen=True)
class VolumeState:
    """Current volume and mute state for a single Sonos room.

    Attributes:
        room_name: Human-readable room name.
        volume: Current volume level (0-100).
        is_muted: True if the zone is currently muted.
    """

    room_name: str
    volume: int
    is_muted: bool


@dataclass(frozen=True)
class Favourite:
    """A saved Sonos favourite item.

    Attributes:
        title: Human-readable title of the favourite.
        uri: Content URI used to play the favourite.
        meta: DIDL-Lite XML string used when calling play_uri. Optional.
    """

    title: str
    uri: str
    meta: str | None = field(default=None)


@dataclass(frozen=True)
class SonosPlaylist:
    """A saved Sonos playlist.

    Attributes:
        title: Human-readable title of the playlist.
        uri: Content URI used to add the playlist to a queue.
        item_id: Optional playlist item identifier.
    """

    title: str
    uri: str
    item_id: str | None = field(default=None)


@dataclass(frozen=True)
class SleepTimerState:
    """Current sleep timer state for a Sonos zone.

    Attributes:
        room_name: Human-readable name of the room.
        active: True if a sleep timer is currently active.
        remaining_seconds: Seconds remaining, or None if inactive.
        remaining_minutes: Minutes remaining (floored), or None if inactive.
    """

    room_name: str
    active: bool
    remaining_seconds: int | None = field(default=None)
    remaining_minutes: int | None = field(default=None)


@dataclass(frozen=True)
class PlayModeState:
    """Current play mode settings for a Sonos zone.

    Attributes:
        room_name: Human-readable name of the room.
        shuffle: True if shuffle mode is active.
        repeat: Repeat mode — "none", "all", or "one".
        cross_fade: True if crossfade between tracks is enabled.
    """

    room_name: str
    shuffle: bool
    repeat: Literal["none", "all", "one"]
    cross_fade: bool


@dataclass(frozen=True)
class AudioSettingsState:
    """Current audio EQ settings for a single Sonos room.

    Attributes:
        room_name: Human-readable room name.
        bass: Bass level (-10 to 10).
        treble: Treble level (-10 to 10).
        loudness: True if loudness compensation is enabled.
    """

    room_name: str
    bass: int
    treble: int
    loudness: bool


@dataclass(frozen=True)
class InputState:
    """Current external-input state for a single Sonos room."""

    room_name: str
    input_source: Literal["line_in", "tv"]
    coordinator_room_name: str | None = field(default=None)


@dataclass(frozen=True)
class GroupAudioState:
    """Current group-level volume and mute state for an active Sonos group.

    Attributes:
        room_name: The requested target room name.
        coordinator_room_name: The active group coordinator room name.
        member_room_names: All room names in the group (including coordinator).
        volume: Current group volume level (0-100).
        is_muted: True if the group is currently muted.
    """

    room_name: str
    coordinator_room_name: str
    member_room_names: tuple[str, ...]
    volume: int
    is_muted: bool
