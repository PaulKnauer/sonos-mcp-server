"""Shared Sonos orchestration service for core playback and volume features."""

from __future__ import annotations

import logging

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.models import PlaybackState, Room, TrackInfo, VolumeState
from soniq_mcp.domain.safety import check_volume

log = logging.getLogger(__name__)


class SonosService:
    """Shared orchestration boundary for room-targeted Sonos operations."""

    def __init__(self, room_service: object, adapter: object, config: SoniqConfig) -> None:
        self._room_service = room_service
        self._adapter = adapter
        self._config = config

    def play(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.play(room.ip_address)

    def pause(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.pause(room.ip_address)

    def stop(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.stop(room.ip_address)

    def next_track(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.next_track(room.ip_address)

    def previous_track(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.previous_track(room.ip_address)

    def get_playback_state(self, room_name: str) -> PlaybackState:
        room = self._room_service.get_room(room_name)
        return self._adapter.get_playback_state(room.ip_address, room.name)

    def get_track_info(self, room_name: str) -> TrackInfo:
        room = self._resolve_track_info_room(room_name)
        return self._adapter.get_track_info(room.ip_address)

    def get_volume_state(self, room_name: str) -> VolumeState:
        room = self._room_service.get_room(room_name)
        volume = self._adapter.get_volume(room.ip_address)
        is_muted = self._adapter.get_mute(room.ip_address)
        return VolumeState(room_name=room.name, volume=volume, is_muted=is_muted)

    def set_volume(self, room_name: str, volume: int) -> None:
        check_volume(volume, self._config)
        room = self._room_service.get_room(room_name)
        self._adapter.set_volume(room.ip_address, volume)

    def adjust_volume(self, room_name: str, delta: int) -> VolumeState:
        room = self._room_service.get_room(room_name)
        current = self._adapter.get_volume(room.ip_address)
        target = max(0, min(100, current + delta))
        check_volume(target, self._config)
        self._adapter.set_volume(room.ip_address, target)
        is_muted = self._adapter.get_mute(room.ip_address)
        return VolumeState(room_name=room.name, volume=target, is_muted=is_muted)

    def mute(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.set_mute(room.ip_address, True)

    def unmute(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.set_mute(room.ip_address, False)

    def _resolve_track_info_room(self, room_name: str) -> Room:
        room = self._room_service.get_room(room_name)
        coordinator_uid = room.group_coordinator_uid
        if not coordinator_uid:
            return room

        rooms = self._room_service.list_rooms()
        for candidate in rooms:
            if candidate.uid == coordinator_uid:
                log.debug(
                    "get_track_info: room=%r routed to coordinator=%r",
                    room_name,
                    candidate.name,
                )
                return candidate

        log.debug(
            "get_track_info: coordinator uid %r not found for room=%r; using room ip",
            coordinator_uid,
            room_name,
        )
        return room
