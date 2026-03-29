UV ?= $(shell command -v uv 2>/dev/null || printf '%s' "$(HOME)/.local/bin/uv")
PACKAGE ?= soniq_mcp
IMAGE ?= soniq-mcp
TAG ?= local

.PHONY: ensure-uv install run run-stdio test check tree lint format type-check coverage audit build-check ci docker-build docker-run docker-compose-up docker-compose-down helm-lint helm-template helm-install

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

lint: ensure-uv
	$(UV) run ruff check src tests
	$(UV) run ruff format --check src tests

format: ensure-uv
	$(UV) run ruff format src tests
	$(UV) run ruff check --fix src tests

type-check: ensure-uv
	$(UV) run mypy src

coverage: ensure-uv
	$(UV) run pytest --cov --cov-report=term-missing

audit: ensure-uv
	# CVE-2026-4539 (pygments) has no fix release; ignored until upstream patch lands
	$(UV) run pip-audit --ignore-vuln CVE-2026-4539

build-check: ensure-uv
	$(UV) build

ci: lint type-check coverage audit build-check

docker-build:
	docker build -t $(IMAGE):$(TAG) .

docker-run:
	docker run --rm -p 8000:8000 \
		-e SONIQ_MCP_TRANSPORT=http \
		-e SONIQ_MCP_HTTP_HOST=0.0.0.0 \
		-e SONIQ_MCP_HTTP_PORT=8000 \
		-e SONIQ_MCP_EXPOSURE=home-network \
		$(IMAGE):$(TAG)

docker-compose-up:
	docker compose up --build -d

docker-compose-down:
	docker compose down

helm-lint:
	helm lint helm/soniq

helm-template:
	helm template soniq helm/soniq

helm-install:
	helm upgrade --install soniq helm/soniq
