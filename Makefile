UV ?= uv
PACKAGE ?= soniq_mcp

.PHONY: install run run-stdio test check tree

install:
	$(UV) sync

# Run the server locally over stdio (primary local transport)
run:
	$(UV) run python -m $(PACKAGE)

run-stdio:
	SONIQ_MCP_TRANSPORT=stdio $(UV) run python -m $(PACKAGE)

test:
	$(UV) run pytest

check:
	$(UV) run python -m compileall src tests

tree:
	find src tests helm docs -maxdepth 3 | sort
