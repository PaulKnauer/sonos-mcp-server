"""Contract tests for local music-library tool schemas."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import LibraryValidationError, SonosDiscoveryError
from soniq_mcp.domain.models import LibraryItem
from soniq_mcp.tools.library import register


class FakeLibraryService:
    def browse_library(
        self,
        *,
        category: str,
        start: object = 0,
        limit: object = 100,
        parent_id: str | None = None,
    ) -> dict:
        return {
            "category": category,
            "parent_id": parent_id,
            "items": [
                LibraryItem(
                    title="Album",
                    item_type="object.container.album.musicAlbum",
                    item_id="A:ALBUM/1",
                    uri=None,
                    album_art_uri=None,
                    is_browsable=True,
                    is_playable=False,
                )
            ],
            "start": start if isinstance(start, int) else 0,
            "limit": limit if isinstance(limit, int) else 100,
            "has_more": False,
        }

    def play_library_item(
        self,
        *,
        room: str,
        title: str,
        uri: object,
        item_id: str | None = None,
        is_playable: object = True,
    ) -> dict:
        return {
            "status": "ok",
            "room": room,
            "title": title,
            "item_id": item_id,
            "uri": uri if isinstance(uri, str) else "",
        }


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, FakeLibraryService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


def _property_type(prop: dict) -> str | None:
    if "type" in prop:
        return prop["type"]
    any_of = prop.get("anyOf", [])
    types = [entry.get("type") for entry in any_of if "type" in entry]
    if len(types) == 1:
        return types[0]
    return None


class TestLibraryToolSurfaceContract:
    def test_library_tool_surface_is_stable(self, registered_app: FastMCP) -> None:
        assert set(get_tools(registered_app)) == {"browse_library", "play_library_item"}


class TestBrowseLibraryContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "browse_library" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["browse_library"].description
        assert desc and len(desc) > 0

    def test_requires_category_only(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["browse_library"].parameters
        assert set(schema.get("required", [])) == {"category"}

    def test_parameter_types_are_stable(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["browse_library"].parameters
        props = schema["properties"]
        assert _property_type(props["category"]) == "string"
        assert _property_type(props["start"]) == "integer"
        assert _property_type(props["limit"]) == "integer"
        assert any(entry.get("type") == "string" for entry in props["parent_id"].get("anyOf", []))

    def test_is_read_only(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["browse_library"].annotations
        assert ann.readOnlyHint is True
        assert ann.destructiveHint is False
        assert ann.idempotentHint is True
        assert ann.openWorldHint is False

    @pytest.mark.anyio
    async def test_response_shape_is_stable(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("browse_library", {"category": "albums"})
        data = json.loads(result[0].text)
        assert data["category"] == "albums"
        assert data["count"] == 1
        assert "has_more" in data
        assert "next_start" in data
        assert data["items"][0]["item_type"] == "object.container.album.musicAlbum"

    @pytest.mark.anyio
    async def test_validation_error_shape_is_stable(self) -> None:
        class _ValidationService(FakeLibraryService):
            def browse_library(self, **kwargs) -> dict:
                raise LibraryValidationError("Unsupported category")

        app = FastMCP("contract-test")
        register(app, SoniqConfig(), _ValidationService())
        result = await app.call_tool("browse_library", {"category": "x"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "library"

    @pytest.mark.anyio
    async def test_discovery_error_shape_is_stable(self) -> None:
        class _DiscoveryService(FakeLibraryService):
            def browse_library(self, **kwargs) -> dict:
                raise SonosDiscoveryError("Discovery failed for 192.168.1.20")

        app = FastMCP("contract-test")
        register(app, SoniqConfig(), _DiscoveryService())
        result = await app.call_tool("browse_library", {"category": "albums"})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"
        assert data["field"] == "sonos_network"
        assert "<redacted-host>" in data["error"]


class TestPlayLibraryItemContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "play_library_item" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["play_library_item"].description
        assert desc and len(desc) > 0

    def test_requires_room_title_uri_and_is_playable(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["play_library_item"].parameters
        assert set(schema.get("required", [])) == {"room", "title", "uri", "is_playable"}

    def test_parameter_types_are_stable(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["play_library_item"].parameters
        props = schema["properties"]
        assert _property_type(props["room"]) == "string"
        assert _property_type(props["title"]) == "string"
        assert _property_type(props["uri"]) == "string"
        assert _property_type(props["is_playable"]) == "boolean"
        assert any(entry.get("type") == "string" for entry in props["item_id"].get("anyOf", []))

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["play_library_item"].annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is False
        assert ann.idempotentHint is False
        assert ann.openWorldHint is False

    @pytest.mark.anyio
    async def test_response_shape_is_stable(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool(
            "play_library_item",
            {
                "room": "Living Room",
                "title": "Track",
                "uri": "x-file-cifs://track.mp3",
                "item_id": "A:TRACKS/1",
                "is_playable": True,
            },
        )
        data = json.loads(result[0].text)
        assert data == {
            "status": "ok",
            "room": "Living Room",
            "title": "Track",
            "item_id": "A:TRACKS/1",
            "uri": "x-file-cifs://track.mp3",
        }

    @pytest.mark.anyio
    async def test_validation_error_shape_is_stable(self) -> None:
        class _ValidationService(FakeLibraryService):
            def play_library_item(self, **kwargs) -> dict:
                raise LibraryValidationError("Invalid uri")

        app = FastMCP("contract-test")
        register(app, SoniqConfig(), _ValidationService())
        result = await app.call_tool(
            "play_library_item",
            {"room": "Living Room", "title": "Track", "uri": "", "is_playable": True},
        )
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "library"
