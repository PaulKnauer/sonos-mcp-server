"""Unit tests for SoCoAdapter grouping operations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import GroupError

ROOM_IP = "192.168.1.10"
COORDINATOR_IP = "192.168.1.20"


class TestJoinGroup:
    def test_calls_zone_join_with_coordinator_zone(self):
        room_zone = MagicMock()
        coordinator_zone = MagicMock()

        def make_zone(ip):
            return room_zone if ip == ROOM_IP else coordinator_zone

        with patch("soco.SoCo", side_effect=make_zone):
            SoCoAdapter().join_group(ROOM_IP, COORDINATOR_IP)

        room_zone.join.assert_called_once_with(coordinator_zone)

    def test_soco_error_raises_group_error(self):
        room_zone = MagicMock()
        room_zone.join.side_effect = RuntimeError("network error")
        coordinator_zone = MagicMock()

        def make_zone(ip):
            return room_zone if ip == ROOM_IP else coordinator_zone

        with patch("soco.SoCo", side_effect=make_zone):
            with pytest.raises(GroupError, match="Failed to join group"):
                SoCoAdapter().join_group(ROOM_IP, COORDINATOR_IP)

    def test_zone_construction_error_raises_group_error(self):
        with patch("soco.SoCo", side_effect=RuntimeError("unreachable")):
            with pytest.raises(GroupError, match="Failed to join group"):
                SoCoAdapter().join_group(ROOM_IP, COORDINATOR_IP)


class TestUnjoinRoom:
    def test_calls_zone_unjoin(self):
        zone = MagicMock()

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().unjoin_room(ROOM_IP)

        zone.unjoin.assert_called_once_with()

    def test_soco_error_raises_group_error(self):
        zone = MagicMock()
        zone.unjoin.side_effect = RuntimeError("speaker offline")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(GroupError, match="Failed to unjoin room"):
                SoCoAdapter().unjoin_room(ROOM_IP)


class TestPartyMode:
    def test_calls_zone_partymode(self):
        zone = MagicMock()

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().party_mode(ROOM_IP)

        zone.partymode.assert_called_once_with()

    def test_soco_error_raises_group_error(self):
        zone = MagicMock()
        zone.partymode.side_effect = RuntimeError("device error")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(GroupError, match="Failed to activate party mode"):
                SoCoAdapter().party_mode(ROOM_IP)
