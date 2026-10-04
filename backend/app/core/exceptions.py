"""Domain exceptions. Services raise these; the API layer maps them to HTTP responses."""


class AppError(Exception):
    status_code = 500
    message = "Internal server error."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message

class BadRequestError(AppError):
    status_code = 400
    message = "Bad request."


class NotFoundError(AppError):
    status_code = 404
    message = "Short URL not found."


class ConflictError(AppError):
    status_code = 409
    message = "Resource already exists."


class IdGenerationError(AppError):
    status_code = 503
    message = "Could not generate a unique short ID. Try again."