"""Unit tests for local music-library MCP tools."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import LibraryError, LibraryValidationError, SonosDiscoveryError
from soniq_mcp.domain.models import LibraryItem
from soniq_mcp.tools.library import register


class FakeLibraryService:
    def __init__(
        self,
        *,
        raise_library_error: Exception | None = None,
        raise_discovery_error: bool = False,
    ) -> None:
        self.raise_library_error = raise_library_error
        self.raise_discovery_error = raise_discovery_error
        self.calls: list[dict] = []

    def browse_library(
        self,
        *,
        category: str,
        start: object = 0,
        limit: object = 100,
        parent_id: str | None = None,
    ) -> dict:
        self.calls.append(
            {
                "category": category,
                "start": start,
                "limit": limit,
                "parent_id": parent_id,
            }
        )
        if self.raise_discovery_error:
            raise SonosDiscoveryError("network down")
        if self.raise_library_error is not None:
            raise self.raise_library_error
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
            "start": 0 if start is None else start,
            "limit": 100 if limit is None else limit,
            "has_more": False,
        }


def make_app(
    *,
    raise_library_error: Exception | None = None,
    raise_discovery_error: bool = False,
    tools_disabled: list[str] | None = None,
) -> tuple[FastMCP, FakeLibraryService]:
    config = SoniqConfig(tools_disabled=tools_disabled or [])
    svc = FakeLibraryService(
        raise_library_error=raise_library_error,
        raise_discovery_error=raise_discovery_error,
    )
    app = FastMCP("test")
    register(app, config, svc)
    return app, svc


class TestBrowseLibraryTool:
    @pytest.mark.anyio
    async def test_returns_normalized_browse_response(self) -> None:
        app, svc = make_app()

        result = await app.call_tool(
            "browse_library",
            {"category": "albums", "start": 0, "limit": 25, "parent_id": None},
        )
        data = json.loads(result[0].text)

        assert data["category"] == "albums"
        assert data["count"] == 1
        assert data["has_more"] is False
        assert data["items"][0]["title"] == "Album"
        assert svc.calls[0]["limit"] == 25

    @pytest.mark.anyio
    async def test_validation_error_returns_error_shape(self) -> None:
        app, _ = make_app(
            raise_library_error=LibraryValidationError("Unsupported library category 'x'.")
        )

        result = await app.call_tool("browse_library", {"category": "x"})
        data = json.loads(result[0].text)

        assert data["category"] == "validation"
        assert data["field"] == "library"

    @pytest.mark.anyio
    async def test_unsupported_drill_down_target_returns_validation_error_shape(self) -> None:
        app, _ = make_app(
            raise_library_error=LibraryValidationError("Unsupported parent_id 'A:ALBUM/1'.")
        )

        result = await app.call_tool(
            "browse_library", {"category": "artists", "parent_id": "A:ALBUM/1"}
        )
        data = json.loads(result[0].text)

        assert data["category"] == "validation"
        assert data["field"] == "library"

    @pytest.mark.anyio
    async def test_library_error_returns_error_shape(self) -> None:
        app, _ = make_app(raise_library_error=LibraryError("library failed"))

        result = await app.call_tool("browse_library", {"category": "albums"})
        data = json.loads(result[0].text)

        assert data["category"] == "operation"
        assert data["field"] == "library"

    @pytest.mark.anyio
    async def test_discovery_error_returns_connectivity_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)

        result = await app.call_tool("browse_library", {"category": "albums"})
        data = json.loads(result[0].text)

        assert data["category"] == "connectivity"
        assert data["field"] == "sonos_network"
        assert "library" not in data["field"]

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["browse_library"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "browse_library" not in tools

    def test_tool_annotations_are_read_only(self) -> None:
        app, _ = make_app()
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        annotations = tools["browse_library"].annotations
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is True
