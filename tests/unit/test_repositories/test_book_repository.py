import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.library_catalog.data.repositories.book_repository import BookRepository


@pytest_asyncio.fixture
async def book_repo(db_session: AsyncSession) -> BookRepository:
    return BookRepository(db_session)


@pytest.mark.asyncio
async def test_find_by_isbn_not_found(book_repo: BookRepository):
    """Поиск по несуществующему ISBN должен вернуть None."""
    result = await book_repo.find_by_isbn("0000000000000")
    assert result is None


@pytest.mark.asyncio
async def test_create_and_get_book(book_repo: BookRepository):
    """Созданная книга должна быть доступна по ID."""
    from datetime import datetime
    book = await book_repo.create(
        title="Test Book",
        author="Author",
        year=2020,
        genre="Fiction",
        pages=100,
    )
    assert book.book_id is not None
    assert book.title == "Test Book"

    fetched = await book_repo.get_by_id(book.book_id)
    assert fetched is not None
    assert fetched.title == "Test Book"


@pytest.mark.asyncio
async def test_count_by_filters_empty(book_repo: BookRepository):
    """Count по несуществующему автору должен вернуть 0."""
    count = await book_repo.count_by_filters(author="NonExistentAuthor_xyz")
    assert count == 0


@pytest.mark.asyncio
async def test_find_by_filters_ordering(book_repo: BookRepository):
    """find_by_filters должен возвращать результаты, отсортированные по created_at DESC."""
    await book_repo.create(title="First Book", author="Author", year=2019, genre="Fiction", pages=50)
    await book_repo.create(title="Second Book", author="Author", year=2020, genre="Fiction", pages=60)

    results = await book_repo.find_by_filters(author="Author")
    assert len(results) >= 2
    # Последняя созданная книга должна идти первой
    assert results[0].created_at >= results[1].created_at
