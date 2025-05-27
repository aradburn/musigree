"""
This module defines the API endpoints for the Musigree application using FastAPI.

It provides FastAPI routes for handling requests related to entities,
relations, networks, search, and random entities. It also includes error
handling and rate limiting.

Key functionalities include:
    - Retrieving relations for a specific entity.
    - Retrieving the network graph for a specific entity.
    - Searching for entities based on a search string.
    - Getting a random entity.
    - Getting all available roles.
    - Handling bad requests, not found errors, and database errors.
    - Applying rate limiting to various endpoints.

The API endpoints interact with the runtime database through
`RuntimeEntityRepository` and `RuntimeRelationRepository`. They use
`runtime_transaction` to ensure database operations are performed within
transactions.

The module uses `musigree.utils` for request argument parsing and
`musigree.middleware` for rate limiting. `RoleCache` is used for retrieving
role information.
"""

import logging
from typing import Dict, Any, List, Optional, cast

from fastapi import APIRouter, Depends, Query, Request

import musigree.utils
from musigree.exceptions import BadRequestError, NotFoundError, DatabaseError
from musigree.library.fields.entity_type import EntityType


from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.app.fastapi_dependencies import rate_limiter

log = logging.getLogger(__name__)
"""
The logger for this module.
"""

router = APIRouter()
"""
The FastAPI router for the API endpoints.

This router is used to organize the API routes and their related functionality.
"""


# noinspection PyUnusedLocal
@router.get("/{entity_type_str}/relations/{entity_id}")
async def route__api__entity_type__relations__entity_id(
    entity_type_str: str,
    entity_id: str,
    request: Request,
    _: None = Depends(rate_limiter(max_requests=60, period=60)),
) -> Dict[str, Any]:
    """
    Retrieves relations for a specific entity.

    This endpoint returns the relations associated with a given entity,
    identified by its type and ID.

    Args:
        entity_type_str: The type of the entity (e.g., "artist", "label").
        entity_id: The ID of the entity.
        request: The FastAPI request object.
        _: Dependency injection for rate limiting.

    Returns:
        Dict[str, Any]: A dictionary containing the relations data.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        NotFoundError: If no data is found for the given entity.
    """
    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )
    from musigree.runtime.runtime_database.runtime_relation_repository import (
        RuntimeRelationRepository,
    )
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    try:
        entity_type = EntityType.from_str(entity_type_str.upper())
    except NotImplementedError:
        raise BadRequestError(message="Bad Entity Type")

    if not entity_id.isnumeric():
        raise BadRequestError(message="Bad Entity Id")

    entity_id_int = int(entity_id)

    with runtime_transaction():
        entity_repository = RuntimeEntityRepository()
        relation_repository = RuntimeRelationRepository()
        data = RuntimeDatabaseManager.runtime_database_helper.get_relations_by_entity_id_and_entity_type(
            entity_repository,
            relation_repository,
            entity_id_int,
            entity_type,
        )

    if data is None:
        raise NotFoundError(message="No Data")

    return cast(Dict[str, Any], data)


# noinspection PyUnusedLocal
@router.get("/{entity_type_str}/network/{entity_id}")
async def route__api__entity_type__network__entity_id(
    entity_type_str: str,
    entity_id: str,
    request: Request,
    roles: Optional[List[str]] = Query(None),
    year: Optional[int] = Query(None),
    _: None = Depends(rate_limiter(max_requests=60, period=60)),
) -> Dict[str, Any]:
    """
    Retrieves the network graph for a specific entity.

    This endpoint returns the network graph centered around a given entity,
    identified by its type and ID. It supports filtering by roles.

    Args:
        entity_type_str: The type of the entity (e.g., "artist", "label").
        entity_id: The ID of the entity.
        request: The FastAPI request object.
        roles: Optional list of roles to filter the network by.
        year: Optional year to filter the network by.
        _: Dependency injection for rate limiting.

    Returns:
        Dict[str, Any]: A dictionary containing the network graph data.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        NotFoundError: If no data is found for the given entity.
    """
    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )
    from musigree.runtime.runtime_database.runtime_relation_repository import (
        RuntimeRelationRepository,
    )
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    try:
        entity_type = EntityType.from_str(entity_type_str.upper())
    except NotImplementedError:
        raise BadRequestError(message="Bad Entity Type")

    if not entity_id.isnumeric():
        raise BadRequestError(message="Bad Entity Id")

    entity_id_int = int(entity_id)

    # Convert query parameters to the format expected by the existing code
    query_params = {}
    if roles:
        query_params["roles"] = roles
    if year is not None:
        query_params["year"] = year

    parsed_args = musigree.utils.parse_request_args(query_params)
    original_roles, original_year = parsed_args if parsed_args else (None, None)

    if not original_roles:
        original_roles = []

    on_mobile = False

    with runtime_transaction():
        entity_repository = RuntimeEntityRepository()
        relation_repository = RuntimeRelationRepository()
        data = RuntimeDatabaseManager.runtime_database_helper.get_network(
            entity_repository,
            relation_repository,
            entity_id_int,
            entity_type,
            on_mobile=on_mobile,
            roles=original_roles,
        )

    if data is None:
        raise NotFoundError(message="No Data")

    return cast(Dict[str, Any], data)


@router.get("/search/{search_string}")
async def route__api__search(
    search_string: str, _: None = Depends(rate_limiter(max_requests=120, period=60))
) -> Dict[str, Any]:
    """
    Searches for entities based on a search string.

    This endpoint returns a list of entities that match the given search string.

    Args:
        search_string: The string to search for.
        _: Dependency injection for rate limiting.

    Returns:
        List[Dict[str, Any]]: A list of entities matching the search string.
    """
    from musigree.runtime.data_access_layer.runtime_entity_search import (
        RuntimeEntitySearch,
    )

    log.debug(f"search_string: {search_string}")
    data = RuntimeEntitySearch.search_entities(search_string)
    return cast(Dict[str, List[Dict[str, Any]]], data)


@router.get("/random")
async def route__api__random(
    _: None = Depends(rate_limiter(max_requests=60, period=60))
) -> Dict[str, str]:
    """
    Retrieves a random entity.

    This endpoint returns a random entity from the database.

    Args:
        _: Dependency injection for rate limiting.

    Returns:
        Dict[str, str]: A dictionary containing the random entity's type and ID.

    Raises:
        DatabaseError: If there is an error retrieving the random entity.
    """
    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    with runtime_transaction():
        entity_repository = RuntimeEntityRepository()
        try:
            entity_id, entity_type = (
                RuntimeDatabaseManager.runtime_database_helper.get_random_entity(
                    entity_repository
                )
            )
            log.debug(f"    Found random entity: {entity_type}-{entity_id}")
        except Exception:
            log.exception("Error in API for /random", exc_info=True)
            raise DatabaseError(message="API error")

    data = {"center": f"{entity_type.name.lower()}-{entity_id}"}
    return data


@router.get("/roles")
async def route__api__role(
    _: None = Depends(rate_limiter(max_requests=60, period=60))
) -> Dict[str, Any]:
    """
    Retrieves all available roles.

    This endpoint returns all the roles in the musigree application.

    Args:
        _: Dependency injection for rate limiting.

    Returns:
        Dict[str, Any]: A dict containing an entry with a list of all the roles.
    """
    from musigree.library.cache.role_cache import RoleCache

    role_data = RoleCache.get_all_roles()
    return role_data
