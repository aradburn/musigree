"""
This module defines utility functions and dependencies for the Musigree FastAPI application.

It primarily includes a `rate_limiter` dependency for implementing rate limiting on
FastAPI application endpoints.

Key functionalities include:
    - **`rate_limiter`**: A dependency factory that enforces rate limiting on FastAPI
      endpoints. It uses a Redis client (or a fake Redis client for
      testing) to track the number of requests made by a specific client
      within a defined time period. API and page routes also share a daily
      counter: after 1000 requests in a day, that client is limited to
      500 requests an hour.

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
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Path, Query, Request, Response

from musigree.exceptions import BadRequestError, RateLimitError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_type import EntityType

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from musigree.library.cache.cache_manager import BaseCache

log = logging.getLogger(__name__)
"""
The logger for the dependencies module.
"""

BURST_PERIOD_SECONDS = 60
DEFAULT_BURST_MAX_REQUESTS = 60
SEARCH_BURST_MAX_REQUESTS = 120
SEARCH_PATH_PREFIX = "/api/search/"
HEAVY_USAGE_DAILY_REQUEST_THRESHOLD = 1000
HEAVY_USAGE_HOURLY_REQUEST_LIMIT = 500
HEAVY_USAGE_DAILY_PERIOD_SECONDS = 24 * 60 * 60
HEAVY_USAGE_HOURLY_PERIOD_SECONDS = 60 * 60


def get_entity_type(
    entity_type_str: Annotated[
        str,
        Path(description="Entity type, such as artist or label"),
    ],
) -> EntityType:
    try:
        entity_type = EntityType.from_str(entity_type_str.upper())
    except NotImplementedError:
        raise BadRequestError(message="Bad Entity Type") from None

    return entity_type


def get_entity_id(
    entity_id: Annotated[
        str,
        Path(description="Numeric entity ID"),
    ],
) -> int:
    if not entity_id.isnumeric():
        raise BadRequestError(message="Bad Entity Id")

    entity_id_int = int(entity_id)
    return entity_id_int


def get_min_year(
    min_year: Annotated[
        int | None,
        Query(description="Inclusive lower bound for release year"),
    ] = None,
) -> int | None:
    """Return the requested minimum release year, if one was sent."""
    return min_year


def get_max_year(
    max_year: Annotated[
        int | None,
        Query(description="Inclusive upper bound for release year"),
    ] = None,
) -> int | None:
    """Return the requested maximum release year, if one was sent."""
    return max_year


def get_year_bounds(
    min_year: Annotated[int | None, Depends(get_min_year)],
    max_year: Annotated[int | None, Depends(get_max_year)],
) -> tuple[int | None, int | None]:
    """Return inclusive year bounds, rejecting an inverted range."""
    if min_year is not None and max_year is not None and min_year > max_year:
        raise BadRequestError(message="min_year must be less than or equal to max_year")
    log.debug(f"Requested year bounds: {min_year}, {max_year}")
    return min_year, max_year


def get_roles(
    roles: Annotated[
        str | None,
        Query(description="Comma-separated role names; commas in names can be escaped with a backslash"),
    ] = None,
) -> set[str]:
    from musigree.library.cache.role_cache import RoleCache

    roles_result = set()
    if roles is not None:
        # List is comma-separated, roles that contain commas are escaped by a \
        unescaped_value = roles.replace("\\,", "|")
        for role_escaped in unescaped_value.split(","):
            role = role_escaped.replace("|", ",")
            # log.debug(f"Requested role: {role}")
            if role in RoleCache.role_category_to_role_name_lookup:
                # log.debug(f"Requested role found: {role}")
                for role_entry in RoleCache.role_category_to_role_name_lookup[role]:
                    # log.debug(f"Requested role_entry: {role_entry}")
                    if role_entry in RoleCache.role_name_to_role_id_lookup:
                        roles_result.add(role_entry)
            elif role in RoleCache.role_name_to_role_id_lookup:
                roles_result.add(role)

    log.debug(f"Requested roles: {roles_result}")
    return roles_result


EntityTypeDep = Annotated[EntityType, Depends(get_entity_type)]
EntityIdDep = Annotated[int, Depends(get_entity_id)]
MinYearDep = Annotated[int | None, Depends(get_min_year)]
MaxYearDep = Annotated[int | None, Depends(get_max_year)]
YearBoundsDep = Annotated[tuple[int | None, int | None], Depends(get_year_bounds)]
RolesDep = Annotated[set[str], Depends(get_roles)]
OnMobileQuery = Annotated[
    bool,
    Query(description="Whether the request is from a mobile device"),
]


def _client_host(request: Request) -> str:
    """Return the client address used to bucket rate-limit counters."""
    if request.client is not None and hasattr(request.client, "host"):
        return request.client.host
    return "unknown"


def _parse_count(redis_value: object) -> int:
    """Return a cache counter, treating missing or unreadable values as zero."""
    if isinstance(redis_value, bool) or not isinstance(redis_value, (int, str, bytes)):
        return 0
    if isinstance(redis_value, str | bytes) and not redis_value:
        return 0
    try:
        return int(redis_value)
    except ValueError:
        return 0


async def _window_count(cache: BaseCache, cache_key: str) -> int:
    """Read a window counter, allowing the request when the cache read fails."""
    try:
        return _parse_count(await cache.get(cache_key))
    except Exception as error:
        log.warning(f"Redis error in rate limiter: {error}")
        return 0


async def _window_ttl(cache: BaseCache, cache_key: str, period: int) -> int:
    """Return the remaining window lifetime, or the full period when it is unknown."""
    try:
        ttl_raw = await cache.ttl(cache_key)
    except Exception as error:
        log.warning(f"Redis TTL error in rate limiter: {error}")
        return period
    if isinstance(ttl_raw, int) and ttl_raw > 0:
        return ttl_raw
    return period


async def _increment_window(cache: BaseCache, cache_key: str, period: int, current_count: int) -> None:
    """Count one allowed request and start the window when the key is new."""
    try:
        await cache.incr(cache_key)
        if current_count == 0:
            await cache.expire(cache_key, period)
    except Exception as error:
        log.warning(f"Redis incr/expire error in rate limiter: {error}")


def _write_limit_headers(
    response: Response,
    *,
    limit: int,
    slots_remaining: int,
    ttl_seconds: int,
) -> dict[str, str]:
    """Publish the limit that decided this request and return those headers."""
    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(0, slots_remaining - 1)),
        "X-RateLimit-Reset": str(int(time.time()) + ttl_seconds),
    }
    response.headers.update(headers)
    return headers


def _write_daily_headers(response: Response, daily_slots_remaining: int) -> dict[str, str]:
    """Publish how many requests remain before the daily threshold."""
    headers = {
        "X-RateLimit-Daily-Limit": str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD),
        "X-RateLimit-Daily-Remaining": str(max(0, daily_slots_remaining - 1)),
    }
    response.headers.update(headers)
    return headers


async def _enforce_sustained_usage(cache: BaseCache, response: Response, client_host: str) -> bool:
    """Count this client for the day and hour, and cap the hour after the daily threshold.

    Counters are per client, not per route, so every API and page request shares
    one budget. The hourly cap starts on the request that would pass 1000 in the
    current day. Until then only the route burst limit applies. Returns whether
    the hourly cap is the limit the client has to follow for this request.
    """
    daily_key = f"ratelimit:daily:{client_host}"
    hourly_key = f"ratelimit:hourly:{client_host}"
    daily_count = await _window_count(cache, daily_key)
    hourly_count = await _window_count(cache, hourly_key)
    hourly_ttl = await _window_ttl(cache, hourly_key, HEAVY_USAGE_HOURLY_PERIOD_SECONDS)
    over_daily_threshold = daily_count >= HEAVY_USAGE_DAILY_REQUEST_THRESHOLD

    if over_daily_threshold and hourly_count >= HEAVY_USAGE_HOURLY_REQUEST_LIMIT:
        headers = _write_limit_headers(
            response,
            limit=HEAVY_USAGE_HOURLY_REQUEST_LIMIT,
            slots_remaining=HEAVY_USAGE_HOURLY_REQUEST_LIMIT - hourly_count,
            ttl_seconds=hourly_ttl,
        )
        headers.update(_write_daily_headers(response, 0))
        log.debug(f"key: {hourly_key}, remaining: 0, ttl: {hourly_ttl}")
        raise RateLimitError(headers=headers)

    await _increment_window(cache, daily_key, HEAVY_USAGE_DAILY_PERIOD_SECONDS, daily_count)
    await _increment_window(cache, hourly_key, HEAVY_USAGE_HOURLY_PERIOD_SECONDS, hourly_count)

    if over_daily_threshold:
        _write_limit_headers(
            response,
            limit=HEAVY_USAGE_HOURLY_REQUEST_LIMIT,
            slots_remaining=HEAVY_USAGE_HOURLY_REQUEST_LIMIT - hourly_count,
            ttl_seconds=hourly_ttl,
        )
        _write_daily_headers(response, 0)
        return True

    _write_daily_headers(response, HEAVY_USAGE_DAILY_REQUEST_THRESHOLD - daily_count)
    return False


def rate_limiter(
    max_requests: int = 10,
    period: int = 60,
    *,
    enforce_heavy_usage_limit: bool = False,
) -> Callable[..., Awaitable[None]]:
    """
    A dependency factory that enforces rate limiting on a FastAPI endpoint.

    This dependency limits the number of requests a client can make to a
    specific endpoint within a defined time period. It uses a Redis client
    to track the number of requests and raises a `RateLimitError` if the limit
    is exceeded.

    When `enforce_heavy_usage_limit` is set, the same client also has one
    daily counter and one hourly counter shared across routes. After more
    than `HEAVY_USAGE_DAILY_REQUEST_THRESHOLD` requests in a day, further
    requests are limited to `HEAVY_USAGE_HOURLY_REQUEST_LIMIT` per hour.
    Clients at or below that daily total keep this function's burst limit.

    Args:
        max_requests: The maximum number of requests allowed
            within the period. Defaults to 10.
        period: The time period (in seconds) within which the
            `max_requests` apply. Defaults to 60.
        enforce_heavy_usage_limit: Also apply the shared daily threshold
            and the tighter hourly cap that follows it.

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
        client_host = _client_host(request)
        cache = CacheManager.get_cache()
        # The Redis key used to track requests for this endpoint and client.
        cache_key = f"ratelimit:{request.url.path}:{client_host}"
        current_requests = await _window_count(cache, cache_key)
        ttl_value = await _window_ttl(cache, cache_key, period)
        remaining = max_requests - current_requests

        if remaining <= 0:
            headers = _write_limit_headers(
                response,
                limit=max_requests,
                slots_remaining=remaining,
                ttl_seconds=ttl_value,
            )
            log.debug(f"key: {cache_key}, remaining: {remaining}, ttl: {ttl_value}")
            raise RateLimitError(headers=headers)

        # The sustained cap is checked before the burst counter moves, so a
        # rejected request does not consume either window.
        hourly_limit_applies = False
        if enforce_heavy_usage_limit:
            hourly_limit_applies = await _enforce_sustained_usage(cache, response, client_host)

        await _increment_window(cache, cache_key, period, current_requests)
        log.debug(f"key: {cache_key}, remaining: {remaining}, ttl: {ttl_value}")
        if not hourly_limit_applies:
            _write_limit_headers(
                response,
                limit=max_requests,
                slots_remaining=remaining,
                ttl_seconds=ttl_value,
            )

    rate_limit_dependency.is_rate_limiter = True  # type: ignore[attr-defined]
    return rate_limit_dependency


_default_burst_limiter = rate_limiter(
    max_requests=DEFAULT_BURST_MAX_REQUESTS,
    period=BURST_PERIOD_SECONDS,
    enforce_heavy_usage_limit=True,
)
_search_burst_limiter = rate_limiter(
    max_requests=SEARCH_BURST_MAX_REQUESTS,
    period=BURST_PERIOD_SECONDS,
    enforce_heavy_usage_limit=True,
)


async def api_rate_limit(request: Request, response: Response) -> None:
    """Rate-limit every API route, with a higher burst for search."""
    if request.url.path.startswith(SEARCH_PATH_PREFIX):
        await _search_burst_limiter(request, response)
        return
    await _default_burst_limiter(request, response)


async def ui_rate_limit(request: Request, response: Response) -> None:
    """Rate-limit HTML pages with the same daily budget as the API."""
    await _default_burst_limiter(request, response)


api_rate_limit.is_rate_limiter = True  # type: ignore[attr-defined]
ui_rate_limit.is_rate_limiter = True  # type: ignore[attr-defined]
