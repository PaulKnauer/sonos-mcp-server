UV ?= uv
PACKAGE ?= soniq_mcp

.PHONY: install run test check tree

install:
	$(UV) sync

run:
	$(UV) run python -m $(PACKAGE)

test:
	$(UV) run pytest

check:
	$(UV) run python -m compileall src tests

tree:
	find src tests helm docs -maxdepth 3 | sort
