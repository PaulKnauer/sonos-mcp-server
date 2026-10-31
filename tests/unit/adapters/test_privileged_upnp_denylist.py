"""Guard against wiring privileged Sonos UPnP APIs into SoniqMCP.

SoCo exposes unauthenticated UPnP/SOAP calls that go well beyond playback
control: locking hardware buttons, toggling LEDs, enabling microphones,
submitting diagnostics, managing music service accounts, and event
subscriptions whose payloads may carry household or service details.

SoniqMCP deliberately exposes an allowlisted capability surface (see
docs/security/threat-model.md, E5/ID6). Adding any of these APIs is a
threat-model change and must be reviewed, not slipped in with a feature.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[3] / "src" / "soniq_mcp"

PRIVILEGED_API_PATTERNS: dict[str, str] = {
    "hardware button lock": r"buttons_enabled|SetButtonLockState",
    "status LED control": r"status_light|SetLEDState",
    "microphone state": r"mic_enabled",
    "diagnostics submission": r"SubmitDiagnostics",
    "music service accounts": r"musicServices|music_services|MusicService",
    "event subscriptions": r"soco\.events|\.subscribe\(",
    "raw zone group topology service": r"zoneGroupTopology",
}


def _source_files() -> list[Path]:
    return sorted(p for p in SRC_ROOT.rglob("*.py") if "__pycache__" not in p.parts)


def test_source_tree_is_found() -> None:
    assert _source_files(), f"no Python sources found under {SRC_ROOT}"


@pytest.mark.parametrize("capability", sorted(PRIVILEGED_API_PATTERNS))
def test_privileged_upnp_api_not_referenced(capability: str) -> None:
    pattern = re.compile(PRIVILEGED_API_PATTERNS[capability])
    hits = [
        f"{path.relative_to(SRC_ROOT)}:{lineno}"
        for path in _source_files()
        for lineno, line in enumerate(path.read_text().splitlines(), start=1)
        if pattern.search(line)
    ]
    assert not hits, (
        f"Privileged Sonos API ({capability}) referenced in: {', '.join(hits)}. "
        "Update docs/security/threat-model.md and get a security review before "
        "exposing it."
    )
