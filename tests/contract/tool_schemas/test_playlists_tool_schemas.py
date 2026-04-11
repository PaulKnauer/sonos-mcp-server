"""Contract tests for playlists tool schemas.

Validates that tool names, descriptions, and parameter schemas remain stable.
These tests act as a breaking-change guard for MCP clients that depend on the
tool surface.
"""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import SonosPlaylist
from soniq_mcp.tools.playlists import register


class FakePlaylistService:
    def list_playlists(self) -> list[SonosPlaylist]:
        return []

    def play_playlist(self, room_name: str, uri: str) -> None:
        pass

    def create_playlist(self, title: str) -> SonosPlaylist:
        return SonosPlaylist(title=title, uri="x-rincon://new", item_id="SQ:1")

    def update_playlist(self, playlist_id: str, room: str) -> SonosPlaylist:
        return SonosPlaylist(title="Test", uri="x-rincon://pl", item_id=playlist_id)

    def delete_playlist(self, playlist_id: str) -> dict:
        return {"playlist_id": playlist_id, "status": "deleted"}


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, FakePlaylistService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestPlaylistToolSurfaceContract:
    def test_playlist_tool_surface_is_stable(self, registered_app: FastMCP) -> None:
        assert set(get_tools(registered_app)) == {
            "list_playlists",
            "play_playlist",
            "create_playlist",
            "update_playlist",
            "delete_playlist",
        }

    def test_rename_playlist_is_not_exposed(self, registered_app: FastMCP) -> None:
        assert "rename_playlist" not in get_tools(registered_app)


class TestListPlaylistsContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "list_playlists" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["list_playlists"].description
        assert desc and len(desc) > 0

    def test_has_no_required_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["list_playlists"].parameters
        assert schema.get("required", []) == []

    def test_is_read_only(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["list_playlists"].annotations
        assert ann.readOnlyHint is True
        assert ann.destructiveHint is False


class TestPlayPlaylistContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "play_playlist" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["play_playlist"].description
        assert desc and len(desc) > 0

    def test_requires_room_and_uri_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["play_playlist"].parameters
        assert "room" in schema["properties"]
        assert "uri" in schema["properties"]
        assert set(schema["required"]) == {"room", "uri"}
        assert schema["properties"]["room"]["type"] == "string"
        assert schema["properties"]["uri"]["type"] == "string"

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["play_playlist"].annotations
        assert ann.readOnlyHint is False


class TestCreatePlaylistContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "create_playlist" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["create_playlist"].description
        assert desc and len(desc) > 0

    def test_requires_title_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["create_playlist"].parameters
        assert "title" in schema["properties"]
        assert "title" in schema.get("required", [])
        assert schema["properties"]["title"]["type"] == "string"

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["create_playlist"].annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is False


class TestUpdatePlaylistContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "update_playlist" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["update_playlist"].description
        assert desc and len(desc) > 0

    def test_requires_playlist_id_and_room(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["update_playlist"].parameters
        assert "playlist_id" in schema["properties"]
        assert "room" in schema["properties"]
        assert set(schema["required"]) == {"playlist_id", "room"}
        assert schema["properties"]["playlist_id"]["type"] == "string"
        assert schema["properties"]["room"]["type"] == "string"

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["update_playlist"].annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is False


class TestDeletePlaylistContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "delete_playlist" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["delete_playlist"].description
        assert desc and len(desc) > 0

    def test_requires_playlist_id_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["delete_playlist"].parameters
        assert "playlist_id" in schema["properties"]
        assert "playlist_id" in schema.get("required", [])
        assert schema["properties"]["playlist_id"]["type"] == "string"

    def test_is_destructive_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["delete_playlist"].annotations
        assert ann.destructiveHint is True
        assert ann.readOnlyHint is False
