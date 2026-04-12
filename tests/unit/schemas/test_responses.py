"""Unit tests for response schemas."""

from __future__ import annotations

from soniq_mcp.domain.models import (
    AlarmRecord,
    AudioSettingsState,
    GroupAudioState,
    InputState,
    LibraryItem,
    PlaybackState,
    Room,
    SleepTimerState,
    Speaker,
    SystemTopology,
    TrackInfo,
    VolumeState,
)
from soniq_mcp.schemas.responses import (
    AlarmDeleteResponse,
    AlarmResponse,
    AlarmsListResponse,
    AudioSettingsResponse,
    GroupAudioStateResponse,
    InputStateResponse,
    LibraryBrowseResponse,
    LibraryItemResponse,
    LibraryPlaybackResponse,
    PlaybackStateResponse,
    RoomListResponse,
    RoomResponse,
    SleepTimerResponse,
    SpeakerResponse,
    SystemTopologyResponse,
    TrackInfoResponse,
    VolumeStateResponse,
)


def make_room(
    name: str = "Living Room",
    uid: str = "RINCON_001",
    ip_address: str = "192.168.1.10",
    is_coordinator: bool = True,
    group_coordinator_uid: str | None = None,
) -> Room:
    return Room(
        name=name,
        uid=uid,
        ip_address=ip_address,
        is_coordinator=is_coordinator,
        group_coordinator_uid=group_coordinator_uid,
    )


class TestRoomResponse:
    def test_from_domain(self) -> None:
        room = make_room()
        resp = RoomResponse.from_domain(room)
        assert resp.name == "Living Room"
        assert resp.uid == "RINCON_001"
        assert resp.ip_address == "192.168.1.10"
        assert resp.is_coordinator is True
        assert resp.group_coordinator_uid is None

    def test_from_domain_with_group_coordinator_uid(self) -> None:
        room = make_room(
            name="Kitchen",
            uid="RINCON_002",
            is_coordinator=False,
            group_coordinator_uid="RINCON_001",
        )
        resp = RoomResponse.from_domain(room)
        assert resp.group_coordinator_uid == "RINCON_001"
        assert resp.is_coordinator is False

    def test_model_dump_is_snake_case(self) -> None:
        resp = RoomResponse.from_domain(make_room())
        d = resp.model_dump()
        assert "is_coordinator" in d
        assert "ip_address" in d
        assert "group_coordinator_uid" in d

    def test_model_dump_group_coordinator_uid_none_for_coordinator(self) -> None:
        d = RoomResponse.from_domain(make_room(is_coordinator=True)).model_dump()
        assert d["group_coordinator_uid"] is None

    def test_model_dump_group_coordinator_uid_present_for_member(self) -> None:
        room = make_room(is_coordinator=False, group_coordinator_uid="RINCON_001")
        d = RoomResponse.from_domain(room).model_dump()
        assert d["group_coordinator_uid"] == "RINCON_001"


class TestRoomListResponse:
    def test_empty(self) -> None:
        resp = RoomListResponse.from_domain([])
        assert resp.count == 0
        assert resp.rooms == []

    def test_from_domain_sets_count(self) -> None:
        rooms = [make_room("R1", "UID1"), make_room("R2", "UID2")]
        resp = RoomListResponse.from_domain(rooms)
        assert resp.count == 2
        assert len(resp.rooms) == 2

    def test_model_dump_serialisable(self) -> None:
        resp = RoomListResponse.from_domain([make_room()])
        d = resp.model_dump()
        assert isinstance(d, dict)
        assert d["count"] == 1
        assert isinstance(d["rooms"], list)
        assert d["rooms"][0]["name"] == "Living Room"


class TestSpeakerResponse:
    def test_from_domain(self) -> None:
        speaker = Speaker(
            name="Living Room",
            uid="RINCON_001",
            ip_address="192.168.1.10",
            room_name="Living Room",
            room_uid="RINCON_001",
            model_name="Sonos One",
            is_visible=True,
        )
        resp = SpeakerResponse.from_domain(speaker)
        assert resp.room_name == "Living Room"
        assert resp.model_name == "Sonos One"
        assert resp.is_visible is True
        assert resp.supports_line_in is False
        assert resp.supports_tv is False


