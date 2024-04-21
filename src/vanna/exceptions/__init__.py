class ImproperlyConfigured(Exception):
    """Raise for incorrect configuration."""

    pass


class DependencyError(Exception):
    """Raise for missing dependencies."""

    pass


class ConnectionError(Exception):
    """Raise for connection"""

    pass


class OTPCodeError(Exception):
    """Raise for invalid otp or not able to send it"""

    pass


class SQLRemoveError(Exception):
    """Raise when not able to remove SQL"""

    pass


class ExecutionError(Exception):
    """Raise when not able to execute Code"""

    pass


class ValidationError(Exception):
    """Raise for validations"""

    pass


class APIError(Exception):
    """Raise for API errors"""

    pass
