import logging
import sys

from Secweb.ContentSecurityPolicy import ContentSecurityPolicy
from Secweb.ContentSecurityPolicy.ContentSecurityPolicyMiddleware import (
    ContentSecurityPolicyOptions,
)
from fastapi import FastAPI

from musigree.config import Configuration
from musigree.constants import AnalyticsType, CSPSetting

log = logging.getLogger(__name__)


def get_content_security_policy_report_only() -> ContentSecurityPolicyOptions:
    # Setup CSP headers
    csp: ContentSecurityPolicyOptions = {
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
) -> ContentSecurityPolicyOptions:
    # Setup CSP headers
    csp: ContentSecurityPolicyOptions = {
        "frame-ancestors": ["'self'"],
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "data:",
            analytics_script_url,
        ],
        # Need to remove 'unsafe-inline'
        "script-src-elem": [
            "'self'",
            "data:",
            "'unsafe-inline'",
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
) -> ContentSecurityPolicyOptions:
    # Setup CSP headers
    csp: ContentSecurityPolicyOptions = {
        "frame-ancestors": ["'self'"],
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "data:",
            "http://localhost:5173",
            "http://localhost:5173/assets/@vite/client",
            analytics_script_url,
        ],
        "script-src-elem": [
            "'self'",
            "data:",
            "'unsafe-inline'",
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
    content_security_policy_options = get_content_security_policy_production(
        analytics_script_url=analytics_script_url, analytics_api_url=analytics_api_url
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

    # Add CSP security headers middleware
    app.add_middleware(
        ContentSecurityPolicy,
        Option=content_security_policy_options,
        script_nonce=False,
        style_nonce=False,
        report_only=is_report_only,
    )

    log.info(
        f"Security middleware configured for {'production' if config.PRODUCTION else 'development'} environment"
    )
