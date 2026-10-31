"""Unit tests for SoCoAdapter.play_uri."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import PlaybackError

IP = "192.168.1.10"


class TestPlayUri:
    def test_passes_arguments_and_starts_playback(self):
        zone = MagicMock()
        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().play_uri(IP, "http://hermes/a.mp3", "<meta/>", "Hello", True)

        zone.play_uri.assert_called_once_with(
            uri="http://hermes/a.mp3", meta="<meta/>", title="Hello", start=True, force_radio=True
        )

    def test_defaults(self):
        zone = MagicMock()
        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().play_uri(IP, "http://hermes/a.mp3")

        zone.play_uri.assert_called_once_with(
            uri="http://hermes/a.mp3", meta="", title="", start=True, force_radio=False
        )

    def test_soco_error_raises_playback_error(self):
        zone = MagicMock()
        zone.play_uri.side_effect = RuntimeError("UPnP 714")
        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(PlaybackError, match="UPnP 714"):
                SoCoAdapter().play_uri(IP, "http://hermes/a.mp3")
