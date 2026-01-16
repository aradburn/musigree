"""
This module defines utility functions and dependencies for the Musigree FastAPI application.

It primarily includes a `rate_limiter` dependency for implementing rate limiting on
FastAPI application endpoints.

Key functionalities include:
    - **`rate_limiter`**: A dependency factory that enforces rate limiting on FastAPI
      endpoints. It uses a Redis client (or a fake Redis client for
      testing) to track the number of requests made by a specific client
      within a defined time period.

The `rate_limiter` dependency interacts with the following components:
    - `fastapi.Request`: For accessing information about the current request,
      such as the endpoint and remote address.
    - `fastapi.Response`: For adding headers to the response.
    - `fakeredis.FakeStrictRedis`: A fake Redis client used for testing,
      providing an in-memory implementation of the Redis API.
    - `exceptions.RateLimitError`: A custom exception raised when the rate
      limit is exceeded.
    - `logging`: For logging operations.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response

from musigree.exceptions import RateLimitError, BadRequestError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_type import EntityType

log = logging.getLogger(__name__)
"""
The logger for the dependencies module.
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


def get_entity_type(entity_type_str: str) -> EntityType:
    try:
        entity_type = EntityType.from_str(entity_type_str.upper())
    except NotImplementedError:
        raise BadRequestError(message="Bad Entity Type") from None

    return entity_type


def get_entity_id(entity_id: str) -> int:
    if not entity_id.isnumeric():
        raise BadRequestError(message="Bad Entity Id")

    entity_id_int = int(entity_id)
    return entity_id_int


def get_year(year: str | None = None) -> tuple[int, int] | int | None:
    if year is None:
        return None
    year_result: tuple[int, int] | int | None

    try:
        if "-" in year:
            start, _, stop = year.partition("-")
            start_year = int(start)
            stop_year = int(stop)
            if start_year <= stop_year:
                year_result = (start_year, stop_year)
            else:
                year_result = (stop_year, start_year)
        else:
            year_result = int(year)
    except ValueError:
        raise BadRequestError(message="Invalid year input") from None
    log.debug(f"Requested year: {year_result}")
    return year_result


def get_roles(roles: str | None = None) -> list[str]:
    from musigree.library.cache.role_cache import RoleCache

    roles_result = set()
    if roles is not None:
        # List is comma-separated, roles that contain commas are escaped by a \
        unescaped_value = roles.replace("\\,", "|")
        for role_escaped in unescaped_value.split(","):
            role = role_escaped.replace("|", ",")
            # log.debug(f"Requested role: {role}")
            if role in RoleCache.role_category_to_role_name_lookup.keys():
                # log.debug(f"Requested role found: {role}")
                for role_entry in RoleCache.role_category_to_role_name_lookup[role]:
                    # log.debug(f"Requested role_entry: {role_entry}")
                    if role_entry in RoleCache.role_name_to_role_id_lookup.keys():
                        roles_result.add(role_entry)
            elif role in RoleCache.role_name_to_role_id_lookup.keys():
                roles_result.add(role)

    if len(roles_result) == 0:
        roles_result = set(UI_DEFAULT_ROLES)
    roles_list: list[str] = list(sorted(roles_result))
    # log.debug(f"Requested roles: {roles}")
    return roles_list


def rate_limiter(max_requests: int = 10, period: int = 60) -> Callable:
    """
    A dependency factory that enforces rate limiting on a FastAPI endpoint.

    This dependency limits the number of requests a client can make to a
    specific endpoint within a defined time period. It uses a Redis client
    to track the number of requests and raises a `RateLimitError` if the limit
    is exceeded.

    Args:
        max_requests: The maximum number of requests allowed
            within the period. Defaults to 10.
        period: The time period (in seconds) within which the
            `max_requests` apply. Defaults to 60.

    Returns:
        Callable: A dependency function for rate limiting.
    """

    async def rate_limit_dependency(request: Request, response: Response) -> None:
        """
        The actual dependency that performs the rate limiting check.

        Args:
            request: The FastAPI request object.
            response: The FastAPI response object.

        Returns:
            None

        Raises:
            RateLimitError: If the rate limit is exceeded.
        """
        # Get client IP, with fallback if client is None
        client_host = "unknown"
        if request.client and hasattr(request.client, "host"):
            client_host = request.client.host

        cache = CacheManager.get_cache()
        # The Redis key used to track requests for this endpoint and client.
        cache_key = f"ratelimit:{request.url.path}:{client_host}"

        try:
            # Get current requests (handle Redis byte response)
            current_requests = 0
            # TODO: ASYNC IMPROVEMENT - Use await with aioredis:
            # redis_value = await get_redis_client().get(key)
            redis_value = cache.get(cache_key)
            if redis_value:
                # Convert bytes to string and then to int
                try:
                    if isinstance(redis_value, bytes):
                        current_requests = int(redis_value.decode("utf-8"))
                    else:
                        current_requests = int(str(redis_value))
                except (ValueError, TypeError):
                    pass
            else:
                current_requests = 0

            remaining = max_requests - current_requests
        except Exception as e:
            log.warning(f"Redis error in rate limiter: {e}")
            # Fallback: allow request but log the error
            remaining = max_requests
            current_requests = 0

        # Get TTL and handle Redis response
        try:
            # TODO: ASYNC IMPROVEMENT - Use await with aioredis:
            # ttl_raw = await get_redis_client().ttl(key)
            ttl_raw = cache.ttl(cache_key)
            ttl_value = period

            # If TTL is a valid positive number, use it
            if isinstance(ttl_raw, int) and ttl_raw > 0:
                ttl_value = ttl_raw
        except Exception as e:
            log.warning(f"Redis TTL error in rate limiter: {e}")
            ttl_value = period

        # Add rate limit headers to the response
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining - 1))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + ttl_value)

        if remaining > 0:
            # Increment the request count
            try:
                # TODO: ASYNC IMPROVEMENT - Use await with aioredis:
                # await get_redis_client().incr(key, 1)
                # if current_requests == 0:
                #     await get_redis_client().expire(key, period)
                await cache.incr(cache_key)
                # Set expiration if this is a new key
                if current_requests == 0:
                    await cache.expire(cache_key, period)
            except Exception as e:
                log.warning(f"Redis incr/expire error in rate limiter: {e}")
                # Continue without incrementing - graceful degradation
            log.debug(f"key: {cache_key}, remaining: {remaining}, ttl: {ttl_value}")
        else:
            log.debug(f"key: {cache_key}, remaining: {remaining}, ttl: {ttl_value}")
            raise RateLimitError()

    return rate_limit_dependency
