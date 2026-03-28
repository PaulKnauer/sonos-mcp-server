UV ?= $(shell command -v uv 2>/dev/null || printf '%s' "$(HOME)/.local/bin/uv")
PACKAGE ?= soniq_mcp
IMAGE ?= soniq-mcp
TAG ?= local

.PHONY: ensure-uv install run run-stdio test check tree docker-build docker-run docker-compose-up docker-compose-down

ensure-uv:
	@command -v uv >/dev/null 2>&1 || test -x "$(UV)" || { \
		echo "uv not found; installing to $(HOME)/.local/bin"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}

install: ensure-uv
	$(UV) sync

run: ensure-uv
	$(UV) run python -m $(PACKAGE)

run-stdio: ensure-uv
	SONIQ_MCP_TRANSPORT=stdio $(UV) run python -m $(PACKAGE)

test: ensure-uv
	$(UV) run pytest

check: ensure-uv
	$(UV) run python -m compileall src tests

tree:
	find src tests helm docs -maxdepth 3 | sort
