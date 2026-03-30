from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from fastapi import FastAPI


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


def register_exception_handlers(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
