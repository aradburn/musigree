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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from musigree.app.fastapi_dependencies import (
    EntityIdDep,
    EntityTypeDep,
    OnMobileQuery,
    RolesDep,
    YearDep,
)
from musigree.exceptions import NotFoundError
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction

log = logging.getLogger(__name__)
"""
The logger for the UI module.
"""

router = APIRouter(tags=["ui"])
"""
The FastAPI router for the UI routes.

This router is used to organize the UI routes and their related functionality.
"""

UI_DEFAULT_ARTIST_ROLES = [
    "Alias",
    "Member Of",
]
UI_DEFAULT_LABEL_ROLES = [
    "Alias",
    "Member Of",
    "Sublabel Of",
    "Released On",
]
"""
Default roles to display if none are specified in the request.
"""


@router.get("/", response_class=HTMLResponse, summary="Home page")
async def route__index(
    request: Request,
    roles: RolesDep,
    year: YearDep = None,
) -> HTMLResponse:
    """
    Serves the main index page.

    This route handles requests to the root URL ("/"). It prepares the
    initial data for the network graph and roles, renders the index
    template, and returns the response.

    Args:
        request: The FastAPI request object.
        roles: Optional set of roles to filter the network by.
        year: Optional year to filter the network by.

    Returns:
        HTMLResponse: The rendered index page.
    """
    # Imported lazily to avoid a circular import with fastapi_app.create_app.
    from musigree.app.fastapi_app import templates
    from musigree.library.cache.role_cache import RoleCache
    from musigree.runtime.data_access_layer.role_entry import RoleEntry

    network_js = "var dgNetwork = null;\n"
    """Initial JavaScript for the network graph, set to null."""
    log.debug(f"network_js: {network_js}")

    roles_json = RoleCache.get_roles_json()
    """Get all the roles JSON data from the RoleCache."""
    roles_js = f"var dgRoles = {roles_json};\n"
    # log.debug(f"roles_js: {roles_js}")

    # Combines network and roles json
    initial_js = network_js + roles_js
    """Combine the network and roles JavaScript variables."""
    # log.debug(f"initial_js: {initial_js}")

    multiselect_mapping = RoleEntry.get_multiselect_mapping()
    """Get the multiselect mapping for roles."""

    # Get the application root from the request
    application_url = str(request.base_url.replace(scheme="https")).rstrip("/")
    title = "Musigree - Explore Music Connections, an Interactive Map of Artists, Bands & Labels"

    # Build URL with query parameters
    og_url = application_url
    # if roles:
    #     og_url += f"?roles={','.join(roles)}"
    #     if year:
    #         og_url += f"&year={year}"
    # elif year:
    #     og_url += f"?year={year}"

    og_title = "Musigree - An Interactive Map of Artists, Bands & Labels"
    og_image = application_url + "/img/og_image.png"

    context = {
        "title": title,
        "application_url": application_url,
        "initial_json": initial_js,
        "multiselect_mapping": multiselect_mapping,
        "og_title": og_title,
        "og_type": "website",
        "og_image": og_image,
        "og_url": og_url,
        "original_roles": roles,
        "original_year": year,
    }

    """Generate the URL for the current request with the selected roles."""
    return templates.TemplateResponse(request=request, name="index.html", context=context)


