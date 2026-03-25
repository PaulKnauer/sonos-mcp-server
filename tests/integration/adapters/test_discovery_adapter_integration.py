"""Integration tests for DiscoveryAdapter against real Sonos hardware.

These tests are SKIPPED unless the ``--hardware`` pytest flag is passed
or the ``SONIQ_HARDWARE_TESTS`` environment variable is set to ``1``.
They require the test machine to be on the same network as live Sonos speakers.
"""

from __future__ import annotations

import os

import pytest

from soniq_mcp.adapters.discovery_adapter import DiscoveryAdapter
from soniq_mcp.domain.models import Room


def hardware_available() -> bool:
    return os.environ.get("SONIQ_HARDWARE_TESTS", "0") == "1"


pytestmark = pytest.mark.skipif(
    not hardware_available(),
    reason="Set SONIQ_HARDWARE_TESTS=1 to run hardware integration tests",
)


class TestDiscoveryAdapterHardware:
    def test_discovers_at_least_one_room(self) -> None:
        adapter = DiscoveryAdapter()
        rooms = adapter.discover_rooms(timeout=10.0)
        assert len(rooms) > 0, "Expected at least one Sonos zone on the network"

    def test_rooms_have_required_fields(self) -> None:
        adapter = DiscoveryAdapter()
        rooms = adapter.discover_rooms(timeout=10.0)
        for room in rooms:
            assert isinstance(room, Room)
            assert room.name, f"Room has empty name: {room}"
            assert room.uid.startswith("RINCON_"), f"Unexpected UID format: {room.uid}"
            assert room.ip_address, f"Room has empty IP: {room}"

    def test_at_least_one_coordinator(self) -> None:
        adapter = DiscoveryAdapter()
        rooms = adapter.discover_rooms(timeout=10.0)
        coordinators = [r for r in rooms if r.is_coordinator]
        assert len(coordinators) > 0, "Expected at least one group coordinator"
