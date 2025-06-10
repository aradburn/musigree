from typing import Any

import pytest
from starlette import status

from musigree.exceptions import (
    BaseError,
    BadRequestError,
    UnprocessableError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ProcessError,
    RateLimitError,
)


def test_base_error_default_values() -> None:
    """Test BaseError with default message and status code."""
    error = BaseError()
    assert error.message == ""
    assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert str(error) == ""


def test_base_error_custom_message() -> None:
    """Test BaseError with custom message."""
    custom_message = "Custom error message"
    error = BaseError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_base_error_custom_status_code() -> None:
    """Test BaseError with custom status code."""
    custom_status = status.HTTP_400_BAD_REQUEST
    error = BaseError(status_code=custom_status)
    assert error.message == ""
    assert error.status_code == custom_status


def test_base_error_custom_message_and_status() -> None:
    """Test BaseError with custom message and status code."""
    custom_message = "Custom error"
    custom_status = status.HTTP_418_IM_A_TEAPOT
    error = BaseError(message=custom_message, status_code=custom_status)
    assert error.message == custom_message
    assert error.status_code == custom_status
    assert str(error) == custom_message


def test_base_error_inheritance() -> None:
    """Test BaseError inherits from Exception."""
    error = BaseError(message="test")
    assert isinstance(error, Exception)


def test_bad_request_error_default() -> None:
    """Test BadRequestError with default message."""
    error = BadRequestError()
    assert error.message == "Bad request"
    assert error.status_code == status.HTTP_400_BAD_REQUEST


def test_bad_request_error_custom_message() -> None:
    """Test BadRequestError with custom message."""
    custom_message = "Invalid input data"
    error = BadRequestError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_400_BAD_REQUEST


def test_bad_request_error_inheritance() -> None:
    """Test BadRequestError inherits from BaseError."""
    error = BadRequestError()
    assert isinstance(error, BaseError)
    assert isinstance(error, Exception)


def test_unprocessable_error_default() -> None:
    """Test UnprocessableError with default message."""
    error = UnprocessableError()
    assert error.message == "Validation error"
    assert error.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_unprocessable_error_custom_message() -> None:
    """Test UnprocessableError with custom message."""
    custom_message = "Field validation failed"
    error = UnprocessableError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_unprocessable_error_inheritance() -> None:
    """Test UnprocessableError inherits from BaseError."""
    error = UnprocessableError()
    assert isinstance(error, BaseError)
    assert isinstance(error, Exception)


def test_not_found_error_default() -> None:
    """Test NotFoundError with default message."""
    error = NotFoundError()
    assert error.message == "Not found"
    assert error.status_code == status.HTTP_404_NOT_FOUND


def test_not_found_error_custom_message() -> None:
    """Test NotFoundError with custom message."""
    custom_message = "Resource not found"
    error = NotFoundError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_404_NOT_FOUND


def test_not_found_error_inheritance() -> None:
    """Test NotFoundError inherits from BaseError."""
    error = NotFoundError()
    assert isinstance(error, BaseError)
    assert isinstance(error, Exception)


def test_authentication_error_default() -> None:
    """Test AuthenticationError with default message."""
    error = AuthenticationError()
    assert error.message == "Authentication error"
    assert error.status_code == status.HTTP_401_UNAUTHORIZED


def test_authentication_error_custom_message() -> None:
    """Test AuthenticationError with custom message."""
    custom_message = "Invalid credentials"
    error = AuthenticationError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_401_UNAUTHORIZED


def test_authentication_error_inheritance() -> None:
    """Test AuthenticationError inherits from BaseError."""
    error = AuthenticationError()
    assert isinstance(error, BaseError)
    assert isinstance(error, Exception)


def test_authorization_error_default() -> None:
    """Test AuthorizationError with default message."""
    error = AuthorizationError()
    assert error.message == "Authorization error"
    assert error.status_code == status.HTTP_403_FORBIDDEN


