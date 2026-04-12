"""Unit tests for LibraryService."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import LibraryValidationError, SonosDiscoveryError
from soniq_mcp.domain.models import LibraryItem, Room
from soniq_mcp.services.library_service import MAX_LIBRARY_BROWSE_LIMIT, LibraryService


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


class FakeRoomService:
    def __init__(self, rooms: list[Room]) -> None:
        self._rooms = list(rooms)

    def list_rooms(self) -> list[Room]:
        return list(self._rooms)


class FakeAdapter:
    def __init__(
        self,
        *,
        items: list[LibraryItem] | None = None,
        total_matches: int | None = None,
    ) -> None:
        self.items = items or []
        self.total_matches = total_matches
        self.calls: list[tuple[str, str, int, int, str | None]] = []

    def browse_library(
        self,
        ip_address: str,
        category: str,
        *,
        start: int,
        limit: int,
        parent_id: str | None = None,
    ) -> tuple[list[LibraryItem], int | None]:
        self.calls.append((ip_address, category, start, limit, parent_id))
        return self.items, self.total_matches


def make_item(title: str = "Album") -> LibraryItem:
    return LibraryItem(
        title=title,
        item_type="object.container.album.musicAlbum",
        item_id="A:ALBUM/1",
        uri=None,
        album_art_uri=None,
        is_browsable=True,
        is_playable=False,
    )


def test_browse_library_returns_bounded_metadata() -> None:
    svc = LibraryService(
        FakeRoomService([make_room()]),
        FakeAdapter(items=[make_item()], total_matches=250),
    )

    result = svc.browse_library("albums", start=100, limit=100)

    assert result["category"] == "albums"
    assert result["start"] == 100
    assert result["limit"] == 100
    assert result["has_more"] is True
    assert len(result["items"]) == 1


def test_browse_library_uses_parent_id_when_present() -> None:
    adapter = FakeAdapter(items=[make_item()])
    svc = LibraryService(FakeRoomService([make_room()]), adapter)

    svc.browse_library("artists", start=0, limit=25, parent_id="A:ARTIST/1")

    assert adapter.calls == [("192.168.1.10", "artists", 0, 25, "A:ARTIST/1")]


def test_has_more_falls_back_to_page_size_when_total_unknown() -> None:
    items = [make_item(f"Album {idx}") for idx in range(10)]
    svc = LibraryService(
        FakeRoomService([make_room()]),
        FakeAdapter(items=items, total_matches=None),
    )

    result = svc.browse_library("albums", start=0, limit=10)

    assert result["has_more"] is True


def test_invalid_category_raises_validation_error() -> None:
    svc = LibraryService(FakeRoomService([make_room()]), FakeAdapter())

    with pytest.raises(LibraryValidationError, match="Unsupported library category"):
        svc.browse_library("playlists")


def test_invalid_start_raises_validation_error() -> None:
    svc = LibraryService(FakeRoomService([make_room()]), FakeAdapter())

    with pytest.raises(LibraryValidationError, match="Invalid start"):
        svc.browse_library("albums", start="0")


def test_invalid_limit_raises_validation_error() -> None:
    svc = LibraryService(FakeRoomService([make_room()]), FakeAdapter())

    with pytest.raises(LibraryValidationError, match="Maximum supported page size"):
        svc.browse_library("albums", limit=MAX_LIBRARY_BROWSE_LIMIT + 1)


def test_blank_parent_id_raises_validation_error() -> None:
    svc = LibraryService(FakeRoomService([make_room()]), FakeAdapter())

    with pytest.raises(LibraryValidationError, match="parent_id"):
        svc.browse_library("artists", parent_id="   ")


def test_malformed_parent_id_raises_validation_error() -> None:
    svc = LibraryService(FakeRoomService([make_room()]), FakeAdapter())

    with pytest.raises(LibraryValidationError, match="normalized Sonos library item"):
        svc.browse_library("artists", parent_id="artist-1")


def test_unsupported_drill_down_target_raises_validation_error() -> None:
    svc = LibraryService(FakeRoomService([make_room()]), FakeAdapter())

    with pytest.raises(LibraryValidationError, match="Unsupported parent_id"):
        svc.browse_library("artists", parent_id="A:ALBUM/1")


def test_no_rooms_raises_discovery_error() -> None:
    svc = LibraryService(FakeRoomService([]), FakeAdapter())

    with pytest.raises(SonosDiscoveryError, match="cannot browse the music library"):
        svc.browse_library("albums")


def test_has_more_uses_requested_window_when_total_known() -> None:
    svc = LibraryService(
        FakeRoomService([make_room()]),
        FakeAdapter(items=[], total_matches=250),
    )

    result = svc.browse_library("albums", start=100, limit=100)

    assert result["has_more"] is True