class TestLibraryResponses:
    def test_library_item_response_from_domain(self) -> None:
        item = LibraryItem(
            title="Album",
            item_type="object.container.album.musicAlbum",
            item_id="A:ALBUM/1",
            uri=None,
            album_art_uri="/getaa?s=1",
            is_browsable=True,
            is_playable=False,
        )

        resp = LibraryItemResponse.from_domain(item)

        assert resp.title == "Album"
        assert resp.item_type == "object.container.album.musicAlbum"
        assert resp.item_id == "A:ALBUM/1"
        assert resp.is_browsable is True
        assert resp.is_playable is False

    def test_library_browse_response_from_domain(self) -> None:
        item = LibraryItem(
            title="Artist",
            item_type="object.container.person.musicArtist",
            item_id="A:ARTIST/1",
            uri=None,
            album_art_uri=None,
            is_browsable=True,
            is_playable=False,
        )

        resp = LibraryBrowseResponse.from_domain(
            category="artists",
            parent_id=None,
            items=[item],
            start=0,
            limit=25,
            has_more=True,
        )

        dump = resp.model_dump()
        assert dump["category"] == "artists"
        assert dump["count"] == 1
        assert dump["start"] == 0
        assert dump["limit"] == 25
        assert dump["has_more"] is True
        assert dump["next_start"] == 25
        assert dump["items"][0]["title"] == "Artist"

    def test_library_browse_response_advances_by_requested_limit_on_empty_page(self) -> None:
        resp = LibraryBrowseResponse.from_domain(
            category="artists",
            parent_id="A:ARTIST/1",
            items=[],
            start=100,
            limit=100,
            has_more=True,
        )

        dump = resp.model_dump()
        assert dump["count"] == 0
        assert dump["next_start"] == 200

    def test_library_playback_response_from_domain(self) -> None:
        resp = LibraryPlaybackResponse.from_domain(
            room="Living Room",
            title="Track",
            uri="x-file-cifs://track.mp3",
            item_id="A:TRACKS/1",
        )

        assert resp.model_dump() == {
            "status": "ok",
            "room": "Living Room",
            "title": "Track",
            "item_id": "A:TRACKS/1",
            "uri": "x-file-cifs://track.mp3",
        }


class TestSystemTopologyResponse:
    def test_from_empty_topology(self) -> None:
        topo = SystemTopology.from_rooms([])
        resp = SystemTopologyResponse.from_domain(topo)
        assert resp.total_count == 0
        assert resp.coordinator_count == 0
        assert resp.speaker_count == 0
        assert resp.rooms == []
        assert resp.speakers == []

    def test_from_topology_with_rooms(self) -> None:
        rooms = [
            make_room("Living Room", "RINCON_001", is_coordinator=True),
            make_room("Kitchen", "RINCON_002", is_coordinator=False),
        ]
        topo = SystemTopology.from_rooms(rooms)
        resp = SystemTopologyResponse.from_domain(topo)
        assert resp.total_count == 2
        assert resp.coordinator_count == 1
        assert resp.speaker_count == 2
        assert len(resp.rooms) == 2

    def test_model_dump_serialisable(self) -> None:
        topo = SystemTopology.from_rooms([make_room()])
        resp = SystemTopologyResponse.from_domain(topo)
        d = resp.model_dump()
        assert isinstance(d, dict)
        assert "total_count" in d
        assert "coordinator_count" in d
        assert "rooms" in d
        assert "speakers" in d
        assert "speaker_count" in d


class TestPlaybackStateResponse:
    def test_from_domain(self) -> None:
        state = PlaybackState(transport_state="PLAYING", room_name="Living Room")
        resp = PlaybackStateResponse.from_domain(state)
        assert resp.transport_state == "PLAYING"
        assert resp.room_name == "Living Room"

    def test_model_dump_snake_case(self) -> None:
        state = PlaybackState(transport_state="STOPPED", room_name="Kitchen")
        d = PlaybackStateResponse.from_domain(state).model_dump()
        assert "transport_state" in d
        assert "room_name" in d


class TestTrackInfoResponse:
    def test_from_domain_with_values(self) -> None:
        info = TrackInfo(
            title="Song",
            artist="Artist",
            album="Album",
            duration="0:03:45",
            position="0:01:00",
            uri="x-sonos-http://track.mp3",
            album_art_uri="http://example.com/art.jpg",
            queue_position=2,
        )
        resp = TrackInfoResponse.from_domain(info, room_name="Living Room")
        assert resp.title == "Song"
        assert resp.artist == "Artist"
        assert resp.room_name == "Living Room"
        assert resp.queue_position == 2

    def test_from_domain_all_none(self) -> None:
        info = TrackInfo()
        resp = TrackInfoResponse.from_domain(info, room_name="Kitchen")
        assert resp.title is None
        assert resp.artist is None
        assert resp.queue_position is None

    def test_model_dump_serialisable(self) -> None:
        info = TrackInfo(title="Test")
        d = TrackInfoResponse.from_domain(info, "Living Room").model_dump()
        assert isinstance(d, dict)
        assert "title" in d
        assert "room_name" in d


