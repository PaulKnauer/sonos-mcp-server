ARG BASE_IMAGE=python:3.12-slim
FROM $BASE_IMAGE

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install local package
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# Default environment for containerised deployment
ENV SONIQ_MCP_TRANSPORT=http
ENV SONIQ_MCP_HTTP_HOST=0.0.0.0
ENV SONIQ_MCP_HTTP_PORT=8000
ENV SONIQ_MCP_EXPOSURE=home-network

EXPOSE 8000

CMD ["/app/.venv/bin/python", "-m", "soniq_mcp"]
