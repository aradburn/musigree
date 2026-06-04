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
from typing import Annotated
from typing import Any

from fastapi import APIRouter, Depends, Query, Path

from musigree.app.fastapi_dependencies import (
    rate_limiter,
    get_entity_type,
    get_entity_id,
    get_roles,
    get_year,
)
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_type import EntityType
from musigree.library.full_text_search.text_search_utils import normalise_search_content
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction

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
@router.get("/{entity_type_str}/details/{entity_id}")
async def route__api__entity_type__details__entity_id(
    entity_type: Annotated[EntityType, Depends(get_entity_type)],
    entity_id: Annotated[int, Depends(get_entity_id)],
    _: None = Depends(rate_limiter(max_requests=60, period=60)),
) -> dict[str, Any]:
    """
    Retrieves detailed information for a specific entity.

    This endpoint returns comprehensive details about an entity, including
    its metadata, aliases, groups, members, countries, genres, and styles.

    Args:
        entity_type: The type of the entity (e.g., "artist", "label").
        entity_id: The ID of the entity.
        _: Dependency injection for rate limiting.

    Returns:
        dict[str, Any]: A dictionary containing the entity details.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        UnprocessableError: If no entity is found with the given ID and type.
    """
    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )

    # Try to get from cache first
    cache = CacheManager.get_cache()
    cache_key_str = CacheManager.create_cache_hkey(
        "api", f"{entity_type.name.lower()}/details/{entity_id}"
    )
    entity_data: dict[str, Any] | None = await cache.hgetall(cache_key_str)
    if entity_data is not None:
        return entity_data
    try:
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
    except NotFoundError:
        raise NotFoundError(message="Entity details not found") from None

    # Convert the entity to a dictionary format suitable for API response
    result_entity_data: dict[str, Any] = {
        "id": entity.entity_id,
        "type": entity.entity_type.name.lower(),
        "name": entity.entity_name,
        "metadata": entity.entity_metadata,
        "entities": entity.entities,
        "relation_counts": entity.relation_counts,
        "countries": entity.countries,
        "genres": entity.genres,
        "styles": entity.styles,
    }

    # Cache the result
    await cache.hset(cache_key_str, result_entity_data)

    return result_entity_data


# noinspection PyUnusedLocal
@router.get("/{entity_type_str}/network/{entity_id}")
async def route__api__entity_type__network__entity_id(
    entity_type: Annotated[EntityType, Depends(get_entity_type)],
    entity_id: Annotated[int, Depends(get_entity_id)],
    roles: Annotated[list[str], Depends(get_roles)],
    year: Annotated[tuple[int, int] | int | None, Depends(get_year)] = None,
    on_mobile: Annotated[bool, Query()] = False,
    _: None = Depends(rate_limiter(max_requests=60, period=60)),
) -> dict[str, Any]:
    """
    Retrieves the network graph for a specific entity.

    This endpoint returns the network graph centered around a given entity,
    identified by its type and ID. It supports filtering by roles.

    Args:
        entity_type: The type of the entity (e.g., "artist", "label").
        entity_id: The ID of the entity.
        roles: Optional list of roles to filter the network by.
        year: Optional year to filter the network by.
        on_mobile: Optional flag indicating if the request is from a mobile device.
        _: Dependency injection for rate limiting.

    Returns:
        dict[str, Any]: A dictionary containing the network graph data.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        UnprocessableError: If no data is found for the given entity.
    """
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

    # Try to get from cache first
    cache = CacheManager.get_cache()
    cache_key_str = CacheManager.create_cache_hkey(
        "api", f"{entity_type.name.lower()}/network/{entity_id}"
    )
    network_data: dict[str, Any] | None = await cache.hgetall(cache_key_str)
    if network_data is not None:
        return network_data

    try:
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            relation_repository = RuntimeRelationRepository()
            network_data = await RuntimeDatabaseManager.runtime_database_helper.get_network(
                entity_repository,
                relation_repository,
                entity_id,
                entity_type,
                on_mobile=on_mobile,
                roles=roles,
            )
    except NotFoundError:
        raise NotFoundError(message="Entity network not found") from None

    if network_data is None:
        raise NotFoundError(message="No Data")

    # Cache the result
    await cache.hset(cache_key_str, network_data)

    return network_data


