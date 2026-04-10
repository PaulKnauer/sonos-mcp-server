"""Group service for SoniqMCP.

Orchestrates room grouping operations: topology inspection, join, unjoin,
party mode, and group-level audio control. Delegates Sonos interaction to
SoCoAdapter and room resolution to RoomService.
"""

from __future__ import annotations

from soniq_mcp.domain.exceptions import GroupError, GroupValidationError, VolumeCapExceeded
from soniq_mcp.domain.models import GroupAudioState, Room


class GroupService:
    """Service for Sonos room grouping operations."""

    def __init__(self, room_service: object, adapter: object, config: object = None) -> None:
        self._room_service = room_service
        self._adapter = adapter
        self._config = config

    def get_group_topology(self) -> list[Room]:
        """Return all rooms with group membership information.

        Group topology is derived from Room.is_coordinator and
        Room.group_coordinator_uid at the schema layer.
        """
        return self._room_service.list_rooms()

    def join_group(self, room_name: str, coordinator_name: str) -> None:
        """Join room_name to the group coordinated by coordinator_name."""
        room = self._room_service.get_room(room_name)
        coordinator = self._room_service.get_room(coordinator_name)
        self._adapter.join_group(room.ip_address, coordinator.ip_address)

    def unjoin_room(self, room_name: str) -> None:
        """Remove room_name from its current group."""
        room = self._room_service.get_room(room_name)
        self._adapter.unjoin_room(room.ip_address)

    def party_mode(self) -> None:
        """Join all rooms into a single whole-home group."""
        rooms = self._room_service.list_rooms()
        if not rooms:
            raise GroupError("No Sonos rooms found — cannot execute party mode")
        self._adapter.party_mode(rooms[0].ip_address)

    # ------------------------------------------------------------------
    # Group-audio helpers
    # ------------------------------------------------------------------

    def _resolve_group_snapshot(self, room_name: str) -> tuple[Room, Room, tuple[str, ...]]:
        """Resolve group state from a single room/topology snapshot.

        Returns:
            (target_room, coordinator_room, member_room_names)

        Raises:
            RoomNotFoundError: If room_name is not found.
            GroupValidationError: If the room has no grouped peers.
        """
        rooms: list[Room] = self._room_service.list_rooms()
        uid_to_room: dict[str, Room] = {r.uid: r for r in rooms}
        name_to_room: dict[str, Room] = {r.name.lower(): r for r in rooms}

        target = name_to_room.get(room_name.strip().lower())
        if target is None:
            from soniq_mcp.domain.exceptions import RoomNotFoundError

            raise RoomNotFoundError(room_name)

        # Resolve coordinator
        if target.is_coordinator:
            coordinator_uid = target.uid
        elif target.group_coordinator_uid:
            coordinator_uid = target.group_coordinator_uid
        else:
            raise GroupValidationError(
                f"Room '{room_name}' is not part of an active group. "
                "Use 'join_group' to add it to a group first."
            )

        coordinator = uid_to_room.get(coordinator_uid)
        if coordinator is None:
            raise GroupValidationError(f"Could not resolve coordinator for room '{room_name}'.")

        # Collect all group members from the snapshot
        member_names: list[str] = []
        for room in rooms:
            if room.is_coordinator and room.uid == coordinator_uid:
                member_names.insert(0, room.name)
            elif room.group_coordinator_uid == coordinator_uid:
                member_names.append(room.name)

        if len(member_names) < 2:
            raise GroupValidationError(
                f"Room '{room_name}' is not part of an active group. "
                "Use 'join_group' to add it to a group first."
            )

        return target, coordinator, tuple(member_names)

    def get_group_audio_state(self, room_name: str) -> GroupAudioState:
        """Return the current group volume and mute state for the active group.

        Args:
            room_name: Any room in the target group.

        Returns:
            GroupAudioState with volume and mute drawn from the group coordinator.

        Raises:
            RoomNotFoundError: If room_name is not found.
            GroupValidationError: If room is not part of an active group.
            GroupError: If the SoCo adapter call fails.
        """
        target, coordinator, member_names = self._resolve_group_snapshot(room_name)
        volume = self._adapter.get_group_volume(coordinator.ip_address)
        is_muted = self._adapter.get_group_mute(coordinator.ip_address)
        return GroupAudioState(
            room_name=target.name,
            coordinator_room_name=coordinator.name,
            member_room_names=member_names,
            volume=volume,
            is_muted=is_muted,
        )

    def set_group_volume(self, room_name: str, volume: int) -> GroupAudioState:
        """Set the group volume to an absolute level.

        Args:
            room_name: Any room in the target group.
            volume: Target volume level (0-100).

        Returns:
            GroupAudioState reflecting the resulting state.

        Raises:
            RoomNotFoundError: If room_name is not found.
            GroupValidationError: If room is not part of an active group.
            VolumeCapExceeded: If volume exceeds configured max_volume_pct.
            GroupError: If the SoCo adapter call fails.
        """
        target, coordinator, member_names = self._resolve_group_snapshot(room_name)
        cap = self._config.max_volume_pct if self._config is not None else 100
        if not 0 <= volume <= 100:
            raise GroupValidationError(f"Group volume must be 0-100, got {volume}.")
        if volume > cap:
            raise VolumeCapExceeded(requested=volume, cap=cap)
        self._adapter.set_group_volume(coordinator.ip_address, volume)
        is_muted = self._adapter.get_group_mute(coordinator.ip_address)
        return GroupAudioState(
            room_name=target.name,
            coordinator_room_name=coordinator.name,
            member_room_names=member_names,
            volume=volume,
            is_muted=is_muted,
        )

    def adjust_group_volume(self, room_name: str, delta: int) -> GroupAudioState:
        """Adjust the group volume by a relative delta.

        Args:
            room_name: Any room in the target group.
            delta: Volume change amount (can be negative).

        Returns:
            GroupAudioState reflecting the resulting state.

        Raises:
            RoomNotFoundError: If room_name is not found.
            GroupValidationError: If room is not part of an active group.
            VolumeCapExceeded: If the intended target exceeds configured max_volume_pct.
            GroupError: If the SoCo adapter call fails.
        """
        target, coordinator, member_names = self._resolve_group_snapshot(room_name)
        cap = self._config.max_volume_pct if self._config is not None else 100
        current_volume = self._adapter.get_group_volume(coordinator.ip_address)
        intended = current_volume + delta
        if not 0 <= intended <= 100:
            raise GroupValidationError(
                f"Group volume adjustment would result in invalid level {intended}."
            )
        if intended > cap:
            raise VolumeCapExceeded(requested=intended, cap=cap)
        new_volume = self._adapter.adjust_group_volume(coordinator.ip_address, delta)
        is_muted = self._adapter.get_group_mute(coordinator.ip_address)
        return GroupAudioState(
            room_name=target.name,
            coordinator_room_name=coordinator.name,
            member_room_names=member_names,
            volume=new_volume,
            is_muted=is_muted,
        )

    def group_mute(self, room_name: str) -> GroupAudioState:
        """Mute the active group.

        Args:
            room_name: Any room in the target group.

        Returns:
            GroupAudioState with is_muted=True.

        Raises:
            RoomNotFoundError: If room_name is not found.
            GroupValidationError: If room is not part of an active group.
            GroupError: If the SoCo adapter call fails.
        """
        target, coordinator, member_names = self._resolve_group_snapshot(room_name)
        self._adapter.set_group_mute(coordinator.ip_address, True)
        volume = self._adapter.get_group_volume(coordinator.ip_address)
        return GroupAudioState(
            room_name=target.name,
            coordinator_room_name=coordinator.name,
            member_room_names=member_names,
            volume=volume,
            is_muted=True,
        )

    def group_unmute(self, room_name: str) -> GroupAudioState:
        """Unmute the active group.

        Args:
            room_name: Any room in the target group.

        Returns:
            GroupAudioState with is_muted=False.

        Raises:
            RoomNotFoundError: If room_name is not found.
            GroupValidationError: If room is not part of an active group.
            GroupError: If the SoCo adapter call fails.
        """
        target, coordinator, member_names = self._resolve_group_snapshot(room_name)
        self._adapter.set_group_mute(coordinator.ip_address, False)
        volume = self._adapter.get_group_volume(coordinator.ip_address)
        return GroupAudioState(
            room_name=target.name,
            coordinator_room_name=coordinator.name,
            member_room_names=member_names,
            volume=volume,
            is_muted=False,
        )
