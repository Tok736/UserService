class AppException(Exception):
    status: int = 400
    message: str = "Bad Request"

    def __init__(self, message: str | None = None, status: int | None = None):
        if message is not None:
            self.message = message
        if status is not None:
            self.status = status
        super().__init__(self.message)


class InvalidToken(AppException):
    status = 401
    message = "Invalid or expired token"
