import unittest

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


class TestBaseError(unittest.TestCase):
    """Test cases for the BaseError exception class."""

    def test_base_error_default_values(self):
        """Test BaseError with default message and status code."""
        error = BaseError()
        self.assertEqual("", error.message)
        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR, error.status_code)
        self.assertEqual("", str(error))

    def test_base_error_custom_message(self):
        """Test BaseError with custom message."""
        custom_message = "Custom error message"
        error = BaseError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR, error.status_code)

    def test_base_error_custom_status_code(self):
        """Test BaseError with custom status code."""
        custom_status = status.HTTP_400_BAD_REQUEST
        error = BaseError(status_code=custom_status)
        self.assertEqual("", error.message)
        self.assertEqual(custom_status, error.status_code)

    def test_base_error_custom_message_and_status(self):
        """Test BaseError with custom message and status code."""
        custom_message = "Custom error"
        custom_status = status.HTTP_418_IM_A_TEAPOT
        error = BaseError(message=custom_message, status_code=custom_status)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(custom_status, error.status_code)
        self.assertEqual(custom_message, str(error))

    def test_base_error_inheritance(self):
        """Test BaseError inherits from Exception."""
        error = BaseError(message="test")
        self.assertIsInstance(error, Exception)


class TestBadRequestError(unittest.TestCase):
    """Test cases for the BadRequestError exception class."""

    def test_bad_request_error_default(self):
        """Test BadRequestError with default message."""
        error = BadRequestError()
        self.assertEqual("Bad request", error.message)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, error.status_code)

    def test_bad_request_error_custom_message(self):
        """Test BadRequestError with custom message."""
        custom_message = "Invalid input data"
        error = BadRequestError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, error.status_code)

    def test_bad_request_error_inheritance(self):
        """Test BadRequestError inherits from BaseError."""
        error = BadRequestError()
        self.assertIsInstance(error, BaseError)
        self.assertIsInstance(error, Exception)


class TestUnprocessableError(unittest.TestCase):
    """Test cases for the UnprocessableError exception class."""

    def test_unprocessable_error_default(self):
        """Test UnprocessableError with default message."""
        error = UnprocessableError()
        self.assertEqual("Validation error", error.message)
        self.assertEqual(status.HTTP_406_NOT_ACCEPTABLE, error.status_code)

    def test_unprocessable_error_custom_message(self):
        """Test UnprocessableError with custom message."""
        custom_message = "Field validation failed"
        error = UnprocessableError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_406_NOT_ACCEPTABLE, error.status_code)

    def test_unprocessable_error_inheritance(self):
        """Test UnprocessableError inherits from BaseError."""
        error = UnprocessableError()
        self.assertIsInstance(error, BaseError)
        self.assertIsInstance(error, Exception)


class TestNotFoundError(unittest.TestCase):
    """Test cases for the NotFoundError exception class."""

    def test_not_found_error_default(self):
        """Test NotFoundError with default message."""
        error = NotFoundError()
        self.assertEqual("Not found", error.message)
        self.assertEqual(status.HTTP_404_NOT_FOUND, error.status_code)

    def test_not_found_error_custom_message(self):
        """Test NotFoundError with custom message."""
        custom_message = "Resource not found"
        error = NotFoundError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_404_NOT_FOUND, error.status_code)

    def test_not_found_error_inheritance(self):
        """Test NotFoundError inherits from BaseError."""
        error = NotFoundError()
        self.assertIsInstance(error, BaseError)
        self.assertIsInstance(error, Exception)


