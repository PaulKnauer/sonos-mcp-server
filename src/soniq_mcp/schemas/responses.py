"""Response schemas for SoniqMCP tool handlers.

All tool handlers return ``.model_dump()`` of these Pydantic models so
the MCP framework receives plain dicts/primitives.

Fields use ``snake_case`` throughout.
"""

from __future__ import annotations

from pydantic import BaseModel

from soniq_mcp.domain.models import Room, SystemTopology, VolumeState


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


class SystemTopologyResponse(BaseModel):
    """Response for the ``get_system_topology`` tool."""

    rooms: list[RoomResponse]
    coordinator_count: int
    total_count: int

    @classmethod
    def from_domain(cls, topology: SystemTopology) -> "SystemTopologyResponse":
        return cls(
            rooms=[RoomResponse.from_domain(r) for r in topology.rooms],
            coordinator_count=topology.coordinator_count,
            total_count=topology.total_count,
        )
