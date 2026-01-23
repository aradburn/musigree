"""
Security middleware and utilities for the Musigree FastAPI application.

This module provides security-related middleware and functions to enhance
the security posture of the application, including security headers,
rate limiting enhancements, and other security best practices.
"""

import logging
import sys
from typing import Union, TYPE_CHECKING

from fastapi import FastAPI
from starlette.types import ASGIApp, Scope, Receive, Send, Message

from musigree.config import Configuration
from musigree.constants import AnalyticsType, CSPSetting

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    ASGI middleware to add security headers to all responses.

    This middleware adds various security headers to protect against
    common web vulnerabilities such as XSS, clickjacking, and MIME
    type sniffing attacks.
    """

    def __init__(
        self,
        app: ASGIApp,
        is_production: bool = False,
        analytics_script_url: str = "",
        analytics_api_url: str = "",
    ):
        self.app = app
        self.is_production = is_production
        self.analytics_script_url = analytics_script_url
        self.analytics_api_url = analytics_api_url

        # Setup CSP headers
        self.content_security_policy_report_only = (
            "frame-ancestors 'self';"
            + "block-all-mixed-content;"
            + "default-src 'self';"
            + "script-src 'self';"
            + "style-src 'self';"
            + "object-src 'none';"
            + "frame-src 'self';"
            + "child-src 'self';"
            + "img-src 'self';"
            + "font-src 'self';"
            + "connect-src 'self';"
            + "manifest-src 'self';"
            + "base-uri 'self';"
            + "form-action 'self';"
            + "media-src 'self';"
            + "prefetch-src 'self';"
            + "worker-src 'self';"
        ).encode("utf-8")
        self.content_security_policy_report_secure = (
            "frame-ancestors 'self';"
            + "default-src 'self';"
            + "script-src 'self' data: http://localhost:5173 "
            + self.analytics_script_url
            + ";"
            + "script-src-elem 'self' data: http://localhost:5173 http://localhost:5173/assets/@vite/client "
            + self.analytics_script_url
            + ";"
            + "style-src 'self' http://localhost:5173 ;"
            + "style-src-elem 'self' 'unsafe-inline' http://localhost:5173 ;"
            + "object-src 'none';"
            + "frame-src 'self';"
            + "child-src 'self';"
            + "img-src 'self' data: "
            + self.analytics_api_url
            + ";"
            + "font-src 'self';"
            + "connect-src 'self' ws://localhost:5173/assets/ "
            + self.analytics_api_url
            + ";"
            + "manifest-src 'self';"
            + "base-uri 'self';"
            + "form-action 'self';"
            + "media-src 'self' data:;"
            + "worker-src 'self';"
        ).encode("utf-8")
        self.content_security_policy_production = (
            "frame-ancestors 'self';"
            + "default-src 'self';"
            +
            # Need to remove 'unsafe-inline'
            "script-src 'self' 'unsafe-inline' "
            + self.analytics_script_url
            + ";"
            +
            # Need to remove 'unsafe-hashes'
            "style-src 'self' 'unsafe-inline' 'unsafe-hashes';"
            + "object-src 'none';"
            + "frame-src 'self';"
            + "child-src 'self';"
            + "img-src 'self' data: "
            + self.analytics_api_url
            + ";"
            + "font-src 'self';"
            + "connect-src 'self' "
            + self.analytics_api_url
            + ";"
            + "manifest-src 'self';"
            + "base-uri 'self';"
            + "form-action 'self';"
            + "media-src 'self' data:;"
            + "worker-src 'self';"
        ).encode("utf-8")
        self.content_security_policy_development = (
            "frame-ancestors 'self';"
            + "default-src 'self';"
            +
            # was "default-src 'self' 'unsafe-inline' 'unsafe-eval' data:; " +
            "script-src      'self' data:                 http://localhost:5173 http://localhost:5173/assets/@vite/client "
            + self.analytics_script_url
            + ";"
            + "script-src-elem 'self' data: 'unsafe-inline' http://localhost:5173 http://localhost:5173/assets/@vite/client "
            + self.analytics_script_url
            + ";"
            + "style-src      'self'                 http://localhost:5173 ;"
            + "style-src-elem 'self' 'unsafe-inline' http://localhost:5173 ;"
            + "object-src 'none';"
            + "frame-src 'self';"
            + "child-src 'self';"
            + "img-src 'self' data: http://localhost:5173 "
            + self.analytics_api_url
            + ";"
            + "font-src 'self';"
            + "connect-src 'self' http://localhost:5173/assets/ ws://localhost:5173/assets/ "
            + self.analytics_api_url
            + ";"
            + "manifest-src 'self';"
            + "base-uri 'self';"
            + "form-action 'self';"
            + "media-src 'self' data:;"
            + "worker-src 'self';"
            # "style-src 'self' 'unsafe-inline' ;" +
            # "img-src 'self' data: https: http://localhost:5173 " + self.analytics_api_url + ";" +
            # "font-src 'self';" +
            # "connect-src 'self' http://localhost:5173 ws://localhost:5173/assests/ " + self.analytics_api_url + ";" +
        ).encode("utf-8")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        ASGI callable that processes HTTP requests and adds security headers.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            # Pass through non-HTTP requests
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                # Add security headers to the response
                headers: dict[Union[str, bytes], Union[str, bytes]] = dict(
                    message.get("headers", [])
                )

                # Define security headers
                security_headers: dict[bytes, bytes] = {
                    # Prevent MIME type sniffing
                    b"x-content-type-options": b"nosniff",
                    # TODO Cross Origin Resource Policy - See fastapi_app.py for CORS setup
                    # b"cross-origin-embedder-policy": b"require-corp",
                    # b"cross-origin-opener-policy": b"same-origin",
                    # b"cross-origin-resource-policy": b"same-origin",
                    # Prevent clickjacking
                    b"x-frame-options": b"DENY",
                    # Enable XSS protection
                    b"x-xss-protection": b"1; mode=block",
                    # Referrer policy
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    # Privacy and anti-tracking headers
                    b"sec-gpc": b"1",
                    b"dnt": b"1",
                    # Permissions policy (previously Feature-Policy)
                    b"permissions-policy": b"geolocation=(), camera=(), microphone=(), interest-cohort=(), "
                    b"accelerometer=(), gyroscope=(), magnetometer=(), usb=(), "
                    b"screen-wake-lock=(), payment=()",
                }

                if self.is_production:
                    # Add HSTS header for production HTTPS
                    security_headers[b"strict-transport-security"] = (
                        b"max-age=31536000; includeSubDomains; preload"
                    )

                    production_csp_setting = CSPSetting.ENFORCE_CSP
                    # noinspection PyUnreachableCode
                    match production_csp_setting:
                        case CSPSetting.REPORT_ONLY:
                            log.info("CSP Report Only")
                            # Report Only Content Security Policy for production
                            # - use to report what is being prevented by CSP policy
                            security_headers[b"content-security-policy-report-only"] = (
                                self.content_security_policy_report_only
                            )
                        case CSPSetting.REPORT_SECURE:
                            log.info("CSP Report Secure")
                            security_headers[b"content-security-policy-report-only"] = (
                                self.content_security_policy_report_secure
                            )
                        case CSPSetting.ENFORCE_CSP:
                            security_headers[b"content-security-policy"] = (
                                self.content_security_policy_production
                            )
                        case _:
                            log.error("CSP Production Security Headers Not Set")
                            sys.exit("CSP Production Security Headers Not Set")

                else:
                    development_csp_setting = CSPSetting.ENFORCE_CSP
                    # noinspection PyUnreachableCode
                    match development_csp_setting:
                        case CSPSetting.REPORT_ONLY:
                            log.info("CSP Report Only")
                            # Report Only Content Security Policy for production
                            # - use to report what is being prevented by CSP policy
                            security_headers[b"content-security-policy-report-only"] = (
                                self.content_security_policy_report_only
                            )
                        case CSPSetting.REPORT_SECURE:
                            log.info("CSP Report Secure")
                            security_headers[b"content-security-policy-report-only"] = (
                                self.content_security_policy_report_secure
                            )
                        case CSPSetting.ENFORCE_CSP:
                            security_headers[b"content-security-policy"] = (
                                self.content_security_policy_development
                            )
                        case _:
                            log.error("CSP Development Security Headers Not Set")
                            sys.exit("CSP Development Security Headers Not Set")

                # Merge security headers with existing headers
                for header_name, header_value in security_headers.items():
                    headers[header_name] = header_value

                # Update message headers (convert back to list of byte tuples)
                message["headers"] = [
                    (
                        name.encode() if isinstance(name, str) else name,
                        value.encode() if isinstance(value, str) else value,
                    )
                    for name, value in headers.items()
                ]

            await send(message)

        await self.app(scope, receive, send_wrapper)


def validate_environment_variables(config: Configuration) -> None:
    """
    Validate that required environment variables are set for production.

    Args:
        config: The application configuration object

    Raises:
        ValueError: If required environment variables are missing in production
    """
    if not config.PRODUCTION:
        return

    missing_vars = []

    if config.DATABASE.value == "postgres":
        required_postgres_vars = [
            ("POSTGRES_DATABASE_USERNAME", config.POSTGRES_DATABASE_USERNAME),
            ("POSTGRES_DATABASE_PASSWORD", config.POSTGRES_DATABASE_PASSWORD),
            ("POSTGRES_DATABASE_HOST", config.POSTGRES_DATABASE_HOST),
            ("POSTGRES_DATABASE_PORT", config.POSTGRES_DATABASE_PORT),
            ("POSTGRES_OFFLINE_DATABASE_NAME", config.POSTGRES_OFFLINE_DATABASE_NAME),
        ]

        for var_name, var_value in required_postgres_vars:
            if not var_value:
                missing_vars.append(var_name)

    if missing_vars:
        raise ValueError(
            f"Required environment variables for production are missing: {', '.join(missing_vars)}"
        )


def setup_security_middleware(app: FastAPI, config: Configuration) -> None:
    """
    Set up security middleware for the FastAPI application.

    Args:
        app: The FastAPI application instance
        config: The application configuration object
    """
    # Validate environment variables for production
    validate_environment_variables(config)

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

    # Add security headers middleware
    # noinspection PyTypeChecker
    app.add_middleware(
        SecurityHeadersMiddleware,
        is_production=config.PRODUCTION,
        analytics_script_url=analytics_script_url,
        analytics_api_url=analytics_api_url,
    )

    log.info(
        f"Security middleware configured for {'production' if config.PRODUCTION else 'development'} environment"
    )