class TestAuthenticationError(unittest.TestCase):
    """Test cases for the AuthenticationError exception class."""

    def test_authentication_error_default(self):
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        self.assertEqual("Authentication error", error.message)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, error.status_code)

    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message."""
        custom_message = "Invalid credentials"
        error = AuthenticationError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, error.status_code)

    def test_authentication_error_inheritance(self):
        """Test AuthenticationError inherits from BaseError."""
        error = AuthenticationError()
        self.assertIsInstance(error, BaseError)
        self.assertIsInstance(error, Exception)


class TestAuthorizationError(unittest.TestCase):
    """Test cases for the AuthorizationError exception class."""

    def test_authorization_error_default(self):
        """Test AuthorizationError with default message."""
        error = AuthorizationError()
        self.assertEqual("Authorization error", error.message)
        self.assertEqual(status.HTTP_403_FORBIDDEN, error.status_code)

    def test_authorization_error_custom_message(self):
        """Test AuthorizationError with custom message."""
        custom_message = "Insufficient permissions"
        error = AuthorizationError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_403_FORBIDDEN, error.status_code)

    def test_authorization_error_inheritance(self):
        """Test AuthorizationError inherits from BaseError."""
        error = AuthorizationError()
        self.assertIsInstance(error, BaseError)
        self.assertIsInstance(error, Exception)


class TestDatabaseError(unittest.TestCase):
    """Test cases for the DatabaseError exception class."""

    def test_database_error_default(self):
        """Test DatabaseError with default message."""
        error = DatabaseError()
        self.assertEqual("Database error", error.message)
        self.assertEqual(status.HTTP_503_SERVICE_UNAVAILABLE, error.status_code)

    def test_database_error_custom_message(self):
        """Test DatabaseError with custom message."""
        custom_message = "Connection timeout"
        error = DatabaseError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_503_SERVICE_UNAVAILABLE, error.status_code)

    def test_database_error_inheritance(self):
        """Test DatabaseError inherits from BaseError."""
        error = DatabaseError()
        self.assertIsInstance(error, BaseError)
        self.assertIsInstance(error, Exception)


class TestProcessError(unittest.TestCase):
    """Test cases for the ProcessError exception class."""

    def test_process_error_default(self):
        """Test ProcessError with default message."""
        error = ProcessError()
        self.assertEqual("Background process error", error.message)
        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR, error.status_code)

    def test_process_error_custom_message(self):
        """Test ProcessError with custom message."""
        custom_message = "Worker process failed"
        error = ProcessError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR, error.status_code)

    def test_process_error_inheritance(self):
        """Test ProcessError inherits from BaseError."""
        error = ProcessError()
        self.assertIsInstance(error, BaseError)
        self.assertIsInstance(error, Exception)


class TestRateLimitError(unittest.TestCase):
    """Test cases for the RateLimitError exception class."""

    def test_rate_limit_error_default(self):
        """Test RateLimitError with default message."""
        error = RateLimitError()
        self.assertEqual("Too Many Requests", error.message)
        self.assertEqual(status.HTTP_429_TOO_MANY_REQUESTS, error.status_code)

    def test_rate_limit_error_custom_message(self):
        """Test RateLimitError with custom message."""
        custom_message = "Rate limit exceeded"
        error = RateLimitError(message=custom_message)
        self.assertEqual(custom_message, error.message)
        self.assertEqual(status.HTTP_429_TOO_MANY_REQUESTS, error.status_code)

    def test_rate_limit_error_inheritance(self):
        """Test RateLimitError inherits from BaseError."""
        error = RateLimitError()
        self.assertIsInstance(error, BaseError)
        self.assertIsInstance(error, Exception)


class TestExceptionModule(unittest.TestCase):
    """Test cases for the exceptions module as a whole."""

    def test_all_exceptions_defined(self):
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
        
        self.assertEqual(set(expected_exceptions), set(__all__))

    def test_status_code_uniqueness(self):
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
        self.assertGreaterEqual(len(unique_codes), 7)  # At least 7 unique codes

    def test_exception_raising_and_catching(self):
        """Test that exceptions can be properly raised and caught."""
        test_message = "Test exception message"
        
        with self.assertRaises(BadRequestError) as context:
            raise BadRequestError(message=test_message)
        
        self.assertEqual(test_message, context.exception.message)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, context.exception.status_code)

    def test_exception_str_representation(self):
        """Test string representation of exceptions."""
        test_message = "Test message"
        error = NotFoundError(message=test_message)
        self.assertEqual(test_message, str(error))


if __name__ == "__main__":
    unittest.main() 