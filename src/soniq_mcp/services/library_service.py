"""Library browsing service for SoniqMCP."""

from __future__ import annotations

import re

from soniq_mcp.domain.exceptions import LibraryValidationError, SonosDiscoveryError

SUPPORTED_LIBRARY_CATEGORIES: frozenset[str] = frozenset(
    {"artists", "album_artists", "albums", "tracks", "genres", "composers"}
)
MAX_LIBRARY_BROWSE_LIMIT = 100
_PARENT_ID_PATTERN = re.compile(r"^[A-Z0-9]+:.+")
_CATEGORY_PARENT_PREFIXES: dict[str, tuple[str, ...]] = {
    "artists": ("A:ARTIST",),
    "album_artists": ("A:ALBUMARTIST",),
    "albums": ("A:ALBUM",),
    "tracks": ("A:TRACKS",),
    "genres": ("A:GENRE",),
    "composers": ("A:COMPOSER",),
}


def _validate_category(value: str) -> str:
    if not isinstance(value, str):
        raise LibraryValidationError("Invalid category. Expected a non-empty string.")
    normalized = value.strip().lower()
    if not normalized:
        raise LibraryValidationError("Invalid category. Expected a non-empty string.")
    if normalized not in SUPPORTED_LIBRARY_CATEGORIES:
        supported = ", ".join(sorted(SUPPORTED_LIBRARY_CATEGORIES))
        raise LibraryValidationError(
            f"Unsupported library category {value!r}. Supported categories: {supported}."
        )
    return normalized


def _validate_start(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LibraryValidationError(
            f"Invalid start {value!r}. Expected a non-negative integer."
        )
    return value


def _validate_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise LibraryValidationError(
            f"Invalid limit {value!r}. Expected a positive integer."
        )
    if value > MAX_LIBRARY_BROWSE_LIMIT:
        raise LibraryValidationError(
            f"Invalid limit {value!r}. Maximum supported page size is "
            f"{MAX_LIBRARY_BROWSE_LIMIT}."
        )
    return value


def _validate_parent_id(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise LibraryValidationError("Invalid parent_id. Expected a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise LibraryValidationError("Invalid parent_id. Expected a non-empty string.")
    if not _PARENT_ID_PATTERN.match(normalized):
        raise LibraryValidationError(
            "Invalid parent_id. Expected a normalized Sonos library item identifier."
        )
    return normalized


def _validate_parent_target(category: str, parent_id: str | None) -> None:
    if parent_id is None:
        return
    allowed_prefixes = _CATEGORY_PARENT_PREFIXES[category]
    if parent_id.startswith(allowed_prefixes):
        return
    supported = ", ".join(allowed_prefixes)
    raise LibraryValidationError(
        f"Unsupported parent_id {parent_id!r} for category {category!r}. "
        f"Expected one of: {supported}."
    )


class LibraryService:
    """Service for bounded local Sonos music-library browsing."""

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def browse_library(
        self,
        category: str,
        start: object = 0,
        limit: object = MAX_LIBRARY_BROWSE_LIMIT,
        parent_id: str | None = None,
    ) -> dict:
        normalized_category = _validate_category(category)
        normalized_start = _validate_start(start)
        normalized_limit = _validate_limit(limit)
        normalized_parent_id = _validate_parent_id(parent_id)
        _validate_parent_target(normalized_category, normalized_parent_id)
        ip_address = self._get_any_ip()
        items, total_matches = self._adapter.browse_library(
            ip_address,
            normalized_category,
            start=normalized_start,
            limit=normalized_limit,
            parent_id=normalized_parent_id,
        )
        has_more = self._compute_has_more(
            total_matches=total_matches,
            start=normalized_start,
            returned=len(items),
            limit=normalized_limit,
        )
        return {
            "category": normalized_category,
            "parent_id": normalized_parent_id,
            "items": items,
            "start": normalized_start,
            "limit": normalized_limit,
            "has_more": has_more,
        }

    def _get_any_ip(self) -> str:
        rooms = self._room_service.list_rooms()
        if not rooms:
            raise SonosDiscoveryError("No Sonos rooms found — cannot browse the music library.")
        return rooms[0].ip_address

    @staticmethod
    def _compute_has_more(
        *,
        total_matches: int | None,
        start: int,
        returned: int,
        limit: int,
    ) -> bool:
        if total_matches is not None:
            return start + limit < total_matches
        return returned == limit
