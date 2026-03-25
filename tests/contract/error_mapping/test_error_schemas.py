"""Contract tests: error response schemas are well-formed (AC: 3, 4)."""

from __future__ import annotations

from soniq_mcp.schemas.errors import ErrorResponse


class TestErrorResponseSchema:
    def test_volume_cap_error_has_required_fields(self) -> None:
        err = ErrorResponse.from_volume_cap(requested=90, cap=80)
        assert "90" in err.error
        assert "80" in err.error
        assert err.field == "volume"
        assert err.suggestion is not None

    def test_tool_not_permitted_error_names_tool(self) -> None:
        err = ErrorResponse.from_tool_not_permitted("ping")
        assert "ping" in err.error
        assert err.field == "tools_disabled"
        assert err.suggestion is not None

    def test_error_response_serialises_to_dict(self) -> None:
        err = ErrorResponse(error="something went wrong")
        d = err.model_dump()
        assert d["error"] == "something went wrong"
        assert d["field"] is None

    def test_error_response_no_internal_paths(self) -> None:
        err = ErrorResponse.from_volume_cap(75, 50)
        assert "/workdir" not in err.error
        assert "/workdir" not in (err.suggestion or "")
