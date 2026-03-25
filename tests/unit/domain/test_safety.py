"""Unit tests for domain safety rules (AC: 1, 3, 4)."""

from __future__ import annotations

import pytest

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import ToolNotPermitted, VolumeCapExceeded
from soniq_mcp.domain.safety import (
    assert_tool_permitted,
    check_volume,
    is_tool_permitted,
    validate_exposure_posture,
)


class TestCheckVolume:
    """Volume safety rule (AC: 3)."""

    def test_volume_within_cap_is_allowed(self) -> None:
        cfg = SoniqConfig(max_volume_pct=80)
        assert check_volume(50, cfg) == 50

    def test_volume_at_cap_is_allowed(self) -> None:
        cfg = SoniqConfig(max_volume_pct=80)
        assert check_volume(80, cfg) == 80

    def test_volume_exceeding_cap_raises(self) -> None:
        cfg = SoniqConfig(max_volume_pct=80)
        with pytest.raises(VolumeCapExceeded) as exc_info:
            check_volume(81, cfg)
        assert exc_info.value.requested == 81
        assert exc_info.value.cap == 80

    def test_volume_zero_is_allowed(self) -> None:
        cfg = SoniqConfig(max_volume_pct=80)
        assert check_volume(0, cfg) == 0

    def test_volume_above_100_raises_value_error(self) -> None:
        cfg = SoniqConfig(max_volume_pct=100)
        with pytest.raises(ValueError):
            check_volume(101, cfg)

    def test_volume_below_zero_raises_value_error(self) -> None:
        cfg = SoniqConfig(max_volume_pct=80)
        with pytest.raises(ValueError):
            check_volume(-1, cfg)

    def test_custom_low_cap_enforced(self) -> None:
        cfg = SoniqConfig(max_volume_pct=30)
        with pytest.raises(VolumeCapExceeded):
            check_volume(31, cfg)

    def test_cap_zero_blocks_all_volume(self) -> None:
        cfg = SoniqConfig(max_volume_pct=0)
        with pytest.raises(VolumeCapExceeded):
            check_volume(1, cfg)

    def test_error_message_is_actionable(self) -> None:
        cfg = SoniqConfig(max_volume_pct=50)
        with pytest.raises(VolumeCapExceeded) as exc_info:
            check_volume(75, cfg)
        msg = str(exc_info.value)
        assert "75" in msg
        assert "50" in msg


class TestToolPermission:
    """Tool restriction controls (AC: 2, 4)."""

    def test_tool_permitted_by_default(self) -> None:
        cfg = SoniqConfig()
        assert is_tool_permitted("ping", cfg) is True

    def test_disabled_tool_not_permitted(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping"])
        assert is_tool_permitted("ping", cfg) is False

    def test_other_tools_unaffected_by_disable(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping"])
        assert is_tool_permitted("server_info", cfg) is True

    def test_assert_permitted_passes_for_allowed(self) -> None:
        cfg = SoniqConfig()
        assert_tool_permitted("ping", cfg)  # should not raise

    def test_assert_permitted_raises_for_disabled(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping"])
        with pytest.raises(ToolNotPermitted) as exc_info:
            assert_tool_permitted("ping", cfg)
        assert exc_info.value.tool_name == "ping"

    def test_multiple_tools_disabled(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping", "server_info"])
        assert is_tool_permitted("ping", cfg) is False
        assert is_tool_permitted("server_info", cfg) is False

    def test_error_message_names_tool(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping"])
        with pytest.raises(ToolNotPermitted) as exc_info:
            assert_tool_permitted("ping", cfg)
        assert "ping" in str(exc_info.value)


class TestExposurePostureValidation:
    """Exposure posture defaults to local (AC: 1, 4)."""

    def test_local_exposure_no_warnings(self) -> None:
        cfg = SoniqConfig(exposure="local")
        assert validate_exposure_posture(cfg) == []

    def test_default_exposure_is_local(self) -> None:
        cfg = SoniqConfig()
        assert validate_exposure_posture(cfg) == []
