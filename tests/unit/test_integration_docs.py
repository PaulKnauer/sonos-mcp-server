"""Documentation regression tests for integration guidance (Story 5.1) and
operational security and release guidance (Story 5.4)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATIONS_README = REPO_ROOT / "docs" / "integrations" / "README.md"
HOME_ASSISTANT_GUIDE = REPO_ROOT / "docs" / "integrations" / "home-assistant.md"
N8N_GUIDE = REPO_ROOT / "docs" / "integrations" / "n8n.md"
SETUP_README = REPO_ROOT / "docs" / "setup" / "README.md"
ROOT_README = REPO_ROOT / "README.md"
PROMPTS_INDEX = REPO_ROOT / "docs" / "prompts" / "README.md"
PROMPTS_GUIDE = REPO_ROOT / "docs" / "prompts" / "example-uses.md"
COMMAND_REFERENCE = REPO_ROOT / "docs" / "prompts" / "command-reference.md"
TROUBLESHOOTING_GUIDE = REPO_ROOT / "docs" / "setup" / "troubleshooting.md"
MAKEFILE = REPO_ROOT / "Makefile"
SECURITY_POLICY = REPO_ROOT / "SECURITY.md"
OPERATIONS_GUIDE = REPO_ROOT / "docs" / "setup" / "operations.md"
DOCKER_GUIDE = REPO_ROOT / "docs" / "setup" / "docker.md"
HELM_GUIDE = REPO_ROOT / "docs" / "setup" / "helm.md"


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

    def test_root_readme_routes_to_prompt_and_command_docs(self) -> None:
        readme = _read(ROOT_README)
        assert "[docs/prompts/example-uses.md](docs/prompts/example-uses.md)" in readme
        assert "[docs/prompts/command-reference.md](docs/prompts/command-reference.md)" in readme
        assert "canonical command surface" in readme

    def test_root_readme_surfaces_input_and_expanded_group_tools(self) -> None:
        readme = _read(ROOT_README)
        assert "`switch_to_line_in`" in readme
        assert "`switch_to_tv`" in readme
        assert "`get_group_volume`" in readme
        assert "`set_group_volume`" in readme
        assert "`adjust_group_volume`" in readme
        assert "`group_mute`" in readme
        assert "`group_unmute`" in readme
        assert "`group_rooms`" in readme

    def test_root_readme_qualifies_remote_deployment_claims(self) -> None:
        readme = _read(ROOT_README)
        assert "Docker on Linux" in readme
        assert "documented Helm / k3s guidance" in readme

    def test_setup_overview_routes_to_product_usage_guides(self) -> None:
        readme = _read(SETUP_README)
        assert "[Prompts and command reference](../prompts/README.md)" in readme
        assert "[Command reference](../prompts/command-reference.md)" in readme
        assert "[Troubleshooting](troubleshooting.md)" in readme

    def test_prompts_index_lists_prompt_and_command_pages(self) -> None:
        index = _read(PROMPTS_INDEX)
        assert "[Example prompts and usage flows](example-uses.md)" in index
        assert "[Command reference](command-reference.md)" in index
        assert "[../setup/README.md](../setup/README.md)" in index

    def test_prompts_include_agent_automation_examples(self) -> None:
        prompts = _read(PROMPTS_GUIDE)
        assert "## Agent and automation workflows" in prompts
        assert "Home Assistant" in prompts
        assert "`n8n`" in prompts
        assert "Streamable HTTP" in prompts
        assert "[command-reference.md](command-reference.md)" in prompts
        assert "[../setup/troubleshooting.md](../setup/troubleshooting.md)" in prompts

    def test_prompts_explain_input_and_group_control_boundaries(self) -> None:
        prompts = _read(PROMPTS_GUIDE)
        assert "## Input switching" in prompts
        assert "`switch_to_line_in`" in prompts
        assert "`switch_to_tv`" in prompts
        assert "`group_rooms`" in prompts
        assert "`get_group_volume`" in prompts
        assert "`set_group_volume`" in prompts
        assert "`adjust_group_volume`" in prompts
        assert "`group_mute`" in prompts
        assert "`group_unmute`" in prompts
        assert "room-level controls" in prompts
        assert "group-level controls" in prompts
        assert "input-specific controls" in prompts

    def test_agent_guides_start_with_diagnostics_before_mutation(self) -> None:
        home_assistant = _read(HOME_ASSISTANT_GUIDE)
        n8n = _read(N8N_GUIDE)
        for guide in (home_assistant, n8n):
            assert "`ping`" in guide
            assert "`server_info`" in guide
            assert "`list_rooms`" in guide

    def test_agent_guides_reference_current_group_and_input_flows(self) -> None:
        home_assistant = _read(HOME_ASSISTANT_GUIDE)
        n8n = _read(N8N_GUIDE)
        assert "`switch_to_tv`" in home_assistant or "`switch_to_line_in`" in home_assistant
        assert "`get_group_volume`" in home_assistant or "`set_group_volume`" in home_assistant
        assert "`group_rooms`" in n8n
        assert "`get_group_volume`" in n8n or "`set_group_volume`" in n8n
        assert "execution layer only" in home_assistant
        assert "execution layer only" in n8n

    def test_command_reference_surfaces_supported_command_paths(self) -> None:
        command_reference = _read(COMMAND_REFERENCE)
        assert "canonical command surface" in command_reference
        assert "| `make install` |" in command_reference
        assert "| `make ci` |" in command_reference
        assert "| `make docker-build` |" in command_reference
        assert "| `make helm-install` |" in command_reference
        assert "uv run python -m soniq_mcp" in command_reference
        assert "local `stdio`" in command_reference
        assert "remote `Streamable HTTP`" in command_reference
        assert (
            "For Claude Desktop local integration, do not pre-start `make run-stdio`."
            in command_reference
        )

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
        assert "`home-network`" in guide
        assert "`ping`" in guide
        assert "`server_info`" in guide
        assert "`list_rooms`" in guide
        assert "## Runtime initialization errors" in guide

    def test_command_reference_targets_match_makefile(self) -> None:
        makefile = _read(MAKEFILE)
        command_reference = _read(COMMAND_REFERENCE)
        defined_targets = {
            match.group(1) for match in re.finditer(r"(?m)^([A-Za-z0-9][A-Za-z0-9_-]*):", makefile)
        }
        supported_targets = [
            "install",
            "run",
            "run-stdio",
            "test",
            "check",
            "lint",
            "format",
            "type-check",
            "coverage",
            "audit",
            "ci",
            "docker-build",
            "docker-run",
            "docker-compose-up",
            "docker-compose-down",
            "helm-lint",
            "helm-template",
            "helm-install",
            "tree",
        ]

        for target in supported_targets:
            assert target in defined_targets
            assert f"`make {target}`" in command_reference


class TestSecurityAndOperationsDocs:
    """Regression tests for the security policy and operator guidance surface (Story 5.4)."""

    def test_security_policy_exists(self) -> None:
        assert SECURITY_POLICY.exists(), "SECURITY.md must exist in the repository root"

    def test_operations_guide_exists(self) -> None:
        assert OPERATIONS_GUIDE.exists(), "docs/setup/operations.md must exist"

    def test_root_readme_links_security_policy(self) -> None:
        readme = _read(ROOT_README)
        assert "SECURITY.md" in readme

    def test_root_readme_links_operations_guide(self) -> None:
        readme = _read(ROOT_README)
        assert "docs/setup/operations.md" in readme

    def test_setup_readme_links_operations_guide(self) -> None:
        readme = _read(SETUP_README)
        assert "operations.md" in readme

    def test_setup_readme_states_no_builtin_auth(self) -> None:
        readme = _read(SETUP_README)
        assert "no built-in" in readme

    def test_security_policy_states_no_builtin_auth(self) -> None:
        policy = _read(SECURITY_POLICY)
        assert "no built-in end-user authentication" in policy

    def test_security_policy_has_reporting_path(self) -> None:
        policy = _read(SECURITY_POLICY)
        assert "Report a vulnerability" in policy
        assert "Security" in policy

    def test_security_policy_has_disclosure_expectations(self) -> None:
        policy = _read(SECURITY_POLICY)
        assert "disclosure" in policy.lower()
        assert "acknowledge" in policy.lower()

    def test_security_policy_states_scope(self) -> None:
        policy = _read(SECURITY_POLICY)
        assert "In scope" in policy
        assert "Out of scope" in policy

    def test_operations_guide_describes_release_automation(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "publish.yml" in guide
        assert "PyPI" in guide
        assert "GHCR" in guide
        assert "v*.*.*" in guide
        assert "GitHub Release" in guide
        assert "gh release create" in guide

    def test_operations_guide_documents_docker_tags(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "semver" in guide.lower() or "major.minor" in guide.lower()
        assert "latest" in guide

    def test_operations_guide_documents_maintainer_release_steps(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "make release-bump-patch" in guide
        assert "make release-tag" in guide
        assert "git push origin v0.1.1" in guide

    def test_operations_guide_documents_upgrade_flows(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "git pull" in guide
        assert "uv sync" in guide
        assert "uv sync --upgrade" not in guide
        assert "docker pull" in guide
        assert "helm upgrade" in guide

    def test_operations_guide_states_deployment_caveats(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "hostNetwork" in guide
        assert "no built-in" in guide
        guide_lower = guide.lower()
        assert (
            "trusted home" in guide_lower
            or "home-network" in guide
            or "home network" in guide_lower
        )

    def test_operations_guide_documents_compatibility_baseline(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "3.12" in guide
        assert "stdio" in guide
        assert "Streamable HTTP" in guide
        assert "Linux" in guide

    def test_docker_guide_has_security_note(self) -> None:
        guide = _read(DOCKER_GUIDE)
        assert "no built-in authentication" in guide

    def test_helm_guide_has_security_note(self) -> None:
        guide = _read(HELM_GUIDE)
        assert "no built-in authentication" in guide

    def test_operations_guide_links_security_policy(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "SECURITY.md" in guide

    def test_operations_guide_does_not_overstate_tag_guarantees(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "CI quality gates passed" not in guide
        assert "triggers the publish workflow" in guide

    def test_operations_guide_uses_truthful_pypi_install_example(self) -> None:
        guide = _read(OPERATIONS_GUIDE)
        assert "pip install soniq-mcp" in guide
        assert "uv add soniq-mcp" not in guide