class TestSleepTimerResponse:
    def test_from_domain_active_timer(self) -> None:
        state = SleepTimerState(
            room_name="Living Room",
            active=True,
            remaining_seconds=1800,
            remaining_minutes=30,
        )
        resp = SleepTimerResponse.from_domain(state)
        assert resp.room_name == "Living Room"
        assert resp.active is True
        assert resp.remaining_seconds == 1800
        assert resp.remaining_minutes == 30

    def test_from_domain_inactive_timer(self) -> None:
        state = SleepTimerState(
            room_name="Kitchen",
            active=False,
            remaining_seconds=None,
            remaining_minutes=None,
        )
        resp = SleepTimerResponse.from_domain(state)
        assert resp.room_name == "Kitchen"
        assert resp.active is False
        assert resp.remaining_seconds is None
        assert resp.remaining_minutes is None

    def test_model_dump_snake_case(self) -> None:
        state = SleepTimerState(
            room_name="Office",
            active=True,
            remaining_seconds=600,
            remaining_minutes=10,
        )
        d = SleepTimerResponse.from_domain(state).model_dump()
        assert "room_name" in d
        assert "active" in d
        assert "remaining_seconds" in d
        assert "remaining_minutes" in d

    def test_model_dump_serialisable_inactive(self) -> None:
        state = SleepTimerState(room_name="Bedroom", active=False)
        d = SleepTimerResponse.from_domain(state).model_dump()
        assert d["active"] is False
        assert d["remaining_seconds"] is None
        assert d["remaining_minutes"] is None


class TestAudioSettingsResponse:
    def test_from_domain(self) -> None:
        state = AudioSettingsState(room_name="Living Room", bass=5, treble=-3, loudness=True)
        resp = AudioSettingsResponse.from_domain(state)
        assert resp.room_name == "Living Room"
        assert resp.bass == 5
        assert resp.treble == -3
        assert resp.loudness is True

    def test_from_domain_zero_values(self) -> None:
        state = AudioSettingsState(room_name="Kitchen", bass=0, treble=0, loudness=False)
        resp = AudioSettingsResponse.from_domain(state)
        assert resp.bass == 0
        assert resp.treble == 0
        assert resp.loudness is False

    def test_model_dump_snake_case(self) -> None:
        state = AudioSettingsState(room_name="Office", bass=-2, treble=4, loudness=True)
        d = AudioSettingsResponse.from_domain(state).model_dump()
        assert "room_name" in d
        assert "bass" in d
        assert "treble" in d
        assert "loudness" in d

    def test_model_dump_serialisable(self) -> None:
        state = AudioSettingsState(room_name="Bedroom", bass=10, treble=-10, loudness=False)
        d = AudioSettingsResponse.from_domain(state).model_dump()
        assert isinstance(d, dict)
        assert d["bass"] == 10
        assert d["treble"] == -10
        assert d["loudness"] is False


class TestInputStateResponse:
    def test_from_domain(self) -> None:
        state = InputState(
            room_name="Living Room",
            input_source="tv",
            coordinator_room_name="Living Room",
        )
        resp = InputStateResponse.from_domain(state)
        assert resp.room_name == "Living Room"
        assert resp.input_source == "tv"
        assert resp.coordinator_room_name == "Living Room"

    def test_model_dump_snake_case(self) -> None:
        state = InputState(
            room_name="Kitchen",
            input_source="line_in",
            coordinator_room_name=None,
        )
        d = InputStateResponse.from_domain(state).model_dump()
        assert "room_name" in d
        assert "input_source" in d
        assert "coordinator_room_name" in d


class TestVolumeStateResponse:
    def test_from_domain(self) -> None:
        state = VolumeState(room_name="Living Room", volume=55, is_muted=False)
        resp = VolumeStateResponse.from_domain(state)
        assert resp.room_name == "Living Room"
        assert resp.volume == 55
        assert resp.is_muted is False

    def test_from_domain_muted(self) -> None:
        state = VolumeState(room_name="Kitchen", volume=0, is_muted=True)
        resp = VolumeStateResponse.from_domain(state)
        assert resp.is_muted is True
        assert resp.volume == 0

    def test_model_dump_serialisable(self) -> None:
        state = VolumeState(room_name="Office", volume=30, is_muted=False)
        d = VolumeStateResponse.from_domain(state).model_dump()
        assert isinstance(d, dict)
        assert d["room_name"] == "Office"
        assert d["volume"] == 30
        assert d["is_muted"] is False


