"""
This module defines custom exception classes for the Musigree system.

It provides a hierarchy of exceptions for different types of errors that may
occur within the application, such as bad requests, unprocessable entities,
not found resources, authentication/authorization failures, database errors,
process errors, and rate limit issues.

Key functionalities include:
    - **`BaseError`**: The base class for all custom exceptions, providing
      common attributes like `message` and `status_code`.
    - **`BadRequestError`**: Represents a bad request from the client.
    - **`UnprocessableError`**: Represents a request that cannot be processed
      due to validation errors or other conditions.
    - **`NotFoundError`**: Represents a resource that cannot be found.
    - **`AuthenticationError`**: Represents an authentication failure.
    - **`AuthorizationError`**: Represents an authorization failure (lack of
      permission).
    - **`DatabaseError`**: Represents a database-related error.
    - **`ProcessError`**: Represents an error that occurred in a background
      process.
    - **`RateLimitError`**: Represents a rate limit error (too many requests).
    - **Status Code Mapping**: Each exception class is associated with an
      appropriate HTTP status code from `starlette.status`.

The module interacts with the following components:
    - `starlette.status`: For defining standard HTTP status codes.

The module utilizes `typing` for type hinting and `starlette.status` for
the status code.
"""

from typing import Any

from starlette import status

__all__ = (
    "BaseError",
    "BadRequestError",
    "UnprocessableError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseError",
    "ProcessError",
    "RateLimitError",
)
"""
List of all exceptions defined in the module.
"""


class BaseError(Exception):
    """
    The base class for all custom exceptions in the Musigree system.

    This class provides common attributes for all exception types, such as
    `message` and `status_code`.
    """

    def __init__(
        self,
        *_: tuple[Any],
        message: str = "",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        """
        Initializes a BaseError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to "".
            status_code (int, optional): The HTTP status code associated
                with the error. Defaults to
                `status.HTTP_500_INTERNAL_SERVER_ERROR`.
        """

        self.message: str = message
        """The error message."""
        self.status_code: int = status_code
        """The HTTP status code associated with the error."""

        super().__init__(message)
        """Call the constructor of the parent class."""


class BadRequestError(BaseError):
    """
    Represents a bad request error.

    This exception is raised when the server cannot process the request due to
    a malformed or invalid request from the client.
    """

    def __init__(self, *_: tuple[Any], message: str = "Bad request") -> None:
        """
        Initializes a BadRequestError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to "Bad request".
        """
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)
        """Call the constructor of the parent class."""


class UnprocessableError(BaseError):
    """
    Represents an unprocessable entity error.

    This exception is raised when the server cannot process the request due to
    validation errors or other conditions, even if the request is well-formed.
    """

    def __init__(self, *_: tuple[Any], message: str = "Validation error") -> None:
        """
        Initializes an UnprocessableError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to
                "Validation error".
        """
        super().__init__(message=message, status_code=status.HTTP_406_NOT_ACCEPTABLE)
        """Call the constructor of the parent class."""


class NotFoundError(BaseError):
    """
    Represents a not found error.

    This exception is raised when the requested resource could not be found.
    """

    def __init__(self, *_: tuple[Any], message: str = "Not found") -> None:
        """
        Initializes a NotFoundError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to "Not found".
        """
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)
        """Call the constructor of the parent class."""


class AuthenticationError(BaseError):
    """
    Represents an authentication error.

    This exception is raised when the user fails to provide valid
    authentication credentials.
    """

    def __init__(self, *_: tuple[Any], message: str = "Authentication error") -> None:
        """
        Initializes an AuthenticationError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to
                "Authentication error".
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        """Call the constructor of the parent class."""


class AuthorizationError(BaseError):
    """
    Represents an authorization error.

    This exception is raised when the user is authenticated but does not have
    permission to perform the requested action.
    """

    def __init__(self, *_: tuple[Any], message: str = "Authorization error") -> None:
        """
        Initializes an AuthorizationError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to
                "Authorization error".
        """
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)
        """Call the constructor of the parent class."""


class DatabaseError(BaseError):
    """
    Represents a database error.

    This exception is raised when there is an error related to the database.
    """

    def __init__(self, *_: tuple[Any], message: str = "Database error") -> None:
        """
        Initializes a DatabaseError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to
                "Database error".
        """
        super().__init__(
            message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        """Call the constructor of the parent class."""


class ProcessError(BaseError):
    """
    Represents a background process error.

    This exception is raised when an error occurs in a background process.
    """

    def __init__(
        self, *_: tuple[Any], message: str = "Background process error"
    ) -> None:
        """
        Initializes a ProcessError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to
                "Background process error".
        """
        super().__init__(
            message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        """Call the constructor of the parent class."""


class RateLimitError(BaseError):
    """
    Represents a rate limit error.

    This exception is raised when the client has made too many requests.
    """

    def __init__(self, *_: tuple[Any], message: str = "Too Many Requests") -> None:
        """
        Initializes a RateLimitError instance.

        Args:
            *_: Unused positional arguments.
            message (str, optional): The error message. Defaults to
                "Too Many Requests".
        """
        super().__init__(message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        """Call the constructor of the parent class."""
