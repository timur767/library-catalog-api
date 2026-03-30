from uuid import UUID


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    """Ресурс не найден."""

    def __init__(self, resource: str, identifier: UUID | str | int):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} with id '{identifier}' not found")


class ValidationException(AppException):
    """Ошибка валидации бизнес-правил."""

    def __init__(self, message: str):
        super().__init__(message)


class ConflictException(AppException):
    """Конфликт данных (например, дубликат)."""

    def __init__(self, message: str):
        super().__init__(message)
