"""Unit tests for playlists tool handlers."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import FavouritesError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import SonosPlaylist
from soniq_mcp.tools.playlists import register


PLAYLIST = SonosPlaylist(title="Party Mix", uri="x-rincon-playlist://pl1", item_id="SQ:1")


class FakeFavouritesService:
    def __init__(
        self,
        playlists: list[SonosPlaylist] | None = None,
        raise_favourites_error: bool = False,
        raise_room_not_found: bool = False,
        raise_discovery_error: bool = False,
    ) -> None:
        self._playlists = playlists or []
        self._raise_favourites_error = raise_favourites_error
        self._raise_room_not_found = raise_room_not_found
        self._raise_discovery_error = raise_discovery_error
        self.play_calls: list[tuple] = []

    def get_playlists(self) -> list[SonosPlaylist]:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_favourites_error:
            raise FavouritesError("playlists error")
        return self._playlists

    def play_playlist(self, room_name: str, uri: str) -> None:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_room_not_found:
            raise RoomNotFoundError(room_name)
        if self._raise_favourites_error:
            raise FavouritesError("playlists error")
        self.play_calls.append((room_name, uri))


def make_app(service: FakeFavouritesService, tools_disabled: list[str] | None = None) -> FastMCP:
    app = FastMCP("test")
    config = SoniqConfig(tools_disabled=tools_disabled or [])
    register(app, config, service)
    return app


def get_tool(app: FastMCP, name: str):
    return {t.name: t for t in app._tool_manager.list_tools()}.get(name)


def parse(result) -> dict:
    return json.loads(result[0].text)


class TestListPlaylists:
    def test_tool_is_registered(self) -> None:
        app = make_app(FakeFavouritesService())
        assert get_tool(app, "list_playlists") is not None

    def test_not_registered_when_disabled(self) -> None:
        app = make_app(FakeFavouritesService(), tools_disabled=["list_playlists"])
        assert get_tool(app, "list_playlists") is None

    def test_is_read_only(self) -> None:
        app = make_app(FakeFavouritesService())
        tool = get_tool(app, "list_playlists")
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_returns_playlists_list(self) -> None:
        app = make_app(FakeFavouritesService(playlists=[PLAYLIST]))
        result = await app.call_tool("list_playlists", {})
        data = parse(result)
        assert data["count"] == 1
        assert data["items"][0]["title"] == "Party Mix"
        assert data["items"][0]["uri"] == "x-rincon-playlist://pl1"

    @pytest.mark.anyio
    async def test_returns_empty_list_when_no_playlists(self) -> None:
        app = make_app(FakeFavouritesService(playlists=[]))
        result = await app.call_tool("list_playlists", {})
        data = parse(result)
        assert data["count"] == 0
        assert data["items"] == []

    @pytest.mark.anyio
    async def test_returns_error_on_favourites_error(self) -> None:
        app = make_app(FakeFavouritesService(raise_favourites_error=True))
        result = await app.call_tool("list_playlists", {})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "favourites"

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_error(self) -> None:
        app = make_app(FakeFavouritesService(raise_discovery_error=True))
        result = await app.call_tool("list_playlists", {})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"


class TestPlayPlaylist:
    def test_tool_is_registered(self) -> None:
        app = make_app(FakeFavouritesService())
        assert get_tool(app, "play_playlist") is not None

    def test_not_registered_when_disabled(self) -> None:
        app = make_app(FakeFavouritesService(), tools_disabled=["play_playlist"])
        assert get_tool(app, "play_playlist") is None

    def test_is_control_tool(self) -> None:
        app = make_app(FakeFavouritesService())
        tool = get_tool(app, "play_playlist")
        assert tool.annotations.readOnlyHint is False

    @pytest.mark.anyio
    async def test_returns_ok_on_success(self) -> None:
        app = make_app(FakeFavouritesService(playlists=[PLAYLIST]))
        result = await app.call_tool("play_playlist", {"room": "Living Room", "uri": PLAYLIST.uri})
        data = parse(result)
        assert data["status"] == "ok"
        assert data["room"] == "Living Room"
        assert data["uri"] == PLAYLIST.uri

    @pytest.mark.anyio
    async def test_returns_error_on_room_not_found(self) -> None:
        app = make_app(FakeFavouritesService(raise_room_not_found=True))
        result = await app.call_tool("play_playlist", {"room": "Unknown", "uri": PLAYLIST.uri})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_returns_error_on_favourites_error(self) -> None:
        app = make_app(FakeFavouritesService(raise_favourites_error=True))
        result = await app.call_tool("play_playlist", {"room": "Living Room", "uri": PLAYLIST.uri})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "favourites"

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_error(self) -> None:
        app = make_app(FakeFavouritesService(raise_discovery_error=True))
        result = await app.call_tool("play_playlist", {"room": "Living Room", "uri": PLAYLIST.uri})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"
