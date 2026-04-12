"""Local music-library MCP tools for SoniqMCP."""

from __future__ import annotations

import logging
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import LibraryError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import LibraryBrowseResponse

log = logging.getLogger(__name__)

_READ_ONLY_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def register(app: FastMCP, config: SoniqConfig, library_service: object) -> None:
    """Register local music-library browse tools onto the FastMCP application."""

    if "browse_library" not in config.tools_disabled:

        @app.tool(title="Browse Music Library", annotations=_READ_ONLY_TOOL_HINTS)
        def browse_library(
            category: str,
            start: Annotated[object, Field(json_schema_extra={"type": "integer"})] = 0,
            limit: Annotated[object, Field(json_schema_extra={"type": "integer"})] = 100,
            parent_id: str | None = None,
        ) -> dict:
            """Browse a bounded slice of the local Sonos music library."""
            assert_tool_permitted("browse_library", config)
            try:
                result = library_service.browse_library(
                    category=category,
                    start=start,
                    limit=limit,
                    parent_id=parent_id,
                )
                return LibraryBrowseResponse.from_domain(**result).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in browse_library: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except LibraryError as exc:
                return ErrorResponse.from_library_error(exc).model_dump()
