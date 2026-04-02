from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.book import Book
from .base_repository import BaseRepository


class BookRepository(BaseRepository[Book]):
    """Репозиторий для работы с книгами."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)

    def _build_filter_stmt(
        self,
        base_stmt: Select,
        title: str | None,
        author: str | None,
        genre: str | None,
        year: int | None,
        available: bool | None,
    ) -> Select:
        """Построить WHERE-условия для фильтрации книг."""
        if title:
            base_stmt = base_stmt.where(Book.title.ilike(f"%{title}%"))
        if author:
            base_stmt = base_stmt.where(Book.author.ilike(f"%{author}%"))
        if genre:
            base_stmt = base_stmt.where(Book.genre == genre)
        if year is not None:
            base_stmt = base_stmt.where(Book.year == year)
        if available is not None:
            base_stmt = base_stmt.where(Book.available == available)
        return base_stmt

    async def find_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Book]:
        """Поиск книг с фильтрацией."""
        stmt = self._build_filter_stmt(select(Book), title, author, genre, year, available)
        stmt = stmt.order_by(Book.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_isbn(self, isbn: str) -> Book | None:
        """Найти книгу по ISBN."""
        result = await self.session.execute(
            select(Book).where(Book.isbn == isbn)
        )
        return result.scalar_one_or_none()

    async def count_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> int:
        """Подсчитать количество книг по фильтрам."""
        stmt = self._build_filter_stmt(
            select(func.count()).select_from(Book), title, author, genre, year, available
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
