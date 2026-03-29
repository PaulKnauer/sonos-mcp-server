"""Unit tests for SoCoAdapter queue operations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import QueueError
from soniq_mcp.domain.models import QueueItem

IP = "192.168.1.10"


def _make_didl(
    title="Track", creator="Artist", album="Album", uri="x-sonos:track", album_art_uri="http://art"
):
    item = MagicMock()
    item.title = title
    item.creator = creator
    item.album = album
    item.uri = uri
    item.album_art_uri = album_art_uri
    return item


class TestGetQueue:
    def test_returns_queue_items_with_1based_positions(self):
        raw = [
            _make_didl("T1", "A1", "Al1", "uri:1", "art:1"),
            _make_didl("T2", "A2", "Al2", "uri:2", "art:2"),
        ]
        zone = MagicMock()
        zone.get_queue.return_value = raw

        with patch("soco.SoCo", return_value=zone):
            adapter = SoCoAdapter()
            result = adapter.get_queue(IP)

        assert len(result) == 2
        assert result[0] == QueueItem(
            position=1, uri="uri:1", title="T1", artist="A1", album="Al1", album_art_uri="art:1"
        )
        assert result[1] == QueueItem(
            position=2, uri="uri:2", title="T2", artist="A2", album="Al2", album_art_uri="art:2"
        )

    def test_empty_queue_returns_empty_list(self):
        zone = MagicMock()
        zone.get_queue.return_value = []

        with patch("soco.SoCo", return_value=zone):
            result = SoCoAdapter().get_queue(IP)

        assert result == []

    def test_soco_error_raises_queue_error(self):
        zone = MagicMock()
        zone.get_queue.side_effect = RuntimeError("network timeout")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(QueueError, match="Failed to get queue"):
                SoCoAdapter().get_queue(IP)

    def test_empty_string_fields_become_none(self):
        raw = [_make_didl(title="", creator="", album="", uri="uri:1", album_art_uri="")]
        zone = MagicMock()
        zone.get_queue.return_value = raw

        with patch("soco.SoCo", return_value=zone):
            result = SoCoAdapter().get_queue(IP)

        assert result[0].title is None
        assert result[0].artist is None
        assert result[0].album is None
        assert result[0].album_art_uri is None


class TestAddToQueue:
    def test_returns_position_from_soco(self):
        zone = MagicMock()
        zone.add_uri_to_queue.return_value = 3

        with patch("soco.SoCo", return_value=zone):
            position = SoCoAdapter().add_to_queue(IP, "x-sonos:track")

        assert position == 3
        zone.add_uri_to_queue.assert_called_once_with("x-sonos:track")

    def test_soco_error_raises_queue_error(self):
        zone = MagicMock()
        zone.add_uri_to_queue.side_effect = RuntimeError("upnp error")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(QueueError, match="Failed to add to queue"):
                SoCoAdapter().add_to_queue(IP, "x-sonos:track")


class TestRemoveFromQueue:
    def test_removes_item_at_position(self):
        items = [_make_didl("T1", uri="uri:1"), _make_didl("T2", uri="uri:2")]
        zone = MagicMock()
        zone.get_queue.return_value = items

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().remove_from_queue(IP, 2)

        zone.remove_from_queue.assert_called_once_with(items[1])

    def test_position_out_of_range_raises_queue_error(self):
        zone = MagicMock()
        zone.get_queue.return_value = [_make_didl()]

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(QueueError, match="out of range"):
                SoCoAdapter().remove_from_queue(IP, 5)

    def test_position_zero_raises_queue_error(self):
        zone = MagicMock()
        zone.get_queue.return_value = [_make_didl()]

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(QueueError, match="out of range"):
                SoCoAdapter().remove_from_queue(IP, 0)

    def test_soco_remove_error_raises_queue_error(self):
        items = [_make_didl()]
        zone = MagicMock()
        zone.get_queue.return_value = items
        zone.remove_from_queue.side_effect = RuntimeError("upnp error")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(QueueError, match="Failed to remove"):
                SoCoAdapter().remove_from_queue(IP, 1)


class TestClearQueue:
    def test_calls_clear_queue(self):
        zone = MagicMock()

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().clear_queue(IP)

        zone.clear_queue.assert_called_once()

    def test_soco_error_raises_queue_error(self):
        zone = MagicMock()
        zone.clear_queue.side_effect = RuntimeError("upnp error")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(QueueError, match="Failed to clear"):
                SoCoAdapter().clear_queue(IP)


class TestPlayFromQueue:
    def test_calls_play_from_queue_with_0based_index(self):
        zone = MagicMock()

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().play_from_queue(IP, 3)

        zone.play_from_queue.assert_called_once_with(2)

    def test_position_1_maps_to_index_0(self):
        zone = MagicMock()

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().play_from_queue(IP, 1)

        zone.play_from_queue.assert_called_once_with(0)

    def test_position_zero_raises_queue_error(self):
        with pytest.raises(QueueError, match="invalid"):
            SoCoAdapter().play_from_queue(IP, 0)

    def test_negative_position_raises_queue_error(self):
        with pytest.raises(QueueError, match="invalid"):
            SoCoAdapter().play_from_queue(IP, -1)

    def test_soco_error_raises_queue_error(self):
        zone = MagicMock()
        zone.play_from_queue.side_effect = RuntimeError("upnp error")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(QueueError, match="Failed to play from queue"):
                SoCoAdapter().play_from_queue(IP, 1)
