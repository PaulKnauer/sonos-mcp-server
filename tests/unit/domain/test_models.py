"""Unit tests for domain models."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.models import PlaybackState, Room, Speaker, SystemTopology, TrackInfo, VolumeState


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


class TestRoom:
    def test_room_fields(self) -> None:
        room = make_room()
        assert room.name == "Living Room"
        assert room.uid == "RINCON_001"
        assert room.ip_address == "192.168.1.10"
        assert room.is_coordinator is True
        assert room.group_coordinator_uid is None

    def test_room_with_group_coordinator_uid(self) -> None:
        room = make_room(is_coordinator=False, group_coordinator_uid="RINCON_000")
        assert room.is_coordinator is False
        assert room.group_coordinator_uid == "RINCON_000"

    def test_room_is_frozen(self) -> None:
        room = make_room()
        with pytest.raises(Exception):
            room.name = "Kitchen"  # type: ignore[misc]

    def test_room_equality(self) -> None:
        r1 = make_room(uid="RINCON_001")
        r2 = make_room(uid="RINCON_001")
        assert r1 == r2

    def test_room_inequality_different_uid(self) -> None:
        r1 = make_room(uid="RINCON_001")
        r2 = make_room(uid="RINCON_002")
        assert r1 != r2


class TestSpeaker:
    def test_speaker_fields(self) -> None:
        speaker = Speaker(
            name="Living Room",
            uid="RINCON_001",
            ip_address="192.168.1.10",
            room_name="Living Room",
            room_uid="RINCON_001",
            model_name="Sonos One",
            is_visible=True,
        )
        assert speaker.room_name == "Living Room"
        assert speaker.model_name == "Sonos One"
        assert speaker.is_visible is True


class TestSystemTopology:
    def test_from_rooms_empty(self) -> None:
        topo = SystemTopology.from_rooms([])
        assert topo.total_count == 0
        assert topo.coordinator_count == 0
        assert topo.speaker_count == 0
        assert topo.rooms == ()
        assert topo.speakers == ()

    def test_from_rooms_single_coordinator(self) -> None:
        room = make_room(is_coordinator=True)
        topo = SystemTopology.from_rooms([room])
        assert topo.total_count == 1
        assert topo.coordinator_count == 1
        assert topo.speaker_count == 1
        assert room in topo.rooms

    def test_from_rooms_mixed(self) -> None:
        coord = make_room(name="Living Room", uid="RINCON_001", is_coordinator=True)
        member = make_room(
            name="Kitchen",
            uid="RINCON_002",
            is_coordinator=False,
            group_coordinator_uid="RINCON_001",
        )
        topo = SystemTopology.from_rooms([coord, member])
        assert topo.total_count == 2
        assert topo.coordinator_count == 1
        assert topo.speaker_count == 2

    def test_from_rooms_uses_explicit_speakers(self) -> None:
        room = make_room()
        speaker = Speaker(
            name="Living Room",
            uid="RINCON_SPK_001",
            ip_address="192.168.1.20",
            room_name="Living Room",
            room_uid="RINCON_001",
            model_name="Sonos One",
            is_visible=False,
        )
        topo = SystemTopology.from_rooms([room], speakers=[speaker])
        assert topo.speaker_count == 1
        assert topo.speakers[0].uid == "RINCON_SPK_001"

    def test_topology_is_frozen(self) -> None:
        topo = SystemTopology.from_rooms([])
        with pytest.raises(Exception):
            topo.total_count = 99  # type: ignore[misc]


class TestPlaybackState:
    def test_fields(self) -> None:
        state = PlaybackState(transport_state="PLAYING", room_name="Living Room")
        assert state.transport_state == "PLAYING"
        assert state.room_name == "Living Room"

    def test_is_frozen(self) -> None:
        state = PlaybackState(transport_state="STOPPED", room_name="Kitchen")
        with pytest.raises(Exception):
            state.transport_state = "PLAYING"  # type: ignore[misc]

    def test_equality(self) -> None:
        s1 = PlaybackState(transport_state="PLAYING", room_name="Living Room")
        s2 = PlaybackState(transport_state="PLAYING", room_name="Living Room")
        assert s1 == s2


class TestTrackInfo:
    def test_all_none_fields(self) -> None:
        info = TrackInfo()
        assert info.title is None
        assert info.artist is None
        assert info.album is None
        assert info.duration is None
        assert info.position is None
        assert info.uri is None
        assert info.album_art_uri is None
        assert info.queue_position is None

    def test_with_values(self) -> None:
        info = TrackInfo(
            title="Song Title",
            artist="Artist Name",
            album="Album Name",
            duration="0:03:45",
            position="0:01:23",
            uri="x-sonos-http://track.mp3",
            album_art_uri="http://example.com/art.jpg",
            queue_position=3,
        )
        assert info.title == "Song Title"
        assert info.artist == "Artist Name"
        assert info.duration == "0:03:45"
        assert info.queue_position == 3

    def test_is_frozen(self) -> None:
        info = TrackInfo(title="Test")
        with pytest.raises(Exception):
            info.title = "Other"  # type: ignore[misc]


class TestVolumeState:
    def test_fields(self) -> None:
        state = VolumeState(room_name="Living Room", volume=50, is_muted=False)
        assert state.room_name == "Living Room"
        assert state.volume == 50
        assert state.is_muted is False

    def test_muted_state(self) -> None:
        state = VolumeState(room_name="Kitchen", volume=0, is_muted=True)
        assert state.is_muted is True
        assert state.volume == 0

    def test_is_frozen(self) -> None:
        state = VolumeState(room_name="Living Room", volume=50, is_muted=False)
        with pytest.raises(Exception):
            state.volume = 99  # type: ignore[misc]

    def test_equality(self) -> None:
        s1 = VolumeState(room_name="Living Room", volume=40, is_muted=False)
        s2 = VolumeState(room_name="Living Room", volume=40, is_muted=False)
        assert s1 == s2

    def test_inequality(self) -> None:
        s1 = VolumeState(room_name="Living Room", volume=40, is_muted=False)
        s2 = VolumeState(room_name="Living Room", volume=60, is_muted=False)
        assert s1 != s2
