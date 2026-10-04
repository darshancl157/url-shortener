"""Domain exceptions. Services raise these; the API layer maps them to HTTP responses."""


class AppError(Exception):
    status_code = 500
    message = "Internal server error."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message