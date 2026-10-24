"""Domain exceptions. Services raise these; the API layer maps them to HTTP responses."""


class AppError(Exception):
    status_code = 500
    message = "Internal server error."
    headers: dict[str, str] | None = None

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

class UnauthorizedError(AppError):
    status_code = 401
    message = "Not authenticated."

class TooManyRequestsError(AppError):
    status_code = 429
    message = "Too many requests. Try again later."

    def __init__(self, retry_after: int):
        super().__init__(f"Too many requests. Try again in {retry_after} seconds.")
        self.headers = {"Retry-After": str(retry_after)}