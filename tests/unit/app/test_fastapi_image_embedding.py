"""
Unit tests for musigree.app.fastapi_image_embedding module.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from Secweb import SecWeb
from starlette.responses import Response

from musigree.app.fastapi_image_embedding import OpenGraphImageEmbeddingMiddleware
from musigree.app.fastapi_middleware import add_app_middleware


class TestOpenGraphImageEmbedding:
    """Cross-origin embedding is limited to the Open Graph image."""

    def test_open_graph_image_allows_cross_origin_embedding(self) -> None:
        """Other sites can embed the Open Graph image; other files stay same-site."""
        app = FastAPI()

        @app.get("/img/og_image.png")
        def open_graph_image() -> Response:
            return Response(content=b"png", media_type="image/png")

        @app.get("/img/favicon-48x48.png")
        def other_image() -> Response:
            return Response(content=b"png", media_type="image/png")

        SecWeb(app, options={"csp": False, "corp": "same-site"})
        add_app_middleware(app, OpenGraphImageEmbeddingMiddleware)

        client = TestClient(app)
        open_graph = client.get("/img/og_image.png")
        other = client.get("/img/favicon-48x48.png")

        assert open_graph.headers["cross-origin-resource-policy"] == "cross-origin"
        assert other.headers["cross-origin-resource-policy"] == "same-site"
