from datetime import datetime
from typing import Callable, Awaitable, List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, PlainTextResponse
from starlette.types import ASGIApp


class CustomCORSPreflightMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: List[str] | None = None,
        allow_methods: List[str] | None = None,
        allow_headers: List[str] | None = None,
        allow_credentials: bool = True,
        max_age: int = 600,
    ):
        super().__init__(app)
        self.allowed_origins = allow_origins or []
        self.allowed_methods = allow_methods or []
        self.allowed_headers = allow_headers or []
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def _is_origin_allowed(self, origin: str) -> bool:
        return origin in self.allowed_origins

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        origin = request.headers.get("origin")
        method = request.method

        # Handle preflight requests (OPTIONS)
        if method == "OPTIONS" and origin:
            if self._is_origin_allowed(origin):
                response = Response(status_code=204)  # No Content for preflight
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
                response.headers["Access-Control-Max-Age"] = str(self.max_age)

                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"

                return response
            else:
                return PlainTextResponse("Invalid origin", status_code=400)

        # Process the actual request
        response = await call_next(request)

        # Add CORS headers to actual responses
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin

            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


class PreflightLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to log preflight requests for debugging purposes"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "OPTIONS":
            print(f"[PREFLIGHT] {datetime.now().isoformat()} - {request.method} {request.url.path}")
            print(f"  Origin: {request.headers.get('origin')}")
            print(f"  Requested Method: {request.headers.get('access-control-request-method')}")
            print(f"  Requested Headers: {request.headers.get('access-control-request-headers')}")

            # Process the request
            response = await call_next(request)

            # Log response headers
            print("  Responding with CORS headers:")
            print(
                f"    Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}"
            )
            print(
                f"    Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods')}"
            )
            print(
                f"    Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers')}"
            )
            print(f"    Access-Control-Max-Age: {response.headers.get('Access-Control-Max-Age')}")
            return response

        return await call_next(request)
