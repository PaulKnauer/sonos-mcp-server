"""Unit tests for playlists tool handlers."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    PlaylistError,
    PlaylistValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.models import SonosPlaylist
from soniq_mcp.tools.playlists import register

PLAYLIST = SonosPlaylist(title="Party Mix", uri="x-rincon-playlist://pl1", item_id="SQ:1")


class FakePlaylistService:
    def __init__(
        self,
        playlists: list[SonosPlaylist] | None = None,
        raise_playlist_error: bool = False,
        raise_validation_error: bool = False,
        raise_room_not_found: bool = False,
        raise_discovery_error: bool = False,
        created_playlist: SonosPlaylist | None = None,
        updated_playlist: SonosPlaylist | None = None,
    ) -> None:
        self._playlists = playlists if playlists is not None else []
        self._raise_playlist_error = raise_playlist_error
        self._raise_validation_error = raise_validation_error
        self._raise_room_not_found = raise_room_not_found
        self._raise_discovery_error = raise_discovery_error
        self._created_playlist = created_playlist or SonosPlaylist(
            title="New", uri="x-rincon://new", item_id="SQ:99"
        )
        self._updated_playlist = updated_playlist or PLAYLIST
        self.play_calls: list[tuple] = []

    def list_playlists(self) -> list[SonosPlaylist]:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_playlist_error:
            raise PlaylistError("playlist error")
        return self._playlists

    def play_playlist(self, room_name: str, uri: str) -> None:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_room_not_found:
            raise RoomNotFoundError(room_name)
        if self._raise_playlist_error:
            raise PlaylistError("playlist error")
        self.play_calls.append((room_name, uri))

    def create_playlist(self, title: str) -> SonosPlaylist:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_validation_error:
            raise PlaylistValidationError("invalid title")
        if self._raise_playlist_error:
            raise PlaylistError("playlist error")
        return self._created_playlist

    def update_playlist(self, playlist_id: str, room: str) -> SonosPlaylist:
        if self._raise_room_not_found:
            raise RoomNotFoundError(room)
        if self._raise_validation_error:
            raise PlaylistValidationError("invalid id or empty queue")
        if self._raise_playlist_error:
            raise PlaylistError("playlist error")
        return self._updated_playlist

    def delete_playlist(self, playlist_id: str) -> dict:
        if self._raise_validation_error:
            raise PlaylistValidationError("invalid id")
        if self._raise_playlist_error:
            raise PlaylistError("playlist error")
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        return {"playlist_id": playlist_id, "status": "deleted"}


def make_app(service: FakePlaylistService, tools_disabled: list[str] | None = None) -> FastMCP:
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
        app = make_app(FakePlaylistService())
        assert get_tool(app, "list_playlists") is not None

    def test_not_registered_when_disabled(self) -> None:
        app = make_app(FakePlaylistService(), tools_disabled=["list_playlists"])
        assert get_tool(app, "list_playlists") is None

    def test_is_read_only(self) -> None:
        app = make_app(FakePlaylistService())
        tool = get_tool(app, "list_playlists")
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_returns_playlists_list_with_item_id(self) -> None:
        app = make_app(FakePlaylistService(playlists=[PLAYLIST]))
        result = await app.call_tool("list_playlists", {})
        data = parse(result)
        assert data["count"] == 1
        assert data["items"][0]["title"] == "Party Mix"
        assert data["items"][0]["uri"] == "x-rincon-playlist://pl1"
        assert data["items"][0]["item_id"] == "SQ:1"

    @pytest.mark.anyio
    async def test_returns_empty_list_when_no_playlists(self) -> None:
        app = make_app(FakePlaylistService(playlists=[]))
        result = await app.call_tool("list_playlists", {})
        data = parse(result)
        assert data["count"] == 0
        assert data["items"] == []

    @pytest.mark.anyio
    async def test_returns_error_on_playlist_error(self) -> None:
        app = make_app(FakePlaylistService(raise_playlist_error=True))
        result = await app.call_tool("list_playlists", {})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "playlist"

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_error(self) -> None:
        app = make_app(FakePlaylistService(raise_discovery_error=True))
        result = await app.call_tool("list_playlists", {})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"


class TestPlayPlaylist:
    def test_tool_is_registered(self) -> None:
        app = make_app(FakePlaylistService())
        assert get_tool(app, "play_playlist") is not None

    def test_not_registered_when_disabled(self) -> None:
        app = make_app(FakePlaylistService(), tools_disabled=["play_playlist"])
        assert get_tool(app, "play_playlist") is None

    def test_is_control_tool(self) -> None:
        app = make_app(FakePlaylistService())
        tool = get_tool(app, "play_playlist")
        assert tool.annotations.readOnlyHint is False

    @pytest.mark.anyio
    async def test_returns_ok_on_success(self) -> None:
        app = make_app(FakePlaylistService(playlists=[PLAYLIST]))
        result = await app.call_tool("play_playlist", {"room": "Living Room", "uri": PLAYLIST.uri})
        data = parse(result)
        assert data["status"] == "ok"
        assert data["room"] == "Living Room"
        assert data["uri"] == PLAYLIST.uri

    @pytest.mark.anyio
    async def test_returns_error_on_room_not_found(self) -> None:
        app = make_app(FakePlaylistService(raise_room_not_found=True))
        result = await app.call_tool("play_playlist", {"room": "Unknown", "uri": PLAYLIST.uri})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_returns_error_on_playlist_error(self) -> None:
        app = make_app(FakePlaylistService(raise_playlist_error=True))
        result = await app.call_tool("play_playlist", {"room": "Living Room", "uri": PLAYLIST.uri})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "playlist"

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_error(self) -> None:
        app = make_app(FakePlaylistService(raise_discovery_error=True))
        result = await app.call_tool("play_playlist", {"room": "Living Room", "uri": PLAYLIST.uri})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"


class TestPlayPlaylistLifecycleInteroperability:
    """Verify play_playlist accepts URIs produced by lifecycle tools."""

    @pytest.mark.anyio
    async def test_plays_uri_from_create_playlist_output(self) -> None:
        """A URI from create_playlist tool output is valid input for play_playlist."""
        created = SonosPlaylist(title="Road Trip", uri="x-rincon-playlist://rt", item_id="SQ:7")
        svc = FakePlaylistService(playlists=[created], created_playlist=created)
        app = make_app(svc)
        create_result = await app.call_tool("create_playlist", {"title": "Road Trip"})
        created_data = parse(create_result)
        result = await app.call_tool(
            "play_playlist", {"room": "Living Room", "uri": created_data["uri"]}
        )
        data = parse(result)
        assert data["status"] == "ok"
        assert data["uri"] == "x-rincon-playlist://rt"
        assert svc.play_calls == [("Living Room", "x-rincon-playlist://rt")]

    @pytest.mark.anyio
    async def test_plays_uri_from_update_playlist_output(self) -> None:
        """A URI from update_playlist tool output is valid input for play_playlist."""
        updated = SonosPlaylist(
            title="Party Mix", uri="x-rincon-playlist://updated", item_id="SQ:1"
        )
        svc = FakePlaylistService(playlists=[PLAYLIST], updated_playlist=updated)
        app = make_app(svc)
        update_result = await app.call_tool(
            "update_playlist", {"playlist_id": "SQ:1", "room": "Living Room"}
        )
        updated_data = parse(update_result)
        result = await app.call_tool(
            "play_playlist", {"room": "Living Room", "uri": updated_data["uri"]}
        )
        data = parse(result)
        assert data["status"] == "ok"
        assert data["uri"] == "x-rincon-playlist://updated"

    @pytest.mark.anyio
    async def test_uri_param_passed_to_service_unchanged(self) -> None:
        """The uri argument is forwarded to the service without any modification."""
        svc = FakePlaylistService(playlists=[PLAYLIST])
        app = make_app(svc)
        await app.call_tool("play_playlist", {"room": "Office", "uri": PLAYLIST.uri})
        assert svc.play_calls == [("Office", PLAYLIST.uri)]


class TestCreatePlaylist:
    def test_tool_is_registered(self) -> None:
        app = make_app(FakePlaylistService())
        assert get_tool(app, "create_playlist") is not None

    def test_not_registered_when_disabled(self) -> None:
        app = make_app(FakePlaylistService(), tools_disabled=["create_playlist"])
        assert get_tool(app, "create_playlist") is None

    def test_is_control_tool(self) -> None:
        app = make_app(FakePlaylistService())
        tool = get_tool(app, "create_playlist")
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_returns_playlist_response_on_success(self) -> None:
        new_pl = SonosPlaylist(title="Summer Jams", uri="x-rincon://new", item_id="SQ:5")
        app = make_app(FakePlaylistService(created_playlist=new_pl))
        result = await app.call_tool("create_playlist", {"title": "Summer Jams"})
        data = parse(result)
        assert data["title"] == "Summer Jams"
        assert data["item_id"] == "SQ:5"

    @pytest.mark.anyio
    async def test_returns_error_on_validation_error(self) -> None:
        app = make_app(FakePlaylistService(raise_validation_error=True))
        result = await app.call_tool("create_playlist", {"title": ""})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "playlist"

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_error(self) -> None:
        app = make_app(FakePlaylistService(raise_discovery_error=True))
        result = await app.call_tool("create_playlist", {"title": "Test"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"


class TestUpdatePlaylist:
    def test_tool_is_registered(self) -> None:
        app = make_app(FakePlaylistService())
        assert get_tool(app, "update_playlist") is not None

    def test_not_registered_when_disabled(self) -> None:
        app = make_app(FakePlaylistService(), tools_disabled=["update_playlist"])
        assert get_tool(app, "update_playlist") is None

    def test_is_control_tool(self) -> None:
        app = make_app(FakePlaylistService())
        tool = get_tool(app, "update_playlist")
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_returns_updated_playlist_on_success(self) -> None:
        updated = SonosPlaylist(title="Party Mix", uri="x-rincon://updated", item_id="SQ:1")
        app = make_app(FakePlaylistService(updated_playlist=updated))
        result = await app.call_tool(
            "update_playlist", {"playlist_id": "SQ:1", "room": "Living Room"}
        )
        data = parse(result)
        assert data["item_id"] == "SQ:1"

    @pytest.mark.anyio
    async def test_returns_error_on_room_not_found(self) -> None:
        app = make_app(FakePlaylistService(raise_room_not_found=True))
        result = await app.call_tool("update_playlist", {"playlist_id": "SQ:1", "room": "Unknown"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_returns_error_on_validation_error(self) -> None:
        app = make_app(FakePlaylistService(raise_validation_error=True))
        result = await app.call_tool(
            "update_playlist", {"playlist_id": "SQ:99", "room": "Living Room"}
        )
        data = parse(result)
        assert "error" in data
        assert data["field"] == "playlist"


class TestDeletePlaylist:
    def test_tool_is_registered(self) -> None:
        app = make_app(FakePlaylistService())
        assert get_tool(app, "delete_playlist") is not None

    def test_not_registered_when_disabled(self) -> None:
        app = make_app(FakePlaylistService(), tools_disabled=["delete_playlist"])
        assert get_tool(app, "delete_playlist") is None

    def test_is_destructive_tool(self) -> None:
        app = make_app(FakePlaylistService())
        tool = get_tool(app, "delete_playlist")
        assert tool.annotations.destructiveHint is True
        assert tool.annotations.readOnlyHint is False

    @pytest.mark.anyio
    async def test_returns_confirmation_on_success(self) -> None:
        app = make_app(FakePlaylistService())
        result = await app.call_tool("delete_playlist", {"playlist_id": "SQ:1"})
        data = parse(result)
        assert data["playlist_id"] == "SQ:1"
        assert data["status"] == "deleted"

    @pytest.mark.anyio
    async def test_returns_error_on_validation_error(self) -> None:
        app = make_app(FakePlaylistService(raise_validation_error=True))
        result = await app.call_tool("delete_playlist", {"playlist_id": ""})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "playlist"

    @pytest.mark.anyio
    async def test_returns_error_on_playlist_error(self) -> None:
        app = make_app(FakePlaylistService(raise_playlist_error=True))
        result = await app.call_tool("delete_playlist", {"playlist_id": "SQ:1"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "playlist"

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_error(self) -> None:
        app = make_app(FakePlaylistService(raise_discovery_error=True))
        result = await app.call_tool("delete_playlist", {"playlist_id": "SQ:1"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"
