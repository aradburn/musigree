"""Unit tests for the container healthcheck script."""

from http.client import HTTPMessage
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from health import HEALTHCHECK_URL, main


def test_healthcheck_succeeds_when_application_is_ready() -> None:
    """A 200 response means startup has finished."""
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response
    response.__exit__.return_value = False

    with patch("health.urllib.request.urlopen", return_value=response) as urlopen:
        assert main() == 0

    assert urlopen.call_args.args[0].full_url == HEALTHCHECK_URL
    assert HEALTHCHECK_URL.startswith("http://127.0.0.1:")


def test_healthcheck_fails_while_application_is_starting() -> None:
    """HTTP 503 keeps the container unready until startup finishes."""
    error = HTTPError(
        HEALTHCHECK_URL,
        503,
        "Service Unavailable",
        HTTPMessage(),
        None,
    )

    with patch("health.urllib.request.urlopen", side_effect=error):
        assert main() == 1


def test_healthcheck_fails_when_the_port_is_not_accepting() -> None:
    """Connection failure means no worker has finished startup yet."""
    with patch(
        "health.urllib.request.urlopen",
        side_effect=URLError("connection refused"),
    ):
        assert main() == 1
