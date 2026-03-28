"""Response schemas for SoniqMCP tool handlers.

All tool handlers return ``.model_dump()`` of these Pydantic models so
the MCP framework receives plain dicts/primitives.

Fields use ``snake_case`` throughout.
"""

from __future__ import annotations

from pydantic import BaseModel

from soniq_mcp.domain.models import PlaybackState, Room, Speaker, SystemTopology, TrackInfo, VolumeState


class RoomResponse(BaseModel):
    """Serialisable representation of a single Sonos room."""

    name: str
    uid: str
    ip_address: str
    is_coordinator: bool

    @classmethod
    def from_domain(cls, room: Room) -> "RoomResponse":
        return cls(
            name=room.name,
            uid=room.uid,
            ip_address=room.ip_address,
            is_coordinator=room.is_coordinator,
        )


class RoomListResponse(BaseModel):
    """Response for the ``list_rooms`` tool."""

    rooms: list[RoomResponse]
    count: int

    @classmethod
    def from_domain(cls, rooms: list[Room]) -> "RoomListResponse":
        return cls(
            rooms=[RoomResponse.from_domain(r) for r in rooms],
            count=len(rooms),
        )


class SpeakerResponse(BaseModel):
    """Serialisable representation of a discovered Sonos speaker/device."""

    name: str
    uid: str
    ip_address: str
    room_name: str
    room_uid: str | None = None
    model_name: str | None = None
    is_visible: bool

    @classmethod
    def from_domain(cls, speaker: Speaker) -> "SpeakerResponse":
        return cls(
            name=speaker.name,
            uid=speaker.uid,
            ip_address=speaker.ip_address,
            room_name=speaker.room_name,
            room_uid=speaker.room_uid,
            model_name=speaker.model_name,
            is_visible=speaker.is_visible,
        )


class SystemTopologyResponse(BaseModel):
    """Response for the ``get_system_topology`` tool."""

    rooms: list[RoomResponse]
    speakers: list[SpeakerResponse]
    coordinator_count: int
    total_count: int
    speaker_count: int

    @classmethod
    def from_domain(cls, topology: SystemTopology) -> "SystemTopologyResponse":
        return cls(
            rooms=[RoomResponse.from_domain(r) for r in topology.rooms],
            speakers=[SpeakerResponse.from_domain(s) for s in topology.speakers],
            coordinator_count=topology.coordinator_count,
            total_count=topology.total_count,
            speaker_count=topology.speaker_count,
        )


class PlaybackStateResponse(BaseModel):
    """Response for playback control and state query tools."""

    transport_state: str
    room_name: str

    @classmethod
    def from_domain(cls, state: PlaybackState) -> "PlaybackStateResponse":
        return cls(
            transport_state=state.transport_state,
            room_name=state.room_name,
        )


class TrackInfoResponse(BaseModel):
    """Response for the ``get_track_info`` tool."""

    room_name: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    duration: str | None = None
    position: str | None = None
    uri: str | None = None
    album_art_uri: str | None = None
    queue_position: int | None = None

    @classmethod
    def from_domain(cls, info: TrackInfo, room_name: str) -> "TrackInfoResponse":
        return cls(
            room_name=room_name,
            title=info.title,
            artist=info.artist,
            album=info.album,
            duration=info.duration,
            position=info.position,
            uri=info.uri,
            album_art_uri=info.album_art_uri,
            queue_position=info.queue_position,
        )


class VolumeStateResponse(BaseModel):
    """Response for volume and mute state tools."""

    room_name: str
    volume: int
    is_muted: bool

    @classmethod
    def from_domain(cls, state: VolumeState) -> "VolumeStateResponse":
        return cls(
            room_name=state.room_name,
            volume=state.volume,
            is_muted=state.is_muted,
        )
