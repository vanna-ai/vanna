
class ImproperlyConfigured(BaseException):
    """Raise for incorrect configuration."""

    pass


class DependencyError(BaseException):
    """Raise for missing dependencies."""

    pass


class ConnectionError(BaseException):
    """Raise for connection"""

    pass


class OtpCodeError(BaseException):
    """Raise for invalid otp or not able to send it"""

    pass


class SQLRemoveError(BaseException):
    """Raise when not able to remove SQL"""

    pass


class ExecutionError(BaseException):
    """Raise when not able to execute Code"""

    pass


class ValidationError(BaseException):
    """Raise for validations"""

    pass


class APIError(BaseException):
    """Raise for API errors"""

    pass

