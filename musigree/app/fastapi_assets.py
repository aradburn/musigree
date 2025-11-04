"""
This module defines the assets handling for the Musigree application.

It provides a function to create a FastAPI router for serving static assets,
with support for both development and production environments.

Key functionalities include:
    - Creating a router for static assets
    - Handling Vite assets in development and production
    - Providing templates with asset URLs through Jinja2

The module uses the following components:
    - FastAPI: For creating the router
    - Starlette: For static files serving
    - Jinja2: For template context processing
"""

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from musigree.app.fastapi_app import templates
from musigree.config import Configuration
from musigree.constants import FRONTEND_DIR

log = logging.getLogger(__name__)
"""The logger for the assets module."""


def create_assets_router(config: Configuration) -> tuple[APIRouter, Jinja2Templates]:
    """
    Creates a FastAPI router for serving static assets.

    Args:
        config: The application configuration.

    Returns:
        Tuple[APIRouter, Jinja2Templates]: The configured assets router and templates.
    """
    # Get environment variables
    vite_origin = os.getenv("VITE_ORIGIN", "http://localhost:5173")

    # Set application constants
    is_production = config.PRODUCTION

    log.info(f"is_production: {is_production}")

    # Create assets router
    assets_router = APIRouter()

    # Mount static files
    # if is_production:
    #     # In production, serve the bundled assets directly
    #     assets_path = FRONTEND_DIR / "dist"
    #     assets_router.mount(
    #         "/prodassets", StaticFiles(directory=assets_path), name="assets"
    #     )

    # Load manifest file in the production environment
    manifest = {}
    if is_production:
        manifest_path = FRONTEND_DIR / "dist" / "manifest.json"
        try:
            with open(manifest_path, "r") as content:
                manifest = json.load(content)
        except OSError as exception:
            raise OSError(
                f"Manifest file not found at {manifest_path}. Run `npm run build`."
            ) from exception

    # Set up templates and add context functions
    # templates = Jinja2Templates(directory=TEMPLATES_DIR)

    @assets_router.get("/context")
    async def get_template_context(request: Request) -> dict[str, Any]:
        """
        Provides template context for assets.

        This is a dummy endpoint that's not meant to be called directly.
        It's used to register the context processor with the templates.

        Args:
            request: The FastAPI request object.

        Returns:
            dict[str, Any]: The template context.
        """
        return {"request": request}

    # Add asset resolver to templates
    def dev_asset(file_path: str) -> str:
        """
        Resolves an asset path in development.

        Args:
            file_path: The path to the asset.

        Returns:
            str: The URL to the asset.
        """
        asset_path = f"{vite_origin}/assets/{file_path}"
        log.debug(f"dev asset: {file_path} -> {asset_path}")
        return asset_path

    def prod_asset(file_path: str) -> str:
        """
        Resolves an asset path in production.

        Args:
            file_path: The path to the asset.

        Returns:
            str: The URL to the asset.
        """
        return f"/prodassets/{manifest[file_path]['file']}"

    asset_func = prod_asset if is_production else dev_asset

    # Add context function to all templates
    templates.env.globals.update(
        {
            "asset": asset_func,
            "is_production": is_production,
        }
    )

    return assets_router, templates
