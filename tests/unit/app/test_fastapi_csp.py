"""
Unit tests for musigree.app.fastapi_csp module.
"""

import re
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.middleware import Middleware
from starlette.responses import HTMLResponse

from musigree.app.fastapi_csp import (
    CSP_NONCE_STATE_KEY,
    ContentSecurityPolicyMiddleware,
    render_content_security_policy,
    setup_csp_middleware,
)
from musigree.config import Configuration, SqliteTestConfiguration
from musigree.constants import TEMPLATES_DIR, AnalyticsType


def _csp_middleware(app: FastAPI) -> Middleware:
    """Return the CSP middleware registered on the application."""
    matches = [
        middleware
        for middleware in app.user_middleware
        if middleware.cls is ContentSecurityPolicyMiddleware
    ]
    assert len(matches) == 1
    return matches[0]


def _directive_sources(policy: str, directive: str) -> list[str]:
    """Return the source list for one CSP directive."""
    for part in policy.split(";"):
        tokens = part.strip().split()
        if tokens and tokens[0] == directive:
            return tokens[1:]
    raise AssertionError(f"{directive} not found in {policy}")


class TestCSPMiddleware:
    """Test cases for CSP middleware setup."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    def test_setup_csp_middleware_production(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup for production."""
        # Arrange
        app = FastAPI()
        test_config.PRODUCTION = True

        # Act
        setup_csp_middleware(app, test_config)

        # Assert
        middleware = _csp_middleware(app)
        assert middleware.kwargs["report_only"] is False
        assert "default-src" in middleware.kwargs["options"]
        assert "'unsafe-inline'" not in middleware.kwargs["options"]["script-src-elem"]

    def test_setup_csp_middleware_development(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup for development."""
        # Arrange
        app = FastAPI()
        test_config.PRODUCTION = False

        # Act
        setup_csp_middleware(app, test_config)

        # Assert
        middleware = _csp_middleware(app)
        assert middleware.kwargs["report_only"] is False
        assert "http://localhost:5173" in middleware.kwargs["options"]["script-src"]
        assert "'unsafe-inline'" not in middleware.kwargs["options"]["script-src-elem"]

    def test_setup_csp_middleware_analytics_umami(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup with Umami analytics."""
        # Arrange
        app = FastAPI()
        test_config.PRODUCTION = True
        test_config.ANALTICS_TYPE = AnalyticsType.UMAMI

        # Act
        setup_csp_middleware(app, test_config)

        # Assert
        csp_options = _csp_middleware(app).kwargs["options"]
        assert "https://umami.musigree.com " in csp_options["script-src"]
        assert "https://umami.musigree.com " in csp_options["connect-src"]

    def test_setup_csp_middleware_analytics_swetrix(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup with Swetrix analytics."""
        # Arrange
        app = FastAPI()
        test_config.PRODUCTION = True
        test_config.ANALTICS_TYPE = AnalyticsType.SWETRIX

        # Act
        setup_csp_middleware(app, test_config)

        # Assert
        csp_options = _csp_middleware(app).kwargs["options"]
        assert (
            "https://swetrix.org/swetrix.js https://cdn.jsdelivr.net/gh/Swetrix/ "
            in csp_options["script-src"]
        )
        assert "https://swetrix-api.musigree.com/ " in csp_options["connect-src"]

    def test_rendered_policy_adds_nonce_to_script_elements(
        self,
        test_config: Configuration,
    ) -> None:
        """Inline scripts are allowed by a nonce on script-src and script-src-elem."""
        # Arrange
        app = FastAPI()
        test_config.PRODUCTION = False
        setup_csp_middleware(app, test_config)
        options = _csp_middleware(app).kwargs["options"]

        # Act
        policy = render_content_security_policy(options, "abc123")

        # Assert
        assert "'nonce-abc123'" in _directive_sources(policy, "script-src")
        assert "'nonce-abc123'" in _directive_sources(policy, "script-src-elem")
        assert "'unsafe-inline'" not in _directive_sources(policy, "script-src-elem")
        assert "'unsafe-inline'" in _directive_sources(policy, "style-src-elem")

    def test_each_response_gets_a_distinct_nonce(
        self,
        test_config: Configuration,
    ) -> None:
        """The nonce in the CSP header matches the request and changes every response."""
        # Arrange
        app = FastAPI()
        setup_csp_middleware(app, test_config)

        @app.get("/")
        def index(request: Request) -> HTMLResponse:
            nonce = getattr(request.state, CSP_NONCE_STATE_KEY)
            return HTMLResponse(f'<script nonce="{nonce}"></script>')

        client = TestClient(app)

        # Act
        first = client.get("/")
        second = client.get("/")

        # Assert
        first_nonce = _nonce_from_policy(first.headers["content-security-policy"])
        second_nonce = _nonce_from_policy(second.headers["content-security-policy"])
        assert first_nonce != second_nonce
        assert f'nonce="{first_nonce}"' in first.text
        assert f'nonce="{second_nonce}"' in second.text


def _nonce_from_policy(policy: str) -> str:
    """Extract the nonce value from a serialized CSP policy."""
    match = re.search(r"'nonce-([^']+)'", policy)
    assert match is not None
    return match.group(1)


class TestIndexTemplateCsp:
    """Inline scripts in the index template must carry the request nonce."""

    def _render(self, *, is_production: bool, nonce: str) -> str:
        environment = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html", "xml"]),
        )
        environment.globals["asset"] = lambda file_path: f"/assets/{file_path}"
        environment.globals["is_production"] = is_production
        request = SimpleNamespace(state=SimpleNamespace(csp_nonce=nonce))
        return environment.get_template("index.html").render(
            request=request,
            title="Musigree",
            og_title="Musigree",
            og_type="website",
            og_image="/img/og_image.png",
            og_url="http://localhost:5000",
            initial_json="var dgNetwork = null;\n",
        )

    def test_development_template_has_no_inline_preamble(self) -> None:
        """The React refresh preamble is not an inline script."""
        html = self._render(is_production=False, nonce="dev-nonce")

        assert "RefreshRuntime" not in html
        assert "__vite_plugin_react_preamble_installed__" not in html
        assert 'nonce="dev-nonce"' in html
        assert "var dgNetwork = null;" in html

    def test_production_analytics_stub_uses_nonce(self) -> None:
        """The OpenPanel queue stub is an inline script allowed by the request nonce."""
        html = self._render(is_production=True, nonce="prod-nonce")

        assert 'nonce="prod-nonce"' in html
        assert "window.op" in html
