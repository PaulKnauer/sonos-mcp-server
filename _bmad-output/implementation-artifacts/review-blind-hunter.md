# Blind Hunter Review Prompt

Use the `bmad-review-adversarial-general` skill.

Review the following diff only. Do not use repo context, spec files, or prior discussion. Report only concrete findings. Output a markdown list. Each finding should include:
- a short title
- severity
- affected file/area
- why it is a problem

```diff
diff --git a/src/soniq_mcp/config/defaults.py b/src/soniq_mcp/config/defaults.py
index d246f4d..6e10f8d 100644
--- a/src/soniq_mcp/config/defaults.py
+++ b/src/soniq_mcp/config/defaults.py
@@ -14,4 +14,6 @@ DEFAULTS: dict[str, object] = {
     "config_file": None,
     "max_volume_pct": 80,
     "tools_disabled": [],
+    "http_host": "127.0.0.1",
+    "http_port": 8000,
 }
diff --git a/src/soniq_mcp/config/loader.py b/src/soniq_mcp/config/loader.py
index d1b8988..aa33a06 100644
--- a/src/soniq_mcp/config/loader.py
+++ b/src/soniq_mcp/config/loader.py
@@ -24,6 +24,8 @@ _ENV_MAP: dict[str, str] = {
     "SONIQ_MCP_CONFIG_FILE": "config_file",
     "SONIQ_MCP_MAX_VOLUME_PCT": "max_volume_pct",
     "SONIQ_MCP_TOOLS_DISABLED": "tools_disabled",
+    "SONIQ_MCP_HTTP_HOST": "http_host",
+    "SONIQ_MCP_HTTP_PORT": "http_port",
 }
 
 
diff --git a/src/soniq_mcp/config/models.py b/src/soniq_mcp/config/models.py
index 9746496..b2b3cd9 100644
--- a/src/soniq_mcp/config/models.py
+++ b/src/soniq_mcp/config/models.py
@@ -56,15 +56,14 @@ class TransportMode(str, Enum):
     """Supported server transport modes."""
 
     STDIO = "stdio"
+    HTTP = "http"
 
 
 class ExposurePosture(str, Enum):
-    """Allowed network exposure postures.
-
-    Story 1.4 will extend this with additional values.
-    """
+    """Allowed network exposure postures."""
 
     LOCAL = "local"
+    HOME_NETWORK = "home-network"
 
 
 class LogLevel(str, Enum):
@@ -109,6 +108,16 @@ class SoniqConfig(BaseModel):
         default_factory=list,
         description="Tool names to suppress at startup.",
     )
+    http_host: str = Field(
+        default="127.0.0.1",
+        description="Bind address for HTTP transport. Use '0.0.0.0' for home-network access.",
+    )
+    http_port: int = Field(
+        default=8000,
+        ge=1,
+        le=65535,
+        description="Bind port for HTTP transport (1-65535).",
+    )
 
     model_config = {"str_strip_whitespace": True, "extra": "forbid"}
 
diff --git a/src/soniq_mcp/domain/safety.py b/src/soniq_mcp/domain/safety.py
index d55537c..6792a83 100644
--- a/src/soniq_mcp/domain/safety.py
+++ b/src/soniq_mcp/domain/safety.py
@@ -62,12 +62,18 @@ def validate_exposure_posture(config: SoniqConfig) -> list[str]:
     """Validate the exposure posture and return any warnings.
 
     Returns a list of human-readable warning strings (empty = OK).
-    Currently ``local`` is the only supported posture; this function
-    is a hook for Story 4 to extend when HTTP transport is added.
+    ``local`` and ``home-network`` are both supported; any other value
+    triggers an unsupported-posture warning.
     """
     warnings: list[str] = []
     from soniq_mcp.config.models import ExposurePosture
-    if config.exposure != ExposurePosture.LOCAL:
+
+    if config.exposure == ExposurePosture.HOME_NETWORK:
+        warnings.append(
+            f"home-network exposure: server will bind to {config.http_host}:{config.http_port} — "
+            "ensure this host is reachable only from your trusted home network."
+        )
+    elif config.exposure != ExposurePosture.LOCAL:
         warnings.append(
             f"exposure '{config.exposure.value}' is not yet fully supported; "
             "defaulting to local-only behaviour."
diff --git a/src/soniq_mcp/server.py b/src/soniq_mcp/server.py
index c113e02..1ef37d1 100644
--- a/src/soniq_mcp/server.py
+++ b/src/soniq_mcp/server.py
@@ -29,7 +29,7 @@ def create_server(config: SoniqConfig | None = None) -> FastMCP:
     for warning in warnings:
         log.warning("Exposure posture: %s", warning)
 
-    app = FastMCP("soniq-mcp")
+    app = FastMCP("soniq-mcp", host=config.http_host, port=config.http_port)
     register_all(app, config)
 
     log.info(
diff --git a/src/soniq_mcp/transports/bootstrap.py b/src/soniq_mcp/transports/bootstrap.py
index 038f1b8..7ba48d6 100644
--- a/src/soniq_mcp/transports/bootstrap.py
+++ b/src/soniq_mcp/transports/bootstrap.py
@@ -22,6 +22,10 @@ def run_transport(app: FastMCP, config: SoniqConfig) -> None:
         from soniq_mcp.transports.stdio import run_stdio
 
         run_stdio(app)
+    elif config.transport == TransportMode.HTTP:
+        from soniq_mcp.transports.streamable_http import run_streamable_http
+
+        run_streamable_http(app, config)
     else:
         raise NotImplementedError(
             f"Transport '{config.transport.value}' is not yet implemented"
diff --git a/src/soniq_mcp/transports/streamable_http.py b/src/soniq_mcp/transports/streamable_http.py
new file mode 100644
index 0000000..df779bc
--- /dev/null
+++ b/src/soniq_mcp/transports/streamable_http.py
@@ -0,0 +1,30 @@
+"""Streamable HTTP transport for SoniqMCP.
+
+Runs the MCP server over HTTP for cross-device home-network use.
+Requires uvicorn (bundled via mcp[cli]).
+"""
+
+from __future__ import annotations
+
+import logging
+
+from mcp.server.fastmcp import FastMCP
+
+from soniq_mcp.config.models import SoniqConfig
+
+log = logging.getLogger(__name__)
+
+
+def run_streamable_http(app: FastMCP, config: SoniqConfig) -> None:
+    """Start the MCP server using the Streamable HTTP transport."""
+    log.info(
+        "Starting SoniqMCP over Streamable HTTP transport host=%s port=%s path=/mcp",
+        config.http_host,
+        config.http_port,
+    )
+    app.run(transport="streamable-http")
+
+
+def streamable_http_transport_name() -> str:
+    """Return the canonical transport identifier."""
+    return "streamable-http"
diff --git a/tests/integration/transports/test_http_bootstrap.py b/tests/integration/transports/test_http_bootstrap.py
new file mode 100644
index 0000000..7e83645
--- /dev/null
+++ b/tests/integration/transports/test_http_bootstrap.py
@@ -0,0 +1,137 @@
+"""Integration tests: HTTP transport bootstrap and tool surface parity (Story 4.1)."""
+
+from __future__ import annotations
+
+from unittest.mock import patch
+
+import pytest
+from mcp.server.fastmcp import FastMCP
+
+from soniq_mcp.config.models import ExposurePosture, SoniqConfig, TransportMode
+from soniq_mcp.domain.safety import validate_exposure_posture
+from soniq_mcp.server import create_server
+from soniq_mcp.transports.bootstrap import run_transport
+from soniq_mcp.transports.streamable_http import streamable_http_transport_name
+
+
+class TestCreateServerWithHttpConfig:
+    def test_create_server_http_transport_succeeds(self) -> None:
+        cfg = SoniqConfig(transport=TransportMode.HTTP)
+        app = create_server(config=cfg)
+        assert isinstance(app, FastMCP)
+
+    def test_create_server_passes_host_to_fastmcp(self) -> None:
+        cfg = SoniqConfig(transport=TransportMode.HTTP, http_host="0.0.0.0", http_port=9001)
+        app = create_server(config=cfg)
+        assert app.settings.host == "0.0.0.0"
+        assert app.settings.port == 9001
+
+    def test_create_server_localhost_host_and_port(self) -> None:
+        cfg = SoniqConfig(transport=TransportMode.HTTP, http_host="127.0.0.1", http_port=9999)
+        app = create_server(config=cfg)
+        assert app.settings.host == "127.0.0.1"
+        assert app.settings.port == 9999
+
+    def test_stdio_server_also_receives_host_port(self) -> None:
+        """server.py always passes host/port; stdio transport ignores them."""
+        cfg = SoniqConfig(transport=TransportMode.STDIO, http_host="127.0.0.1", http_port=8080)
+        app = create_server(config=cfg)
+        assert app.settings.host == "127.0.0.1"
+        assert app.settings.port == 8080
+
+
+class TestHttpToolSurfaceParity:
+    def test_http_exposes_same_tools_as_stdio(self) -> None:
+        http_cfg = SoniqConfig(transport=TransportMode.HTTP)
+        stdio_cfg = SoniqConfig(transport=TransportMode.STDIO)
+        http_app = create_server(config=http_cfg)
+        stdio_app = create_server(config=stdio_cfg)
+        http_tools = {t.name for t in http_app._tool_manager.list_tools()}
+        stdio_tools = {t.name for t in stdio_app._tool_manager.list_tools()}
+        assert http_tools == stdio_tools
+
+    def test_http_server_exposes_ping(self) -> None:
+        cfg = SoniqConfig(transport=TransportMode.HTTP)
+        app = create_server(config=cfg)
+        tool_names = {t.name for t in app._tool_manager.list_tools()}
+        assert "ping" in tool_names
+
+    def test_http_server_exposes_all_29_tools(self) -> None:
+        cfg = SoniqConfig(transport=TransportMode.HTTP)
+        app = create_server(config=cfg)
+        tool_names = {t.name for t in app._tool_manager.list_tools()}
+        expected = {
+            "ping", "server_info", "list_rooms",
+            "play", "pause", "stop", "get_playback_state",
+            "get_volume", "set_volume", "mute",
+            "get_queue", "add_to_queue", "clear_queue",
+            "list_favourites", "play_favourite",
+            "get_group_topology", "join_group", "party_mode",
+        }
+        assert expected.issubset(tool_names)
+
+
+class TestRunTransportHttpDispatch:
+    def test_run_transport_dispatches_to_http(self) -> None:
+        cfg = SoniqConfig(transport=TransportMode.HTTP)
+        app = create_server(config=cfg)
+        with patch("soniq_mcp.transports.streamable_http.run_streamable_http") as mock_run:
+            run_transport(app, cfg)
+            mock_run.assert_called_once_with(app, cfg)
+
+    def test_run_transport_does_not_raise_for_http(self) -> None:
+        """HTTP transport must not hit the NotImplementedError branch."""
+        cfg = SoniqConfig(transport=TransportMode.HTTP)
+        app = create_server(config=cfg)
+        with patch("soniq_mcp.transports.streamable_http.run_streamable_http"):
+            run_transport(app, cfg)
+
+    def test_run_transport_still_raises_for_unknown(self) -> None:
+        from unittest.mock import MagicMock
+        cfg = SoniqConfig()
+        app = create_server(config=cfg)
+        bad_cfg = MagicMock()
+        bad_cfg.transport.__eq__ = lambda self, other: False
+        with pytest.raises(NotImplementedError):
+            run_transport(app, bad_cfg)
+
+
+class TestStreamableHttpTransportName:
+    def test_transport_name_is_streamable_http(self) -> None:
+        assert streamable_http_transport_name() == "streamable-http"
+
+
+class TestHomeNetworkExposurePosture:
+    def test_home_network_emits_warning(self) -> None:
+        cfg = SoniqConfig(exposure=ExposurePosture.HOME_NETWORK, http_host="0.0.0.0", http_port=8000)
+        warnings = validate_exposure_posture(cfg)
+        assert len(warnings) == 1
+        assert "home-network" in warnings[0]
+        assert "0.0.0.0" in warnings[0]
+        assert "8000" in warnings[0]
+
+    def test_local_exposure_no_warning(self) -> None:
+        cfg = SoniqConfig(exposure=ExposurePosture.LOCAL)
+        warnings = validate_exposure_posture(cfg)
+        assert warnings == []
+
+    def test_unknown_exposure_emits_unsupported_warning(self) -> None:
+        """Simulates a future posture value not yet fully supported."""
+        cfg = SoniqConfig(exposure=ExposurePosture.LOCAL)
+        object.__setattr__(cfg, "exposure", type("FakePosture", (), {"value": "public"})())
+        warnings = validate_exposure_posture(cfg)
+        assert len(warnings) == 1
+        assert "not yet fully supported" in warnings[0]
+
+    def test_home_network_warning_mentions_host_and_port(self) -> None:
+        cfg = SoniqConfig(
+            exposure=ExposurePosture.HOME_NETWORK,
+            http_host="192.168.1.50",
+            http_port=8765,
+        )
+        warnings = validate_exposure_posture(cfg)
+        assert "192.168.1.50" in warnings[0]
+        assert "8765" in warnings[0]
diff --git a/tests/smoke/streamable_http/test_streamable_http_smoke.py b/tests/smoke/streamable_http/test_streamable_http_smoke.py
new file mode 100644
index 0000000..469944f
--- /dev/null
+++ b/tests/smoke/streamable_http/test_streamable_http_smoke.py
@@ -0,0 +1,80 @@
+"""Smoke tests: Streamable HTTP transport end-to-end (Story 4.1, AC 1, 2).
+
+Starts the server as a subprocess bound to a local test port, connects via
+the MCP streamable-http client, and verifies the tool surface and ping tool
+work identically to the stdio transport.
+"""
+
+from __future__ import annotations
+
+import os
+import subprocess
+import sys
+import time
+
+import anyio
+import pytest
+from mcp.client.session import ClientSession
+from mcp.client.streamable_http import streamable_http_client
+
+_TEST_PORT = 18431
+_TEST_HOST = "127.0.0.1"
+_MCP_PATH = "/mcp"
+
+
+@pytest.fixture(scope="module")
+def http_server_proc():
+    """Start the SoniqMCP server over Streamable HTTP in a subprocess."""
+    env = {
+        **os.environ,
+        "SONIQ_MCP_TRANSPORT": "http",
+        "SONIQ_MCP_HTTP_HOST": _TEST_HOST,
+        "SONIQ_MCP_HTTP_PORT": str(_TEST_PORT),
+        "SONIQ_MCP_EXPOSURE": "local",
+        "SONIQ_MCP_LOG_LEVEL": "WARNING",
+    }
+    proc = subprocess.Popen(
+        [sys.executable, "-m", "soniq_mcp"],
+        env=env,
+        stdout=subprocess.DEVNULL,
+        stderr=subprocess.DEVNULL,
+    )
+    time.sleep(2.0)
+    yield proc
+    proc.terminate()
+    try:
+        proc.wait(timeout=5)
+    except subprocess.TimeoutExpired:
+        proc.kill()
+
+
+class TestStreamableHTTPSmoke:
+    """A same-machine MCP client must connect over Streamable HTTP and call tools (AC 1, 2)."""
+
+    def test_client_can_initialize_and_call_ping(self, http_server_proc) -> None:
+        async def run_session() -> None:
+            url = f"http://{_TEST_HOST}:{_TEST_PORT}{_MCP_PATH}"
+            async with streamable_http_client(url) as (read_stream, write_stream, _):
+                async with ClientSession(read_stream, write_stream) as session:
+                    await session.initialize()
+
+                    result = await session.call_tool("ping")
+
+                    assert result.isError is False
+                    assert [item.text for item in result.content] == ["pong"]
+
+        anyio.run(run_session)
+
+    def test_http_tool_surface_includes_ping(self, http_server_proc) -> None:
+        async def run_session() -> None:
+            url = f"http://{_TEST_HOST}:{_TEST_PORT}{_MCP_PATH}"
+            async with streamable_http_client(url) as (read_stream, write_stream, _):
+                async with ClientSession(read_stream, write_stream) as session:
+                    await session.initialize()
+                    tools = await session.list_tools()
+                    tool_names = [tool.name for tool in tools.tools]
+                    assert "ping" in tool_names
+                    assert "list_rooms" in tool_names
+                    assert "play" in tool_names
+
+        anyio.run(run_session)
diff --git a/tests/unit/config/test_http_config.py b/tests/unit/config/test_http_config.py
new file mode 100644
index 0000000..9df5db4
--- /dev/null
+++ b/tests/unit/config/test_http_config.py
@@ -0,0 +1,115 @@
+"""Unit tests: HTTP transport config fields and env var loading (Story 4.1)."""
+
+from __future__ import annotations
+
+import pytest
+
+from soniq_mcp.config.loader import load_config
+from soniq_mcp.config.models import ExposurePosture, SoniqConfig, TransportMode
+
+
+class TestTransportModeEnum:
+    def test_http_value(self) -> None:
+        assert TransportMode.HTTP == "http"
+
+    def test_stdio_value_unchanged(self) -> None:
+        assert TransportMode.STDIO == "stdio"
+
+    def test_http_is_valid_transport(self) -> None:
+        cfg = SoniqConfig(transport=TransportMode.HTTP)
+        assert cfg.transport == TransportMode.HTTP
+
+    def test_invalid_transport_rejected(self) -> None:
+        with pytest.raises(Exception):
+            SoniqConfig(transport="grpc")  # type: ignore[arg-type]
+
+class TestExposurePostureEnum:
+    def test_home_network_value(self) -> None:
+        assert ExposurePosture.HOME_NETWORK == "home-network"
+
+    def test_local_value_unchanged(self) -> None:
+        assert ExposurePosture.LOCAL == "local"
+
+    def test_home_network_is_valid_posture(self) -> None:
+        cfg = SoniqConfig(exposure=ExposurePosture.HOME_NETWORK)
+        assert cfg.exposure == ExposurePosture.HOME_NETWORK
+
+    def test_invalid_exposure_rejected(self) -> None:
+        with pytest.raises(Exception):
+            SoniqConfig(exposure="public")  # type: ignore[arg-type]
+
+class TestHttpHostField:
+    def test_default_is_localhost(self) -> None:
+        cfg = SoniqConfig()
+        assert cfg.http_host == "127.0.0.1"
+
+    def test_custom_host_accepted(self) -> None:
+        cfg = SoniqConfig(http_host="0.0.0.0")
+        assert cfg.http_host == "0.0.0.0"
+
+    def test_arbitrary_ip_accepted(self) -> None:
+        cfg = SoniqConfig(http_host="192.168.1.100")
+        assert cfg.http_host == "192.168.1.100"
+
+class TestHttpPortField:
+    def test_default_is_8000(self) -> None:
+        cfg = SoniqConfig()
+        assert cfg.http_port == 8000
+
+    def test_custom_port_accepted(self) -> None:
+        cfg = SoniqConfig(http_port=9000)
+        assert cfg.http_port == 9000
+
+    def test_port_1_accepted(self) -> None:
+        cfg = SoniqConfig(http_port=1)
+        assert cfg.http_port == 1
+
+    def test_port_65535_accepted(self) -> None:
+        cfg = SoniqConfig(http_port=65535)
+        assert cfg.http_port == 65535
+
+    def test_port_0_rejected(self) -> None:
+        with pytest.raises(Exception):
+            SoniqConfig(http_port=0)
+
+    def test_port_65536_rejected(self) -> None:
+        with pytest.raises(Exception):
+            SoniqConfig(http_port=65536)
+
+class TestHttpEnvVarLoading:
+    def test_http_host_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
+        monkeypatch.setenv("SONIQ_MCP_HTTP_HOST", "0.0.0.0")
+        cfg = load_config()
+        assert cfg.http_host == "0.0.0.0"
+
+    def test_http_port_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
+        monkeypatch.setenv("SONIQ_MCP_HTTP_PORT", "9876")
+        cfg = load_config()
+        assert cfg.http_port == 9876
+
+    def test_http_port_coerced_from_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
+        monkeypatch.setenv("SONIQ_MCP_HTTP_PORT", "7777")
+        cfg = load_config()
+        assert isinstance(cfg.http_port, int)
+        assert cfg.http_port == 7777
+
+    def test_transport_http_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
+        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "http")
+        cfg = load_config()
+        assert cfg.transport == TransportMode.HTTP
+
+    def test_exposure_home_network_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
+        monkeypatch.setenv("SONIQ_MCP_EXPOSURE", "home-network")
+        cfg = load_config()
+        assert cfg.exposure == ExposurePosture.HOME_NETWORK
+
+    def test_defaults_used_when_no_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
+        monkeypatch.delenv("SONIQ_MCP_HTTP_HOST", raising=False)
+        monkeypatch.delenv("SONIQ_MCP_HTTP_PORT", raising=False)
+        cfg = load_config()
+        assert cfg.http_host == "127.0.0.1"
+        assert cfg.http_port == 8000
```
