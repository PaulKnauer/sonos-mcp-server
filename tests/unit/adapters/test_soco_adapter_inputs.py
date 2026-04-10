"""Unit tests for SoCoAdapter input-switching methods."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import InputError


class FakeZone:
    def __init__(self, music_source: str = "TV") -> None:
        self.line_in_calls = 0
        self.tv_calls = 0
        self._music_source = music_source

    def switch_to_line_in(self) -> None:
        self.line_in_calls += 1
        self._music_source = "LINE_IN"

    def switch_to_tv(self) -> None:
        self.tv_calls += 1
        self._music_source = "TV"

    @property
    def music_source(self) -> str:
        return self._music_source


def _patch_soco(zone: FakeZone):
    return patch("soco.SoCo", return_value=zone)


def test_switch_to_line_in_calls_zone_method() -> None:
    adapter = SoCoAdapter()
    zone = FakeZone()
    with _patch_soco(zone):
        adapter.switch_to_line_in("192.168.1.10")
    assert zone.line_in_calls == 1


def test_switch_to_tv_calls_zone_method() -> None:
    adapter = SoCoAdapter()
    zone = FakeZone()
    with _patch_soco(zone):
        adapter.switch_to_tv("192.168.1.10")
    assert zone.tv_calls == 1


def test_get_music_source_returns_zone_value() -> None:
    adapter = SoCoAdapter()
    zone = FakeZone(music_source="LINE_IN")
    with _patch_soco(zone):
        result = adapter.get_music_source("192.168.1.10")
    assert result == "LINE_IN"


@pytest.mark.parametrize(
    ("method_name", "expected_fragment"),
    [
        ("switch_to_line_in", "line-in"),
        ("switch_to_tv", "TV"),
        ("get_music_source", "music source"),
    ],
)
def test_input_methods_wrap_soco_errors(method_name: str, expected_fragment: str) -> None:
    adapter = SoCoAdapter()
    with patch("soco.SoCo", side_effect=RuntimeError("boom")):
        method = getattr(adapter, method_name)
        with pytest.raises(InputError, match=expected_fragment):
            method("192.168.1.10")
