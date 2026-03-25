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
class SystemTopology:
    """Snapshot of the full Sonos household topology.

    Attributes:
        rooms: All discovered rooms/zones.
        coordinator_count: Number of group coordinators found.
        total_count: Total number of zones found.
    """

    rooms: tuple[Room, ...]
    coordinator_count: int
    total_count: int

    @classmethod
    def from_rooms(cls, rooms: list[Room]) -> "SystemTopology":
        """Build a topology snapshot from a flat list of rooms."""
        return cls(
            rooms=tuple(rooms),
            coordinator_count=sum(1 for r in rooms if r.is_coordinator),
            total_count=len(rooms),
        )
