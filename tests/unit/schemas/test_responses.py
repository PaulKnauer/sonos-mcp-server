"""Unit tests for response schemas."""

from __future__ import annotations

from soniq_mcp.domain.models import PlaybackState, Room, Speaker, SystemTopology, TrackInfo
from soniq_mcp.schemas.responses import (
    PlaybackStateResponse,
    RoomListResponse,
    RoomResponse,
    SpeakerResponse,
    SystemTopologyResponse,
    TrackInfoResponse,
)


def make_room(
    name: str = "Living Room",
    uid: str = "RINCON_001",
    ip_address: str = "192.168.1.10",
    is_coordinator: bool = True,
) -> Room:
    return Room(name=name, uid=uid, ip_address=ip_address, is_coordinator=is_coordinator)


class TestRoomResponse:
    def test_from_domain(self) -> None:
        room = make_room()
        resp = RoomResponse.from_domain(room)
        assert resp.name == "Living Room"
        assert resp.uid == "RINCON_001"
        assert resp.ip_address == "192.168.1.10"
        assert resp.is_coordinator is True

    def test_model_dump_is_snake_case(self) -> None:
        resp = RoomResponse.from_domain(make_room())
        d = resp.model_dump()
        assert "is_coordinator" in d
        assert "ip_address" in d


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
