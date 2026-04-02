import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.library_catalog.api.v1.schemas.book import BookCreate, BookUpdate
from src.library_catalog.domain.exceptions import (
    BookAlreadyExistsException,
    BookNotFoundException,
)
from src.library_catalog.domain.services.book_service import BookService


def make_service(book_repo=None, ol_client=None):
    if book_repo is None:
        book_repo = AsyncMock()
    if ol_client is None:
        ol_client = AsyncMock()
        ol_client.enrich = AsyncMock(return_value={})
    return BookService(book_repository=book_repo, openlibrary_client=ol_client)


def make_book_create(**kwargs) -> BookCreate:
    defaults = dict(
        title="Test Book",
        author="Test Author",
        year=2020,
        genre="Fiction",
        pages=100,
        isbn=None,
        description=None,
    )
    defaults.update(kwargs)
    return BookCreate(**defaults)


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn_raises():
    """ISBN дубликат должен выбрасывать BookAlreadyExistsException."""
    repo = AsyncMock()
    repo.find_by_isbn = AsyncMock(return_value=MagicMock())  # найден дубликат

    service = make_service(book_repo=repo)
    book_data = make_book_create(isbn="9780132350884")

    with pytest.raises(BookAlreadyExistsException):
        await service.create_book(book_data)


def test_book_create_invalid_pages_raises_validation_error():
    """Pydantic должен отклонять pages=0 до передачи в сервис."""
    with pytest.raises(ValidationError):
        make_book_create(pages=0)


@pytest.mark.asyncio
async def test_create_book_success():
    """Успешное создание книги без ISBN."""
    repo = AsyncMock()
    mock_book = MagicMock()
    mock_book.book_id = uuid4()
    mock_book.title = "Test Book"
    mock_book.author = "Test Author"
    mock_book.year = 2020
    mock_book.genre = "Fiction"
    mock_book.pages = 100
    mock_book.available = True
    mock_book.isbn = None
    mock_book.description = None
    mock_book.extra = None
    from datetime import datetime
    mock_book.created_at = datetime.now()
    mock_book.updated_at = datetime.now()

    repo.find_by_isbn = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=mock_book)

    service = make_service(book_repo=repo)
    book_data = make_book_create()

    result = await service.create_book(book_data)
    assert result.title == "Test Book"
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_book_not_found_raises():
    """Получение несуществующей книги должно выбрасывать BookNotFoundException."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)

    service = make_service(book_repo=repo)

    with pytest.raises(BookNotFoundException):
        await service.get_book(uuid4())


@pytest.mark.asyncio
async def test_update_book_not_found_raises():
    """Обновление несуществующей книги должно выбрасывать BookNotFoundException."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)

    service = make_service(book_repo=repo)
    book_data = BookUpdate(title="New Title")

    with pytest.raises(BookNotFoundException):
        await service.update_book(uuid4(), book_data)


@pytest.mark.asyncio
async def test_delete_book_not_found_raises():
    """Удаление несуществующей книги должно выбрасывать BookNotFoundException."""
    repo = AsyncMock()
    repo.delete = AsyncMock(return_value=False)

    service = make_service(book_repo=repo)

    with pytest.raises(BookNotFoundException):
        await service.delete_book(uuid4())
