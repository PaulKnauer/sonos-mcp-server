"""Documentation regression tests for integration guidance (Story 5.1)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATIONS_README = REPO_ROOT / "docs" / "integrations" / "README.md"
HOME_ASSISTANT_GUIDE = REPO_ROOT / "docs" / "integrations" / "home-assistant.md"
N8N_GUIDE = REPO_ROOT / "docs" / "integrations" / "n8n.md"
SETUP_README = REPO_ROOT / "docs" / "setup" / "README.md"
ROOT_README = REPO_ROOT / "README.md"
PROMPTS_GUIDE = REPO_ROOT / "docs" / "prompts" / "example-uses.md"
TROUBLESHOOTING_GUIDE = REPO_ROOT / "docs" / "setup" / "troubleshooting.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestIntegrationGuides:
    def test_agent_integration_guides_exist(self) -> None:
        assert HOME_ASSISTANT_GUIDE.exists()
        assert N8N_GUIDE.exists()

    def test_integrations_readme_lists_agent_guides(self) -> None:
        readme = _read(INTEGRATIONS_README)
        assert "[Home Assistant](home-assistant.md)" in readme
        assert "[n8n](n8n.md)" in readme
        assert "planned for Epic 5" not in readme

    def test_setup_overview_links_to_agent_guides(self) -> None:
        readme = _read(SETUP_README)
        assert "[Home Assistant](../integrations/home-assistant.md)" in readme
        assert "[n8n](../integrations/n8n.md)" in readme
        assert "[Troubleshooting](troubleshooting.md)" in readme

    def test_root_readme_surfaces_agent_integrations(self) -> None:
        readme = _read(ROOT_README)
        assert "[Home Assistant integration](docs/integrations/home-assistant.md)" in readme
        assert "[n8n integration](docs/integrations/n8n.md)" in readme

    def test_root_readme_qualifies_remote_deployment_claims(self) -> None:
        readme = _read(ROOT_README)
        assert "Docker on Linux" in readme
        assert "documented Helm / k3s guidance" in readme

    def test_prompts_include_agent_automation_examples(self) -> None:
        prompts = _read(PROMPTS_GUIDE)
        assert "## Agent and automation workflows" in prompts
        assert "Home Assistant" in prompts
        assert "`n8n`" in prompts
        assert "Streamable HTTP" in prompts

    def test_agent_guides_call_out_remote_deployment_caveats(self) -> None:
        home_assistant = _read(HOME_ASSISTANT_GUIDE)
        n8n = _read(N8N_GUIDE)
        assert "Docker on Linux" in home_assistant
        assert "`hostNetwork: true`" in home_assistant
        assert "manual workaround" in home_assistant
        assert "[troubleshooting](../setup/troubleshooting.md)" in home_assistant
        assert "Docker on Linux" in n8n
        assert "`hostNetwork: true`" in n8n
        assert "manual workaround" in n8n
        assert "[troubleshooting](../setup/troubleshooting.md)" in n8n

    def test_troubleshooting_guide_matches_supported_diagnostic_categories(self) -> None:
        guide = _read(TROUBLESHOOTING_GUIDE)
        assert "configuration" in guide
        assert "connectivity" in guide
        assert "validation" in guide
        assert "operation" in guide
        assert "`ping`" in guide
        assert "`server_info`" in guide
        assert "`list_rooms`" in guide