# noinspection PyUnusedLocal
@router.get("/{entity_type_str}/relations/{entity_id}")
async def route__api__entity_type__relations__entity_id(
    entity_type: Annotated[EntityType, Depends(get_entity_type)],
    entity_id: Annotated[int, Depends(get_entity_id)],
    _: None = Depends(rate_limiter(max_requests=60, period=60)),
) -> dict[str, Any]:
    """
    Retrieves relations for a specific entity.

    This endpoint returns the relations associated with a given entity,
    identified by its type and ID.

    Args:
        entity_type: The type of the entity (e.g., "artist", "label").
        entity_id: The ID of the entity.
        _: Dependency injection for rate limiting.

    Returns:
        dict[str, Any]: A dictionary containing the relations data.

    Raises:
        BadRequestError: If the entity type or entity ID is invalid.
        UnprocessableError: If no data is found for the given entity.
    """
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

    # Try to get from cache first
    cache = CacheManager.get_cache()
    cache_key_str = CacheManager.create_cache_hkey(
        "api", f"{entity_type.name.lower()}/relations/{entity_id}"
    )
    relations_data: dict[str, Any] | None = await cache.hgetall(cache_key_str)
    if relations_data is not None:
        return relations_data
    try:
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            relation_repository = RuntimeRelationRepository()
            relations_data = await RuntimeDatabaseManager.runtime_database_helper.get_relations_by_entity_id_and_entity_type(
                entity_repository,
                relation_repository,
                entity_id,
                entity_type,
            )

    except NotFoundError:
        raise NotFoundError(message="Entity relations not found") from None

    if relations_data is None:
        raise NotFoundError(message="No Relations Data")

    # Cache the result
    await cache.hset(cache_key_str, relations_data)

    return relations_data


@router.get("/search/{search_string}")
async def route__api__search(
    search_string: str = Path(
        ...,  # The '...' indicates the parameter is required
        title="The string to search for",
        min_length=2,
        max_length=20,
    ),
    _: None = Depends(rate_limiter(max_requests=120, period=60)),
) -> dict[str, Any]:
    """
    Searches for entities based on a search string.

    This endpoint returns a list of entities that match the given search string.

    Args:
        search_string: The string to search for.
        _: Dependency injection for rate limiting.

    Returns:
        dict[str, Any]: A dict containing a list of entities matching the search string.
    """
    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )
    from musigree.runtime.data_access_layer.runtime_entity_search import (
        RuntimeEntitySearch,
    )
    from musigree.runtime.runtime_database.runtime_token_repository import RuntimeTokenRepository

    # Normalize first
    normalised_search_string = normalise_search_content(search_string)

    # Try to get from cache first
    cache = CacheManager.get_cache()
    cache_key_str = CacheManager.create_cache_hkey("api", f"search/{normalised_search_string}")
    search_data: dict[str, Any] | None = await cache.hgetall(cache_key_str)
    if search_data is not None:
        return search_data

    try:
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            token_repository = RuntimeTokenRepository()

            search_data = await RuntimeEntitySearch.search_entities(
                entity_repository, token_repository, normalised_search_string
            )
    except NotFoundError as _ex:
        raise NotFoundError(message="Entity name not found") from None

    result_search_data: dict[str, Any] = search_data if search_data is not None else {}

    # Cache the result
    await cache.hset(cache_key_str, result_search_data)

    return result_search_data


@router.get("/random")
async def route__api__random(
    _: None = Depends(rate_limiter(max_requests=60, period=60)),
) -> dict[str, str]:
    """
    Retrieves a random entity.

    This endpoint returns a random entity from the database.

    Args:
        _: Dependency injection for rate limiting.

    Returns:
        dict[str, str]: A dictionary containing the random entity's type and ID.

    Raises:
        DatabaseError: If there is an error retrieving the random entity.
    """
    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    assert RuntimeDatabaseManager.runtime_database_helper is not None, (
        "runtime_database_helper must be initialized before calling initialize()"
    )

    async with runtime_transaction():
        entity_repository = RuntimeEntityRepository()
        try:
            (
                entity_id,
                entity_type,
            ) = await RuntimeDatabaseManager.runtime_database_helper.get_random_entity(
                entity_repository
            )
            log.debug(f"    Found random entity: {entity_type}-{entity_id}")
        except Exception:
            log.exception("Error in API for /random", exc_info=True)
            raise DatabaseError(message="API error") from None

    data = {"center": f"{entity_type.name.lower()}-{entity_id}"}
    return data


@router.get("/roles")
async def route__api__role(
    _: None = Depends(rate_limiter(max_requests=60, period=60)),
) -> dict[str, Any]:
    """
    Retrieves all available roles.

    This endpoint returns all the roles in the musigree application.

    Args:
        _: Dependency injection for rate limiting.

    Returns:
        dict[str, Any]: A dict containing an entry with a list of all the roles.
    """
    from musigree.library.cache.role_cache import RoleCache

    role_data = RoleCache.get_all_roles()
    return role_data
