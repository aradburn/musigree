"""Allow other sites to embed the Open Graph image.

Open Graph consumers load ``/img/og_image.png`` from other origins. The page
Content-Security-Policy does not apply to those requests.
``Cross-Origin-Resource-Policy: same-site`` does, so this middleware relaxes
that header for the one image.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_OPEN_GRAPH_IMAGE_PATH = "/img/og_image.png"
_CORP_HEADER_NAME = b"cross-origin-resource-policy"


class OpenGraphImageEmbeddingMiddleware:
    """Let other origins embed the Open Graph image.

    The rest of the site keeps ``Cross-Origin-Resource-Policy: same-site``,
    which blocks cross-origin ``<img>`` loads. This one file is published for
    link previews, so its response uses ``cross-origin``.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") != _OPEN_GRAPH_IMAGE_PATH:
            await self.app(scope, receive, send)
            return

        async def send_embeddable(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = message.setdefault("headers", [])
                # SecWeb writes the header in mixed case. Match case-insensitively
                # so the same-site value is replaced rather than sent twice.
                message["headers"] = [
                    (name, value)
                    for name, value in raw_headers
                    if name.lower() != _CORP_HEADER_NAME
                ]
                message["headers"].append((_CORP_HEADER_NAME, b"cross-origin"))
            await send(message)

        await self.app(scope, receive, send_embeddable)
