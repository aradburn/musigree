from __future__ import annotations

import logging
import secrets
import sys
from typing import TYPE_CHECKING

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from musigree.app.fastapi_middleware import add_app_middleware
from musigree.config import Configuration
from musigree.constants import AnalyticsType, CSPSetting

if TYPE_CHECKING:
    # noinspection protected-member
    from Secweb._types import Content_Security_Policy_Options

log = logging.getLogger(__name__)

# 128 bits, the minimum recommended for a CSP nonce.
_CSP_NONCE_BYTES = 16
CSP_NONCE_STATE_KEY = "csp_nonce"
_NONCE_DIRECTIVES = frozenset({"script-src", "script-src-elem"})


def get_content_security_policy_report_only() -> Content_Security_Policy_Options:
    # Setup CSP headers
    csp: Content_Security_Policy_Options = {
        "frame-ancestors": ["'self'"],
        "block-all-mixed-content": [],
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'"],
        "object-src": ["'none'"],
        "frame-src": ["'self'"],
        "child-src": ["'self'"],
        "img-src": ["'self'"],
        "font-src": ["'self'"],
        "connect-src": ["'self'"],
        "manifest-src": ["'self'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "media-src": ["'self'"],
        "worker-src": ["'self'"],
    }
    return csp


def get_content_security_policy_production(
    analytics_script_url: str, analytics_api_url: str
) -> Content_Security_Policy_Options:
    # Setup CSP headers
    csp: Content_Security_Policy_Options = {
        "frame-ancestors": ["'self'"],
        "default-src": ["'none'"],
        "script-src": [
            "'self'",
            # "data:",
            analytics_script_url,
        ],
        # Inline scripts are allowed per response by a nonce, not 'unsafe-inline'.
        "script-src-elem": [
            "'self'",
            # "data:",
            analytics_script_url,
        ],
        "style-src": [
            "'self'",
        ],
        "style-src-elem": [
            "'self'",
            "'unsafe-inline'",
        ],
        "object-src": ["'none'"],
        "frame-src": ["'self'"],
        "child-src": ["'self'"],
        "img-src": [
            "'self'",
            "data:",
            analytics_api_url,
        ],
        "font-src": ["'self'"],
        "connect-src": [
            "'self'",
            analytics_api_url,
        ],
        "manifest-src": ["'self'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "media-src": ["'self'", "data:"],
        "worker-src": ["'self'"],
    }
    return csp


def get_content_security_policy_development(
    analytics_script_url: str, analytics_api_url: str
) -> Content_Security_Policy_Options:
    # Setup CSP headers
    csp: Content_Security_Policy_Options = {
        "frame-ancestors": ["'self'"],
        "default-src": ["'none'"],
        "script-src": [
            "'self'",
            # "data:",
            "http://localhost:5173",
            "http://localhost:5173/assets/@vite/client",
            analytics_script_url,
        ],
        "script-src-elem": [
            "'self'",
            # "data:",
            "http://localhost:5173",
            "http://localhost:5173/assets/@vite/client",
            analytics_script_url,
        ],
        "style-src": [
            "'self'",
            "http://localhost:5173",
        ],
        "style-src-elem": [
            "'self'",
            "'unsafe-inline'",
            "http://localhost:5173",
        ],
        "object-src": ["'none'"],
        "frame-src": ["'self'"],
        "child-src": ["'self'"],
        "img-src": [
            "'self'",
            "data:",
            "http://localhost:5173",
            analytics_api_url,
        ],
        "font-src": ["'self'"],
        "connect-src": [
            "'self'",
            "http://localhost:5173/assets/",
            "ws://localhost:5173/assets/",
            analytics_api_url,
        ],
        "manifest-src": ["'self'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "media-src": ["'self'", "data:"],
        "worker-src": ["'self'"],
    }
    return csp


def render_content_security_policy(
    options: Content_Security_Policy_Options,
    nonce: str,
) -> str:
    """Serialize a CSP policy, allowing this response's inline scripts by nonce.

    ``script-src-elem`` overrides ``script-src`` for ``<script>`` elements, so the
    nonce has to be present on both directives.
    """
    nonce_source = f"'nonce-{nonce}'"
    parts: list[str] = []
    for directive, values in options.items():
        if isinstance(values, list):
            sources = [str(value) for value in values]
        else:
            sources = [str(values)]
        if directive in _NONCE_DIRECTIVES:
            sources.append(nonce_source)
        if sources:
            parts.append(f"{directive} {' '.join(sources)}")
        else:
            parts.append(directive)
    return "; ".join(parts)


class ContentSecurityPolicyMiddleware:
    """Set a per-request CSP nonce and emit the matching Content-Security-Policy header."""

    def __init__(
        self,
        app: ASGIApp,
        options: Content_Security_Policy_Options,
        report_only: bool = False,
    ) -> None:
        self.app = app
        self.options = options
        self._header_name = (
            b"Content-Security-Policy-Report-Only" if report_only else b"Content-Security-Policy"
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        nonce = secrets.token_urlsafe(_CSP_NONCE_BYTES)
        if "state" not in scope:
            scope["state"] = {}
        scope["state"][CSP_NONCE_STATE_KEY] = nonce
        policy = render_content_security_policy(self.options, nonce).encode("latin-1")

        async def send_with_csp(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self._header_name, policy))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_csp)


def setup_csp_middleware(app: FastAPI, config: Configuration) -> None:
    """
    Set up CSP security middleware for the FastAPI application.

    Args:
        app: The FastAPI application instance
        config: The application configuration object
    """
    analytics_script_url = ""
    analytics_api_url = ""

    match config.ANALTICS_TYPE:
        case AnalyticsType.UMAMI:
            analytics_script_url = "https://umami.musigree.com "
            analytics_api_url = "https://umami.musigree.com "
        case AnalyticsType.SWETRIX:
            analytics_script_url = (
                "https://swetrix.org/swetrix.js https://cdn.jsdelivr.net/gh/Swetrix/ "
            )
            analytics_api_url = "https://swetrix-api.musigree.com/ "
        case AnalyticsType.OPENPANEL:
            analytics_script_url = "https://openpanel.dev/op1.js "
            analytics_api_url = "https://opapi.musigree.com/ "

    is_report_only = False
    content_security_policy_options: Content_Security_Policy_Options = (
        get_content_security_policy_production(
            analytics_script_url=analytics_script_url, analytics_api_url=analytics_api_url
        )
    )

    if config.PRODUCTION:
        production_csp_setting = CSPSetting.ENFORCE_CSP
        # noinspection PyUnreachableCode
        match production_csp_setting:
            case CSPSetting.REPORT_ONLY:
                log.info("CSP Report Only")
                # Report Only Content Security Policy for production
                # - use to report what is being prevented by CSP policy
                is_report_only = True
                content_security_policy_options = get_content_security_policy_report_only()
            case CSPSetting.REPORT_SECURE:
                log.info("CSP Report Secure")
                is_report_only = True
                content_security_policy_options = get_content_security_policy_production(
                    analytics_script_url=analytics_script_url, analytics_api_url=analytics_api_url
                )
            case CSPSetting.ENFORCE_CSP:
                log.info("Enforcing Production CSP")
                is_report_only = False
                content_security_policy_options = get_content_security_policy_production(
                    analytics_script_url=analytics_script_url, analytics_api_url=analytics_api_url
                )
            case _:
                content_security_policy_options = get_content_security_policy_report_only()
                log.error("CSP Production Security Headers Not Set")
                sys.exit("CSP Production Security Headers Not Set")

    else:
        development_csp_setting = CSPSetting.ENFORCE_CSP
        # noinspection PyUnreachableCode
        match development_csp_setting:
            case CSPSetting.REPORT_ONLY:
                log.info("CSP Report Only")
                is_report_only = True
                # Report Only Content Security Policy for production
                content_security_policy_options = get_content_security_policy_report_only()
            case CSPSetting.REPORT_SECURE:
                log.info("CSP Report Secure")
                is_report_only = True
                content_security_policy_options = get_content_security_policy_development(
                    analytics_script_url=analytics_script_url, analytics_api_url=analytics_api_url
                )
            case CSPSetting.ENFORCE_CSP:
                log.info("Enforcing Development CSP")
                is_report_only = False
                content_security_policy_options = get_content_security_policy_development(
                    analytics_script_url=analytics_script_url, analytics_api_url=analytics_api_url
                )
            case _:
                content_security_policy_options = get_content_security_policy_report_only()
                log.error("CSP Development Security Headers Not Set")
                sys.exit("CSP Development Security Headers Not Set")

    # Secweb 2.0 requires a reporting endpoint when CSP is report-only.
    if (
        is_report_only
        and "report-to" not in content_security_policy_options
        and "report-uri" not in content_security_policy_options
    ):
        content_security_policy_options["report-uri"] = ["/csp-report"]

    # Secweb only attaches a nonce to script-src, and it stores that nonce in a
    # process-global that is not safe under concurrent requests. script-src-elem
    # is what governs <script> elements, so the nonce is applied here instead.
    add_app_middleware(
        app,
        ContentSecurityPolicyMiddleware,
        options=content_security_policy_options,
        report_only=is_report_only,
    )

    log.info(
        f"Security middleware configured for {'production' if config.PRODUCTION else 'development'} environment"
    )