class TestGroupAudioStateResponse:
    def _make_state(
        self,
        room_name: str = "Living Room",
        coordinator: str = "Living Room",
        members: tuple = ("Living Room", "Kitchen"),
        volume: int = 35,
        is_muted: bool = False,
    ) -> GroupAudioState:
        return GroupAudioState(
            room_name=room_name,
            coordinator_room_name=coordinator,
            member_room_names=members,
            volume=volume,
            is_muted=is_muted,
        )

    def test_from_domain(self) -> None:
        state = self._make_state()
        resp = GroupAudioStateResponse.from_domain(state)
        assert resp.room_name == "Living Room"
        assert resp.coordinator_room_name == "Living Room"
        assert resp.member_room_names == ["Living Room", "Kitchen"]
        assert resp.volume == 35
        assert resp.is_muted is False

    def test_from_domain_muted(self) -> None:
        state = self._make_state(is_muted=True, volume=0)
        resp = GroupAudioStateResponse.from_domain(state)
        assert resp.is_muted is True
        assert resp.volume == 0

    def test_model_dump_snake_case(self) -> None:
        d = GroupAudioStateResponse.from_domain(self._make_state()).model_dump()
        assert "room_name" in d
        assert "coordinator_room_name" in d
        assert "member_room_names" in d
        assert "volume" in d
        assert "is_muted" in d

    def test_model_dump_member_room_names_is_list(self) -> None:
        d = GroupAudioStateResponse.from_domain(self._make_state()).model_dump()
        assert isinstance(d["member_room_names"], list)
        assert "Living Room" in d["member_room_names"]
        assert "Kitchen" in d["member_room_names"]

    def test_from_domain_single_member_tuple_converts_to_list(self) -> None:
        state = self._make_state(members=("Living Room",))
        d = GroupAudioStateResponse.from_domain(state).model_dump()
        assert isinstance(d["member_room_names"], list)


def make_alarm_record(
    alarm_id: str = "101",
    room_name: str = "Living Room",
    start_time: str = "07:00:00",
    recurrence: str = "DAILY",
    enabled: bool = True,
    volume: int | None = 30,
    include_linked_zones: bool = False,
) -> AlarmRecord:
    return AlarmRecord(
        alarm_id=alarm_id,
        room_name=room_name,
        start_time=start_time,
        recurrence=recurrence,
        enabled=enabled,
        volume=volume,
        include_linked_zones=include_linked_zones,
    )


class TestAlarmResponse:
    def test_from_domain(self) -> None:
        record = make_alarm_record()
        resp = AlarmResponse.from_domain(record)
        assert resp.alarm_id == "101"
        assert resp.room_name == "Living Room"
        assert resp.start_time == "07:00:00"
        assert resp.recurrence == "DAILY"
        assert resp.enabled is True
        assert resp.volume == 30
        assert resp.include_linked_zones is False

    def test_from_domain_no_volume(self) -> None:
        record = make_alarm_record(volume=None)
        resp = AlarmResponse.from_domain(record)
        assert resp.volume is None

    def test_from_domain_disabled_with_linked_zones(self) -> None:
        record = make_alarm_record(enabled=False, include_linked_zones=True)
        resp = AlarmResponse.from_domain(record)
        assert resp.enabled is False
        assert resp.include_linked_zones is True

    def test_model_dump_is_snake_case(self) -> None:
        d = AlarmResponse.from_domain(make_alarm_record()).model_dump()
        assert "alarm_id" in d
        assert "room_name" in d
        assert "start_time" in d
        assert "recurrence" in d
        assert "enabled" in d
        assert "volume" in d
        assert "include_linked_zones" in d

    def test_model_dump_serialisable(self) -> None:
        d = AlarmResponse.from_domain(make_alarm_record()).model_dump()
        assert isinstance(d, dict)
        assert d["alarm_id"] == "101"


class TestAlarmsListResponse:
    def test_empty(self) -> None:
        resp = AlarmsListResponse.from_domain([])
        assert resp.alarms == []
        assert resp.count == 0

    def test_with_single_item(self) -> None:
        resp = AlarmsListResponse.from_domain([make_alarm_record()])
        assert resp.count == 1
        assert resp.alarms[0].alarm_id == "101"

    def test_with_multiple_items(self) -> None:
        records = [
            make_alarm_record(alarm_id="1", room_name="Living Room"),
            make_alarm_record(alarm_id="2", room_name="Bedroom", recurrence="WEEKDAYS"),
        ]
        resp = AlarmsListResponse.from_domain(records)
        assert resp.count == 2
        assert resp.alarms[0].alarm_id == "1"
        assert resp.alarms[1].alarm_id == "2"
        assert resp.alarms[1].recurrence == "WEEKDAYS"

    def test_model_dump_serialisable(self) -> None:
        d = AlarmsListResponse.from_domain([make_alarm_record()]).model_dump()
        assert isinstance(d, dict)
        assert d["count"] == 1
        assert isinstance(d["alarms"], list)


class TestAlarmDeleteResponse:
    def test_fields(self) -> None:
        resp = AlarmDeleteResponse(alarm_id="123", status="deleted")
        assert resp.alarm_id == "123"
        assert resp.status == "deleted"

    def test_model_dump_serialisable(self) -> None:
        d = AlarmDeleteResponse(alarm_id="999", status="deleted").model_dump()
        assert d["alarm_id"] == "999"
        assert d["status"] == "deleted"
