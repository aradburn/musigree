"""
This module defines the user interface (UI) routes for the Musigree application using FastAPI.

It handles requests for the main index page, entity-specific pages, and
static files like favicons. It uses FastAPI's `APIRouter` to organize the routes
and interact with the Musigree backend.

Key functionalities include:
    - Serving the main index page with initial data for the network graph
      and roles.
    - Serving entity-specific pages, displaying the network graph for a given
      entity.
    - Handling request argument parsing for roles and year.
    - Integrating with `RoleCache` for role data and `RuntimeDatabaseManager`
      for network data.
    - Using `RuntimeEntityRepository` and `RuntimeRelationRepository` for
      database interactions.
    - Employing `runtime_transaction` for database transactions.
    - Handling `BadRequestError` and `NotFoundError`.

The module uses `musigree.utils` for parsing request arguments,
`musigree.exceptions` for custom exceptions, and `musigree.library.cache.role_cache`
for role caching. It interacts with `musigree.runtime` for database operations.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

import musigree.utils
from musigree.exceptions import BadRequestError, NotFoundError
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction

log = logging.getLogger(__name__)
"""
The logger for the UI module.
"""

router = APIRouter()
"""
The FastAPI router for the UI routes.

This router is used to organize the UI routes and their related functionality.
"""

UI_DEFAULT_ROLES = [
    "Alias",
    "Member Of",
    # 'Sublabel Of',
    # 'Released On',
]
"""
Default roles to display if none are specified in the request.
"""


@router.get("/", response_class=HTMLResponse)
async def route__index(
    request: Request,
    roles: list[str] | None = Query(None),
    year: int | None = Query(None),
) -> HTMLResponse:
    """
    Serves the main index page.

    This route handles requests to the root URL ("/"). It prepares the
    initial data for the network graph and roles, renders the index
    template, and returns the response.

    Args:
        request: The FastAPI request object.
        roles: Optional list of roles to filter the network by.
        year: Optional year to filter the network by.

    Returns:
        HTMLResponse: The rendered index page.
    """
    from musigree.library.cache.role_cache import RoleCache
    from musigree.runtime.data_access_layer.role_entry import RoleEntry
    from musigree.app.fastapi_app import templates

    network_js = "var dgNetwork = null;\n"
    """Initial JavaScript for the network graph, set to null."""
    log.debug(f"network_js: {network_js}")

    roles_json = RoleCache.get_roles_json()
    """Get the roles JSON data from the RoleCache."""
    roles_js = f"var dgRoles = {roles_json};\n"
    # log.debug(f"roles_js: {roles_js}")

    # Combines network and roles json
    initial_js = network_js + roles_js
    """Combine the network and roles JavaScript variables."""
    # log.debug(f"initial_js: {initial_js}")

    # Convert query parameters to the format expected by the existing code
    query_params: dict[str, Any] = {}
    if roles:
        query_params["roles"] = roles
    if year is not None:
        query_params["year"] = year

    parsed_args = musigree.utils.parse_request_args(query_params)
    """Parse the request arguments for roles and year."""
    original_roles, original_year = parsed_args if parsed_args else (None, None)
    if not original_roles:
        original_roles = UI_DEFAULT_ROLES.copy()
    """Use default roles if none are specified in the request."""
    multiselect_mapping = RoleEntry.get_multiselect_mapping()
    """Get the multiselect mapping for roles."""

    # Get the application root from the request
    application_url = str(request.base_url).rstrip("/")

    # Build URL with query parameters
    url = "/"
    if original_roles:
        url += f"?roles={','.join(original_roles)}"
        if original_year:
            url += f"&year={original_year}"
    elif original_year:
        url += f"?year={original_year}"

    """Generate the URL for the current request with the selected roles."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            # "request": request,
            "application_url": application_url,
            "initial_json": initial_js,
            "multiselect_mapping": multiselect_mapping,
            "og_title": "Musigree",
            "og_url": url,
            "original_roles": original_roles,
            "original_year": original_year,
            "title": "Musigree",
        },
    )


