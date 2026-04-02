import logging
from uuid import UUID

from ...api.v1.schemas.book import BookCreate, BookUpdate, ShowBook
from ...data.repositories.book_repository import BookRepository
from ...external.openlibrary.client import OpenLibraryClient
from ..exceptions import (
    BookAlreadyExistsException,
    BookNotFoundException,
    OpenLibraryException,
)
from ..mappers import book_mapper

logger = logging.getLogger(__name__)


class BookService:
    """
    Сервис для работы с книгами.

    Содержит всю бизнес-логику приложения.
    """

    def __init__(
        self,
        book_repository: BookRepository,
        openlibrary_client: OpenLibraryClient,
    ):
        self.book_repo = book_repository
        self.ol_client = openlibrary_client

    async def create_book(self, book_data: BookCreate) -> ShowBook:
        """
        Создать новую книгу с обогащением из Open Library.

        Бизнес-правила:
        - ISBN уникален (если указан)

        Raises:
            BookAlreadyExistsException: Если ISBN уже существует
        """
        if book_data.isbn:
            existing = await self.book_repo.find_by_isbn(book_data.isbn)
            if existing:
                raise BookAlreadyExistsException(book_data.isbn)

        extra = await self._enrich_book_data(book_data)

        book = await self.book_repo.create(
            title=book_data.title,
            author=book_data.author,
            year=book_data.year,
            genre=book_data.genre,
            pages=book_data.pages,
            isbn=book_data.isbn,
            description=book_data.description,
            extra=extra,
        )

        return book_mapper.to_show_book(book)

    async def get_book(self, book_id: UUID) -> ShowBook:
        """
        Получить книгу по ID.

        Raises:
            BookNotFoundException: Если книга не найдена
        """
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFoundException(book_id)

        return book_mapper.to_show_book(book)

    async def update_book(self, book_id: UUID, book_data: BookUpdate) -> ShowBook:
        """
        Обновить книгу.

        Обновляются только переданные поля.
        """
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFoundException(book_id)

        updated = await self.book_repo.update(book, **book_data.model_dump(exclude_unset=True))

        return book_mapper.to_show_book(updated)

    async def delete_book(self, book_id: UUID) -> None:
        """
        Удалить книгу.

        Raises:
            BookNotFoundException: Если книга не найдена
        """
        deleted = await self.book_repo.delete(book_id)
        if not deleted:
            raise BookNotFoundException(book_id)

    async def search_books(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ShowBook], int]:
        """
        Поиск книг с фильтрацией и пагинацией.

        Returns:
            tuple: (список книг, общее количество)
        """
        books = await self.book_repo.find_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
            limit=limit,
            offset=offset,
        )

        total = await self.book_repo.count_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )

        return book_mapper.to_show_books(books), total

    # ========== ПРИВАТНЫЕ МЕТОДЫ ==========

    async def _enrich_book_data(self, book_data: BookCreate) -> dict | None:
        """
        Обогатить данные книги из Open Library.

        Не выбрасывает исключение если API недоступен.
        """
        try:
            extra = await self.ol_client.enrich(
                title=book_data.title,
                author=book_data.author,
                isbn=book_data.isbn,
            )
            return extra if extra else None
        except OpenLibraryException:
            logger.warning(
                "Failed to enrich book data from Open Library",
                extra={"title": book_data.title, "author": book_data.author},
            )
            return None
