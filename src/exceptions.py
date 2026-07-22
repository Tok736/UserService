class AppException(Exception):
    """Базовое доменное исключение приложения"""

    status: int = 400
    message: str = "Bad Request"

    def __init__(self, message: str | None = None, status: int | None = None):
        if message is not None:
            self.message = message
        if status is not None:
            self.status = status
        super().__init__(self.message)


class AuthConsumerUnavailable(AppException):
    status = 500
    message = "Auth service unavailable"


class InvalidToken(AppException):
    status = 401
    message = "Invalid or expired token"


class AlreadyDeleted(AppException):
    status = 409
    message = "Already deleted"


class NotFound(AppException):
    status = 404
    message = "Not found"


class AccessDenied(AppException):
    status = 403
    message = "Access denied"


class ValidationError(AppException):
    status = 422
    message = "Validation error"


class Conflict(AppException):
    status = 409
    message = "Conflict"


class VersionConflict(AppException):
    status = 409
    message = "Version conflict, reload and retry"
