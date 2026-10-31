"""Unit tests for SoCoAdapter radio favourites."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import FavouritesError
from soniq_mcp.domain.models import RadioFavourite

IP = "192.168.1.10"


def _didl(title, uri):
    # spec excludes ``.uri`` so the adapter must use get_uri()
    item = MagicMock(spec=["title", "get_uri", "to_didl_string"])
    item.title = title
    item.get_uri.return_value = uri
    item.to_didl_string.return_value = f"<meta>{title}</meta>"
    return item


class TestGetRadioFavourites:
    def test_returns_stations_and_shows(self):
        zone = MagicMock()
        zone.music_library.get_favorite_radio_stations.return_value = [
            _didl("Radio 1", "x-sonosapi-stream:s1")
        ]
        zone.music_library.get_favorite_radio_shows.return_value = [
            _didl("Podcast", "x-sonosapi-stream:p1")
        ]

        with patch("soco.SoCo", return_value=zone):
            result = SoCoAdapter().get_radio_favourites(IP)

        assert result == [
            RadioFavourite("Radio 1", "x-sonosapi-stream:s1", "station", "<meta>Radio 1</meta>"),
            RadioFavourite("Podcast", "x-sonosapi-stream:p1", "show", "<meta>Podcast</meta>"),
        ]

    def test_soco_error_raises_favourites_error(self):
        zone = MagicMock()
        zone.music_library.get_favorite_radio_stations.side_effect = RuntimeError("upnp")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(FavouritesError, match="radio favourites"):
                SoCoAdapter().get_radio_favourites(IP)
