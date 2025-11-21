"""
Security middleware and utilities for the Musigree FastAPI application.

This module provides security-related middleware and functions to enhance
the security posture of the application, including security headers,
rate limiting enhancements, and other security best practices.
"""

import logging
import sys
from enum import Enum
from typing import Union, TYPE_CHECKING

from fastapi import FastAPI
from starlette.types import ASGIApp, Scope, Receive, Send, Message

from musigree.config import Configuration

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


class ProductionCSPSetting(Enum):
    REPORT_ONLY = 1
    REPORT_SECURE = 2
    PRODUCTION = 3


class SecurityHeadersMiddleware:
    """
    ASGI middleware to add security headers to all responses.

    This middleware adds various security headers to protect against
    common web vulnerabilities such as XSS, clickjacking, and MIME
    type sniffing attacks.
    """

    def __init__(self, app: ASGIApp, is_production: bool = False):
        self.app = app
        self.is_production = is_production

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

                    production_csp_setting = ProductionCSPSetting.PRODUCTION
                    # noinspection PyUnreachableCode
                    match production_csp_setting:
                        case ProductionCSPSetting.REPORT_ONLY:
                            log.info("CSP Report Only")
                            # Report Only Content Security Policy for production
                            # - use to report what is being prevented by CSP policy
                            security_headers[b"content-security-policy-report-only"] = (
                                b"frame-ancestors 'self';"
                                b"block-all-mixed-content;"
                                b"default-src 'self';"
                                b"script-src 'self';"
                                b"style-src 'self';"
                                b"object-src 'none';"
                                b"frame-src 'self';"
                                b"child-src 'self';"
                                b"img-src 'self';"
                                b"font-src 'self';"
                                b"connect-src 'self';"
                                b"manifest-src 'self';"
                                b"base-uri 'self';"
                                b"form-action 'self';"
                                b"media-src 'self';"
                                b"prefetch-src 'self';"
                                b"worker-src 'self';"
                            )
                        case ProductionCSPSetting.REPORT_SECURE:
                            log.info("CSP Report Secure")
                            security_headers[b"content-security-policy-report-only"] = (
                                b"frame-ancestors 'self';"
                                b"default-src 'self';"
                                b"script-src 'self' 'unsafe-inline' https://umami.musigree.com/ https://pagead2.googlesyndication.com/ https://fundingchoicesmessages.google.com ;"
                                b"style-src 'self' 'unsafe-inline' 'unsafe-hashes';"
                                b"object-src 'none';"
                                b"frame-src 'self';"
                                b"child-src 'self';"
                                b"img-src 'self' data:;"
                                b"font-src 'self';"
                                b"connect-src 'self' https://umami.musigree.com/ https://fundingchoicesmessages.google.com;"
                                b"manifest-src 'self';"
                                b"base-uri 'self';"
                                b"form-action 'self';"
                                b"media-src 'self' data:;"
                                b"worker-src 'self';"
                            )
                        case ProductionCSPSetting.PRODUCTION:
                            security_headers[b"content-security-policy"] = (
                                b"frame-ancestors 'self';"
                                b"default-src 'self';"
                                b"script-src 'self' 'unsafe-inline' https://umami.musigree.com/ https://pagead2.googlesyndication.com/ https://fundingchoicesmessages.google.com ;"
                                b"style-src 'self' 'unsafe-inline' 'unsafe-hashes';"
                                b"object-src 'none';"
                                b"frame-src 'self';"
                                b"child-src 'self';"
                                b"img-src 'self' data:;"
                                b"font-src 'self';"
                                b"connect-src 'self' https://umami.musigree.com/ https://fundingchoicesmessages.google.com;"
                                b"manifest-src 'self';"
                                b"base-uri 'self';"
                                b"form-action 'self';"
                                b"media-src 'self' data:;"
                                b"worker-src 'self';"
                            )
                        case _:
                            log.error("CSP Production Security Headers Not Set")
                            sys.exit("CSP Production Security Headers Not Set")

                else:
                    # More permissive CSP for development
                    security_headers[b"content-security-policy"] = (
                        b"default-src 'self' 'unsafe-inline' 'unsafe-eval' data:; "
                        b"script-src 'self' 'unsafe-inline' 'unsafe-eval' data: http://localhost:5173; "
                        b"connect-src 'self' http://localhost:* ws://localhost:*; "
                        b"img-src 'self' data: https: http://localhost:5173;"
                    )

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

    # Add security headers middleware
    # noinspection PyTypeChecker
    app.add_middleware(SecurityHeadersMiddleware, is_production=config.PRODUCTION)

    log.info(
        f"Security middleware configured for {'production' if config.PRODUCTION else 'development'} environment"
    )