async def route__entity_type__entity_id(
    request: Request,
    entity_type: EntityTypeDep,
    entity_id: EntityIdDep,
    roles: RolesDep,
    year: YearDep = None,
    on_mobile: OnMobileQuery = False,
) -> HTMLResponse:
    """
    Serves the entity-specific page.

    This route handles requests for URLs like "/artist/123" or "/label/456".
    It retrieves the network graph data for the specified entity, prepares
    the initial data, renders the index template, and returns the response.

    Args:
        request: The FastAPI request object.
        entity_type: The type of the entity (e.g., "artist", "label").
        entity_id: The ID of the entity.
        roles: Optional set of roles to filter the network by.
        year: Optional year to filter the network by.
        on_mobile: Optional flag indicating if the request is from a mobile device.

    Returns:
        HTMLResponse: The rendered entity-specific page.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        UnprocessableError: If no network data is found for the given entity.
    """
    # Imported lazily to avoid a circular import with fastapi_app.create_app.
    from musigree.app.fastapi_app import templates
    from musigree.library.cache.role_cache import RoleCache
    from musigree.runtime.data_access_layer.role_entry import RoleEntry
    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )
    from musigree.runtime.runtime_database.runtime_relation_repository import (
        RuntimeRelationRepository,
    )
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    assert RuntimeDatabaseManager.runtime_database_helper is not None, (
        "runtime_database_helper must be initialized before calling initialize()"
    )

    log.debug("route__entity_type__entity_id")

    roles_with_defaults = get_roles_with_defaults(roles, entity_type)

    try:
        # Retrieve the network data for the entity.
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            relation_repository = RuntimeRelationRepository()
            network_data = await RuntimeDatabaseManager.runtime_database_helper.get_network(
                entity_repository,
                relation_repository,
                entity_id,
                entity_type,
                on_mobile=on_mobile,
                roles=roles_with_defaults,
            )
    except NotFoundError as _ex:
        raise NotFoundError(message="Entity not found") from None

    # Raise UnprocessableError if no network data is found.
    if network_data is None:
        raise NotFoundError(message="No Network Data")

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
    application_url = str(request.base_url.replace(scheme="https")).rstrip("/")

    # Build URL with query parameters
    og_url = f"{application_url}/{entity_type.name.lower()}/{entity_id}"
    if roles:
        og_url += f"?roles={','.join(roles)}"
        if year:
            og_url += f"&year={year}"
    elif year:
        og_url += f"?year={year}"

    og_title = f'Musigree: The "{entity_name}" network'
    og_image = application_url + "/img/og_image.png"

    """Generate the URL for the current entity."""
    title = f"Musigree: {entity_name}"
    """Set the page title."""
    multiselect_mapping = RoleEntry.get_multiselect_mapping()
    """Get the multiselect mapping for roles."""

    context = {
        "title": title,
        "application_url": application_url,
        "initial_json": initial_js,
        "key": key,
        "multiselect_mapping": multiselect_mapping,
        "og_title": og_title,
        "og_type": "website",
        "og_image": og_image,
        "og_url": og_url,
        "original_roles": roles,
        "original_year": year,
    }

    return templates.TemplateResponse(request, name="index.html", context=context)


@router.get("/artist/{entity_id}", response_class=HTMLResponse, summary="Artist network page")
async def route__artist__entity_id(
    request: Request,
    entity_id: EntityIdDep,
    roles: RolesDep,
    year: YearDep = None,
    on_mobile: OnMobileQuery = False,
) -> HTMLResponse:
    """
    Serves the entity-specific page.

    This route handles requests for URLs like "/artist/123" or "/label/456".
    It retrieves the network graph data for the specified entity, prepares
    the initial data, renders the index template, and returns the response.

    Args:
        request: The FastAPI request object.
        entity_id: The ID of the entity.
        roles: Optional set of roles to filter the network by.
        year: Optional year to filter the network by.
        on_mobile: Optional flag indicating if the request is from a mobile device.

    Returns:
        HTMLResponse: The rendered entity-specific page.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        UnprocessableError: If no network data is found for the given entity.
    """
    return await route__entity_type__entity_id(
        request, EntityType.ARTIST, entity_id, roles, year, on_mobile
    )


@router.get("/label/{entity_id}", response_class=HTMLResponse, summary="Label network page")
async def route__label__entity_id(
    request: Request,
    entity_id: EntityIdDep,
    roles: RolesDep,
    year: YearDep = None,
    on_mobile: OnMobileQuery = False,
) -> HTMLResponse:
    """
    Serves the entity-specific page.

    This route handles requests for URLs like "/artist/123" or "/label/456".
    It retrieves the network graph data for the specified entity, prepares
    the initial data, renders the index template, and returns the response.

    Args:
        request: The FastAPI request object.
        entity_id: The ID of the entity.
        roles: Optional set of roles to filter the network by.
        year: Optional year to filter the network by.
        on_mobile: Optional flag indicating if the request is from a mobile device.

    Returns:
        HTMLResponse: The rendered entity-specific page.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        UnprocessableError: If no network data is found for the given entity.
    """
    return await route__entity_type__entity_id(
        request, EntityType.LABEL, entity_id, roles, year, on_mobile
    )


def get_roles_with_defaults(roles: set[str], entity_type: EntityType) -> list[str]:
    roles_result = roles
    if len(roles) == 0:
        if entity_type == EntityType.ARTIST:
            roles_result = set(UI_DEFAULT_ARTIST_ROLES)
        elif entity_type == EntityType.LABEL:
            roles_result = set(UI_DEFAULT_LABEL_ROLES)

    return sorted(roles_result)
