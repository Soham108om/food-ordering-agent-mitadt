import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mcp.client import format_mcp_error


class WrappedTaskError(Exception):
    def __init__(self, *exceptions):
        super().__init__("unhandled errors in a TaskGroup")
        self.exceptions = exceptions


def test_format_mcp_error_includes_nested_http_status():
    inner_error = RuntimeError(
        "Client error '429 Too Many Requests' for url 'https://mcp.swiggy.com/food'"
    )
    error = WrappedTaskError(inner_error)

    assert "429 Too Many Requests" in format_mcp_error(error)
    assert "TaskGroup" not in format_mcp_error(error)


def test_format_mcp_error_reports_multiple_nested_causes():
    error = WrappedTaskError(
        RuntimeError("connection refused"),
        TimeoutError("request timed out")
    )

    detail = format_mcp_error(error)

    assert "connection refused" in detail
    assert "request timed out" in detail
