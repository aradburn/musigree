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
      providing a in-memory implementation of the Redis API.
    - `exceptions.RateLimitError`: A custom exception raised when the rate
      limit is exceeded.
    - `logging`: For logging operations.
"""

import logging
import time
from typing import Callable

import fakeredis
from fastapi import Request, Response

from musigree.exceptions import RateLimitError

log = logging.getLogger(__name__)
"""
The logger for the dependencies module.
"""

redis_client = fakeredis.FakeStrictRedis()
# redis_client = redis.StrictRedis()
"""
The redis client, `fakeredis.FakeStrictRedis` is used for testing.
"""


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

        key = f"ratelimit:{request.url.path}:{client_host}"
        """
        The Redis key used to track requests for this endpoint and client.
        """

        try:
            # Get current requests (handle Redis byte response)
            current_requests = 0
            redis_value = redis_client.get(key)
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
        except (ValueError, TypeError) as e:
            log.debug(f"Redis error handling value: {e}")
            remaining = max_requests
            await redis_client.setex(key, period, 0)

        # Get TTL and handle Redis response
        ttl_raw = redis_client.ttl(key)
        ttl_value = period

        # If TTL is a valid positive number, use it
        if isinstance(ttl_raw, int) and ttl_raw > 0:
            ttl_value = ttl_raw

        # Add rate limit headers to the response
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining - 1))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + ttl_value)

        if remaining > 0:
            # Increment the request count
            # noinspection PyAsyncCall
            redis_client.incr(key, 1)
            log.debug(f"key: {key}, remaining: {remaining}, ttl: {ttl_value}")
        else:
            log.debug(f"key: {key}, remaining: {remaining}, ttl: {ttl_value}")
            raise RateLimitError()

    return rate_limit_dependency