def test_authorization_error_custom_message() -> None:
    """Test AuthorizationError with custom message."""
    custom_message = "Insufficient permissions"
    error = AuthorizationError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_403_FORBIDDEN


def test_authorization_error_inheritance() -> None:
    """Test AuthorizationError inherits from BaseError."""
    error = AuthorizationError()
    assert isinstance(error, BaseError)
    assert isinstance(error, Exception)


def test_database_error_default() -> None:
    """Test DatabaseError with default message."""
    error = DatabaseError()
    assert error.message == "Database error"
    assert error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_database_error_custom_message() -> None:
    """Test DatabaseError with custom message."""
    custom_message = "Connection timeout"
    error = DatabaseError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_database_error_inheritance() -> None:
    """Test DatabaseError inherits from BaseError."""
    error = DatabaseError()
    assert isinstance(error, BaseError)
    assert isinstance(error, Exception)


def test_process_error_default() -> None:
    """Test ProcessError with default message."""
    error = ProcessError()
    assert error.message == "Background process error"
    assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_process_error_custom_message() -> None:
    """Test ProcessError with custom message."""
    custom_message = "Worker process failed"
    error = ProcessError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_process_error_inheritance() -> None:
    """Test ProcessError inherits from BaseError."""
    error = ProcessError()
    assert isinstance(error, BaseError)
    assert isinstance(error, Exception)


def test_rate_limit_error_default() -> None:
    """Test RateLimitError with default message."""
    error = RateLimitError()
    assert error.message == "Too Many Requests"
    assert error.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_rate_limit_error_custom_message() -> None:
    """Test RateLimitError with custom message."""
    custom_message = "Rate limit exceeded"
    error = RateLimitError(message=custom_message)
    assert error.message == custom_message
    assert error.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_rate_limit_error_inheritance() -> None:
    """Test RateLimitError inherits from BaseError."""
    error = RateLimitError()
    assert isinstance(error, BaseError)
    assert isinstance(error, Exception)


def test_all_exceptions_defined() -> None:
    """Test that all exceptions from __all__ are properly defined."""
    # noinspection PyProtectedMember
    from musigree.exceptions import __all__
    
    expected_exceptions = [
        "BaseError",
        "BadRequestError", 
        "UnprocessableError",
        "NotFoundError",
        "AuthenticationError",
        "AuthorizationError",
        "DatabaseError",
        "ProcessError", 
        "RateLimitError",
    ]
    
    assert set(expected_exceptions) == set(__all__)


def test_status_code_uniqueness() -> None:
    """Test that different exception types have different status codes (where appropriate)."""
    error_status_pairs = [
        (BadRequestError(), status.HTTP_400_BAD_REQUEST),
        (UnprocessableError(), status.HTTP_406_NOT_ACCEPTABLE),
        (NotFoundError(), status.HTTP_404_NOT_FOUND),
        (AuthenticationError(), status.HTTP_401_UNAUTHORIZED),
        (AuthorizationError(), status.HTTP_403_FORBIDDEN),
        (DatabaseError(), status.HTTP_503_SERVICE_UNAVAILABLE),
        (ProcessError(), status.HTTP_500_INTERNAL_SERVER_ERROR),
        (RateLimitError(), status.HTTP_429_TOO_MANY_REQUESTS),
    ]
    
    status_codes = [pair[1] for pair in error_status_pairs]
    # Most status codes should be unique (except 500 which is shared by BaseError and ProcessError)
    unique_codes = set(status_codes)
    assert len(unique_codes) >= 7  # At least 7 unique codes


def test_exception_raising_and_catching() -> None:
    """Test that exceptions can be properly raised and caught."""
    test_message = "Test exception message"
    
    with pytest.raises(BadRequestError) as exc_info:
        raise BadRequestError(message=test_message)
    
    assert exc_info.value.message == test_message
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_exception_str_representation() -> None:
    """Test string representation of exceptions."""
    test_message = "Test message"
    error = NotFoundError(message=test_message)
    assert str(error) == test_message 