@router.get("/{entity_type_str}/{entity_id}", response_class=HTMLResponse)
async def route__entity_type__entity_id(
    request: Request,
    entity_type_str: str,
    entity_id: str,
    roles: list[str] | None = Query(None),
    year: int | None = Query(None),
) -> HTMLResponse:
    """
    Serves the entity-specific page.

    This route handles requests for URLs like "/artist/123" or "/label/456".
    It retrieves the network graph data for the specified entity, prepares
    the initial data, renders the index template, and returns the response.

    Args:
        request: The FastAPI request object.
        entity_type_str: The type of the entity (e.g., "artist", "label").
        entity_id: The ID of the entity.
        roles: Optional list of roles to filter the network by.
        year: Optional year to filter the network by.

    Returns:
        HTMLResponse: The rendered entity-specific page.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        NotFoundError: If no network data is found for the given entity.
    """
    from musigree.library.cache.role_cache import RoleCache
    from musigree.runtime.data_access_layer.role_entry import RoleEntry

    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )
    from musigree.runtime.runtime_database.runtime_relation_repository import (
        RuntimeRelationRepository,
    )
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
    from musigree.app.fastapi_app import templates

    assert RuntimeDatabaseManager.runtime_database_helper is not None, (
        "runtime_database_helper must be initialized before calling initialize()"
    )

    # Convert query parameters to the format expected by the existing code
    query_params: dict[str, Any] = {}
    if roles:
        query_params["roles"] = roles
    if year is not None:
        query_params["year"] = year

    parsed_args = musigree.utils.parse_request_args(query_params)
    """Parse the request arguments for roles and year."""
    requested_roles, requested_year = parsed_args if parsed_args else (None, None)
    if not requested_roles:
        requested_roles = UI_DEFAULT_ROLES.copy()
    """Use default roles if none are specified in the request."""
    try:
        entity_type = EntityType.from_str(entity_type_str.upper())
    except NotImplementedError:
        raise BadRequestError(message="Bad Entity Type")
    """Validate the entity type."""
    if not entity_id.isnumeric():
        raise BadRequestError(message="Bad Entity Id")
    """Validate the entity ID."""
    entity_id_int = int(entity_id)

    async with runtime_transaction():
        entity_repository = RuntimeEntityRepository()
        relation_repository = RuntimeRelationRepository()
        network_data = await RuntimeDatabaseManager.runtime_database_helper.get_network(
            entity_repository,
            relation_repository,
            entity_id_int,
            entity_type,
            on_mobile=False,
            roles=requested_roles,
        )
    """Retrieve the network data for the entity."""
    if network_data is None:
        raise NotFoundError(message="No Network Data")
    """Raise NotFoundError if no network data is found."""

    network_json = json.dumps(
        network_data,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    """Convert the network data to JSON."""
    network_js = f"var dgNetwork = {network_json};\n"
    """Create a JavaScript variable for the network data."""
    log.debug(f"network_js: {network_js}")

    roles_json = RoleCache.get_roles_json()
    """Get the roles JSON data from the RoleCache."""
    roles_js = f"var dgRoles = {roles_json};\n"
    # log.debug(f"roles_js: {roles_js}")

    # Combines network and roles json
    initial_js = network_js + roles_js
    """Combine the network and roles JavaScript variables."""
    # log.debug(f"initial_js: {initial_js}")

    entity_name = network_data["center"]["name"]
    """Extract the entity name from the network data."""
    key = f"{entity_type.name.lower()}-{entity_id}"
    """Create a unique key for the entity."""

    # Get the application root from the request
    application_url = str(request.base_url).rstrip("/")

    # Build URL with query parameters
    url = f"/{entity_type.name.lower()}/{entity_id}"
    if requested_roles:
        url += f"?roles={','.join(requested_roles)}"
        if requested_year:
            url += f"&year={requested_year}"
    elif requested_year:
        url += f"?year={requested_year}"

    """Generate the URL for the current entity."""
    title = f"Musigree: {entity_name}"
    """Set the page title."""
    multiselect_mapping = RoleEntry.get_multiselect_mapping()
    """Get the multiselect mapping for roles."""

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "application_url": application_url,
            "initial_json": initial_js,
            "key": key,
            "multiselect_mapping": multiselect_mapping,
            "og_title": f'Musigree: The "{entity_name}" network',
            "og_url": url,
            "original_roles": requested_roles,
            "original_year": requested_year,
            "title": title,
        },
    )
