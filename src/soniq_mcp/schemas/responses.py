"""Response schemas for SoniqMCP tool handlers.

All tool handlers return ``.model_dump()`` of these Pydantic models so
the MCP framework receives plain dicts/primitives.

Fields use ``snake_case`` throughout.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from soniq_mcp.domain.models import (
    AlarmRecord,
    AudioSettingsState,
    Favourite,
    GroupAudioState,
    InputState,
    PlaybackState,
    PlayModeState,
    QueueItem,
    Room,
    SleepTimerState,
    SonosPlaylist,
    Speaker,
    SystemTopology,
    TrackInfo,
    VolumeState,
)


class RoomResponse(BaseModel):
    """Serialisable representation of a single Sonos room."""

    name: str
    uid: str
    ip_address: str
    is_coordinator: bool
    group_coordinator_uid: str | None = None

    @classmethod
    def from_domain(cls, room: Room) -> RoomResponse:
        return cls(
            name=room.name,
            uid=room.uid,
            ip_address=room.ip_address,
            is_coordinator=room.is_coordinator,
            group_coordinator_uid=room.group_coordinator_uid,
        )


class RoomListResponse(BaseModel):
    """Response for the ``list_rooms`` tool."""

    rooms: list[RoomResponse]
    count: int

    @classmethod
    def from_domain(cls, rooms: list[Room]) -> RoomListResponse:
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
    supports_line_in: bool
    supports_tv: bool

    @classmethod
    def from_domain(cls, speaker: Speaker) -> SpeakerResponse:
        return cls(
            name=speaker.name,
            uid=speaker.uid,
            ip_address=speaker.ip_address,
            room_name=speaker.room_name,
            room_uid=speaker.room_uid,
            model_name=speaker.model_name,
            is_visible=speaker.is_visible,
            supports_line_in=speaker.supports_line_in,
            supports_tv=speaker.supports_tv,
        )


class SystemTopologyResponse(BaseModel):
    """Response for the ``get_system_topology`` tool."""

    rooms: list[RoomResponse]
    speakers: list[SpeakerResponse]
    coordinator_count: int
    total_count: int
    speaker_count: int

    @classmethod
    def from_domain(cls, topology: SystemTopology) -> SystemTopologyResponse:
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
    def from_domain(cls, state: PlaybackState) -> PlaybackStateResponse:
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
    def from_domain(cls, info: TrackInfo, room_name: str) -> TrackInfoResponse:
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
    def from_domain(cls, state: VolumeState) -> VolumeStateResponse:
        return cls(
            room_name=state.room_name,
            volume=state.volume,
            is_muted=state.is_muted,
        )


class FavouriteResponse(BaseModel):
    """Serialisable representation of a single Sonos favourite."""

    title: str
    uri: str

    @classmethod
    def from_domain(cls, fav: Favourite) -> FavouriteResponse:
        return cls(title=fav.title, uri=fav.uri)


class FavouritesListResponse(BaseModel):
    """Response for the ``list_favourites`` tool."""

    items: list[FavouriteResponse]
    count: int

    @classmethod
    def from_domain(cls, items: list[Favourite]) -> FavouritesListResponse:
        return cls(items=[FavouriteResponse.from_domain(f) for f in items], count=len(items))


class PlaylistResponse(BaseModel):
    """Serialisable representation of a single Sonos playlist."""

    title: str
    uri: str
    item_id: str | None = None

    @classmethod
    def from_domain(cls, pl: SonosPlaylist) -> PlaylistResponse:
        return cls(title=pl.title, uri=pl.uri, item_id=pl.item_id)


class PlaylistsListResponse(BaseModel):
    """Response for the ``list_playlists`` tool."""

    items: list[PlaylistResponse]
    count: int

    @classmethod
    def from_domain(cls, items: list[SonosPlaylist]) -> PlaylistsListResponse:
        return cls(items=[PlaylistResponse.from_domain(p) for p in items], count=len(items))


class PlaylistDeleteResponse(BaseModel):
    """Response for the ``delete_playlist`` tool."""

    playlist_id: str
    status: str


class QueueItemResponse(BaseModel):
    """Serialisable representation of a single Sonos queue item."""

    position: int
    uri: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_art_uri: str | None = None

    @classmethod
    def from_domain(cls, item: QueueItem) -> QueueItemResponse:
        return cls(
            position=item.position,
            uri=item.uri,
            title=item.title,
            artist=item.artist,
            album=item.album,
            album_art_uri=item.album_art_uri,
        )


class QueueResponse(BaseModel):
    """Response for the ``get_queue`` tool."""

    room: str
    items: list[QueueItemResponse]
    count: int

    @classmethod
    def from_domain(cls, room_name: str, items: list[QueueItem]) -> QueueResponse:
        return cls(
            room=room_name,
            items=[QueueItemResponse.from_domain(item) for item in items],
            count=len(items),
        )


class GroupResponse(BaseModel):
    """A single Sonos group with its coordinator and member room names."""

    coordinator: str
    members: list[str]


class SleepTimerResponse(BaseModel):
    """Response for sleep timer get and set tools."""

    room_name: str
    active: bool
    remaining_seconds: int | None = None
    remaining_minutes: int | None = None

    @classmethod
    def from_domain(cls, state: SleepTimerState) -> SleepTimerResponse:
        return cls(
            room_name=state.room_name,
            active=state.active,
            remaining_seconds=state.remaining_seconds,
            remaining_minutes=state.remaining_minutes,
        )


class PlayModeResponse(BaseModel):
    """Response for play mode get and set tools."""

    room_name: str
    shuffle: bool
    repeat: Literal["none", "all", "one"]
    cross_fade: bool

    @classmethod
    def from_domain(cls, state: PlayModeState) -> PlayModeResponse:
        return cls(
            room_name=state.room_name,
            shuffle=state.shuffle,
            repeat=state.repeat,
            cross_fade=state.cross_fade,
        )


class AudioSettingsResponse(BaseModel):
    """Response for audio EQ get and set tools."""

    room_name: str
    bass: int
    treble: int
    loudness: bool

    @classmethod
    def from_domain(cls, state: AudioSettingsState) -> AudioSettingsResponse:
        return cls(
            room_name=state.room_name,
            bass=state.bass,
            treble=state.treble,
            loudness=state.loudness,
        )


class InputStateResponse(BaseModel):
    """Response for input-switching tools."""

    room_name: str
    input_source: Literal["line_in", "tv"]
    coordinator_room_name: str | None = None

    @classmethod
    def from_domain(cls, state: InputState) -> InputStateResponse:
        return cls(
            room_name=state.room_name,
            input_source=state.input_source,
            coordinator_room_name=state.coordinator_room_name,
        )


class GroupAudioStateResponse(BaseModel):
    """Response for group-level volume and mute tools."""

    room_name: str
    coordinator_room_name: str
    member_room_names: list[str]
    volume: int
    is_muted: bool

    @classmethod
    def from_domain(cls, state: GroupAudioState) -> GroupAudioStateResponse:
        return cls(
            room_name=state.room_name,
            coordinator_room_name=state.coordinator_room_name,
            member_room_names=list(state.member_room_names),
            volume=state.volume,
            is_muted=state.is_muted,
        )


class AlarmResponse(BaseModel):
    """Serialisable representation of a single Sonos alarm."""

    alarm_id: str
    room_name: str
    start_time: str
    recurrence: str
    enabled: bool
    volume: int | None = None
    include_linked_zones: bool

    @classmethod
    def from_domain(cls, record: AlarmRecord) -> AlarmResponse:
        return cls(
            alarm_id=record.alarm_id,
            room_name=record.room_name,
            start_time=record.start_time,
            recurrence=record.recurrence,
            enabled=record.enabled,
            volume=record.volume,
            include_linked_zones=record.include_linked_zones,
        )


class AlarmsListResponse(BaseModel):
    """Response for the ``list_alarms`` tool."""

    alarms: list[AlarmResponse]
    count: int

    @classmethod
    def from_domain(cls, records: list[AlarmRecord]) -> AlarmsListResponse:
        return cls(
            alarms=[AlarmResponse.from_domain(r) for r in records],
            count=len(records),
        )


class AlarmDeleteResponse(BaseModel):
    """Response for the ``delete_alarm`` tool."""

    alarm_id: str
    status: str


class GroupTopologyResponse(BaseModel):
    """Current grouping state of the Sonos household."""

    groups: list[GroupResponse]
    total_groups: int
    total_rooms: int

    @classmethod
    def from_rooms(cls, rooms: list[Room]) -> GroupTopologyResponse:
        """Derive group topology from Room domain objects.

        Uses Room.is_coordinator and Room.group_coordinator_uid to
        reconstruct which rooms belong to which group.
        """
        uid_to_name: dict[str, str] = {r.uid: r.name for r in rooms}
        groups_map: dict[str, list[str]] = {}  # coordinator_uid -> member names

        for room in rooms:
            if room.is_coordinator:
                # Coordinator is always the first member of its own group
                groups_map.setdefault(room.uid, []).insert(0, room.name)
            else:
                coord_uid = room.group_coordinator_uid or room.uid
                groups_map.setdefault(coord_uid, []).append(room.name)

        groups = [
            GroupResponse(
                coordinator=uid_to_name.get(coord_uid, coord_uid),
                members=members,
            )
            for coord_uid, members in groups_map.items()
        ]
        return cls(groups=groups, total_groups=len(groups), total_rooms=len(rooms))
