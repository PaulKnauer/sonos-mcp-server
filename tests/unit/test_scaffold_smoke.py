from soniq_mcp.server import create_application
from soniq_mcp.transports.bootstrap import bootstrap_transport


def test_create_application_returns_placeholder_metadata() -> None:
    app = create_application()

    assert app["name"] == "soniq_mcp"
    assert app["transport"] == "stdio"


def test_bootstrap_transport_uses_stdio_placeholder() -> None:
    assert bootstrap_transport() == "stdio"
