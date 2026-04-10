"""Unit tests for DiscoveryAdapter — no real Sonos hardware required.

Uses fake zone objects to simulate SoCo responses, testing the adapter
in isolation via constructor injection patterns.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.discovery_adapter import DiscoveryAdapter
from soniq_mcp.domain.exceptions import SonosDiscoveryError
from soniq_mcp.domain.models import Room, Speaker


def make_fake_zone(
    player_name: str = "Living Room",
    uid: str = "RINCON_001",
    ip_address: str = "192.168.1.10",
    is_coordinator: bool = True,
    coordinator_uid: str | None = None,
) -> MagicMock:
    """Build a fake SoCo zone object with the attributes DiscoveryAdapter reads."""
    zone = MagicMock()
    zone.player_name = player_name
    zone.uid = uid
    zone.ip_address = ip_address
    zone.is_coordinator = is_coordinator

    group = MagicMock()
    if coordinator_uid:
        coord = MagicMock()
        coord.uid = coordinator_uid
        group.coordinator = coord
    else:
        coord = MagicMock()
        coord.uid = uid  # zone is its own coordinator
        group.coordinator = coord
    zone.group = group

    return zone


class TestDiscoveryAdapterZoneToRoom:
    def test_coordinator_zone(self) -> None:
        zone = make_fake_zone(is_coordinator=True)
        room = DiscoveryAdapter._zone_to_room(zone)
        assert isinstance(room, Room)
        assert room.name == "Living Room"
        assert room.uid == "RINCON_001"
        assert room.ip_address == "192.168.1.10"
        assert room.is_coordinator is True
        assert room.group_coordinator_uid is None

    def test_member_zone_sets_coordinator_uid(self) -> None:
        zone = make_fake_zone(
            player_name="Kitchen",
            uid="RINCON_002",
            is_coordinator=False,
            coordinator_uid="RINCON_001",
        )
        room = DiscoveryAdapter._zone_to_room(zone)
        assert room.is_coordinator is False
        assert room.group_coordinator_uid == "RINCON_001"

    def test_zone_without_group(self) -> None:
        zone = make_fake_zone()
        zone.group = None
        room = DiscoveryAdapter._zone_to_room(zone)
        assert room.group_coordinator_uid is None

    def test_zone_missing_uid_raises_discovery_error(self) -> None:
        zone = make_fake_zone()
        zone.uid = None
        with pytest.raises(SonosDiscoveryError, match="missing required uid"):
            DiscoveryAdapter._zone_to_room(zone)


class TestDiscoveryAdapterZoneToSpeaker:
    def test_maps_zone_to_speaker(self) -> None:
        zone = make_fake_zone()
        zone.is_visible = True
        zone.get_speaker_info.return_value = {
            "zone_name": "Living Room",
            "model_name": "Sonos One",
        }

        speaker = DiscoveryAdapter._zone_to_speaker(zone)

        assert isinstance(speaker, Speaker)
        assert speaker.room_name == "Living Room"
        assert speaker.model_name == "Sonos One"
        assert speaker.room_uid == "RINCON_001"
        assert speaker.supports_line_in is False
        assert speaker.supports_tv is False

    def test_infers_input_capabilities_from_model_name(self) -> None:
        zone = make_fake_zone()
        zone.is_visible = True
        zone.get_speaker_info.return_value = {
            "zone_name": "Living Room",
            "model_name": "Sonos Amp",
        }

        speaker = DiscoveryAdapter._zone_to_speaker(zone)

        assert speaker.supports_line_in is True
        assert speaker.supports_tv is True

    def test_speaker_info_falls_back_to_zone_name(self) -> None:
        zone = make_fake_zone()
        zone.is_visible = False
        zone.get_speaker_info.side_effect = RuntimeError("boom")

        speaker = DiscoveryAdapter._zone_to_speaker(zone)

        assert speaker.room_name == "Living Room"
        assert speaker.room_uid is None
        assert speaker.is_visible is False
        assert speaker.supports_line_in is False
        assert speaker.supports_tv is False


class TestDiscoveryAdapterDiscoverRooms:
    def test_returns_empty_list_when_no_zones(self) -> None:
        adapter = DiscoveryAdapter()
        with patch("soco.discover", return_value=None):
            rooms = adapter.discover_rooms(timeout=1.0)
        assert rooms == []

    def test_returns_empty_set_from_soco(self) -> None:
        adapter = DiscoveryAdapter()
        with patch("soco.discover", return_value=set()):
            rooms = adapter.discover_rooms(timeout=1.0)
        assert rooms == []

    def test_maps_single_zone_to_room(self) -> None:
        adapter = DiscoveryAdapter()
        zone = make_fake_zone()
        with patch("soco.discover", return_value={zone}):
            rooms = adapter.discover_rooms(timeout=1.0)
        assert len(rooms) == 1
        assert rooms[0].name == "Living Room"

    def test_maps_multiple_zones(self) -> None:
        adapter = DiscoveryAdapter()
        zones = {
            make_fake_zone("Living Room", "RINCON_001"),
            make_fake_zone("Kitchen", "RINCON_002"),
        }
        with patch("soco.discover", return_value=zones):
            rooms = adapter.discover_rooms(timeout=1.0)
        assert len(rooms) == 2
        names = {r.name for r in rooms}
        assert names == {"Living Room", "Kitchen"}

    def test_raises_discovery_error_on_soco_exception(self) -> None:
        adapter = DiscoveryAdapter()
        with patch("soco.discover", side_effect=OSError("network unreachable")):
            with pytest.raises(SonosDiscoveryError, match="Sonos discovery failed"):
                adapter.discover_rooms(timeout=1.0)

    def test_discovery_error_passthrough(self) -> None:
        """A SonosDiscoveryError raised inside should propagate unchanged."""
        adapter = DiscoveryAdapter()
        original = SonosDiscoveryError("already a domain error")
        with patch("soco.discover", side_effect=original):
            with pytest.raises(SonosDiscoveryError, match="already a domain error"):
                adapter.discover_rooms(timeout=1.0)


class TestDiscoveryAdapterDiscoverSpeakers:
    def test_returns_empty_list_when_no_zones(self) -> None:
        adapter = DiscoveryAdapter()
        with patch("soco.discover", return_value=None):
            speakers = adapter.discover_speakers(timeout=1.0)
        assert speakers == []

    def test_uses_household_all_zones_for_speakers(self) -> None:
        adapter = DiscoveryAdapter()
        visible_zone = make_fake_zone("Living Room", "RINCON_001")
        visible_zone.is_visible = True
        visible_zone.get_speaker_info.return_value = {
            "zone_name": "Living Room",
            "model_name": "Sonos One",
        }
        hidden_zone = make_fake_zone("Living Room LS", "RINCON_002")
        hidden_zone.is_visible = False
        hidden_zone.get_speaker_info.return_value = {
            "zone_name": "Living Room",
            "model_name": "Sonos One SL",
        }
        visible_zone.all_zones = {visible_zone, hidden_zone}

        with patch("soco.discover", return_value={visible_zone}):
            speakers = adapter.discover_speakers(timeout=1.0)

        assert len(speakers) == 2
        assert {speaker.uid for speaker in speakers} == {"RINCON_001", "RINCON_002"}
