import httpx

from ...core.config import settings
from ...domain.exceptions import OpenLibraryException, OpenLibraryTimeoutException
from ..base.base_client import BaseApiClient
from .schemas import OpenLibrarySearchDoc, OpenLibrarySearchResponse


class OpenLibraryClient(BaseApiClient):
    """Клиент для Open Library API."""

    def __init__(
        self,
        base_url: str = settings.openlibrary_base_url,
        timeout: float = settings.openlibrary_timeout,
    ):
        super().__init__(base_url, timeout=timeout)

    def client_name(self) -> str:
        return "openlibrary"

    async def search_by_isbn(self, isbn: str) -> dict:
        """
        Поиск книги по ISBN.

        Args:
            isbn: ISBN-10 или ISBN-13

        Returns:
            dict: Данные книги (cover_url, subjects, etc.)

        Raises:
            OpenLibraryException: При ошибке API
            OpenLibraryTimeoutException: При таймауте
        """
        try:
            raw = await self._get(
                "/search.json",
                params={"isbn": isbn, "limit": 1},
            )
            response = OpenLibrarySearchResponse(**raw)
            if not response.docs:
                return {}
            return self._extract_book_data(response.docs[0])

        except httpx.TimeoutException:
            raise OpenLibraryTimeoutException(self.timeout)
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e))

    async def search_by_title_author(self, title: str, author: str) -> dict:
        """
        Поиск по названию и автору.

        Returns:
            dict: Данные книги или пустой словарь
        """
        try:
            raw = await self._get(
                "/search.json",
                params={"title": title, "author": author, "limit": 1},
            )
            response = OpenLibrarySearchResponse(**raw)
            if not response.docs:
                return {}
            return self._extract_book_data(response.docs[0])

        except httpx.TimeoutException:
            raise OpenLibraryTimeoutException(self.timeout)
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e))

    async def enrich(
        self,
        title: str,
        author: str,
        isbn: str | None = None,
    ) -> dict:
        """
        Обогатить данные книги.

        Сначала пытается найти по ISBN, затем по title+author.

        Returns:
            dict: Обогащенные данные или пустой словарь
        """
        if isbn:
            data = await self.search_by_isbn(isbn)
            if data:
                return data

        return await self.search_by_title_author(title, author)

    def _get_cover_url(self, cover_id: int | None) -> str | None:
        """Получить URL обложки."""
        if not cover_id:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

    def _extract_book_data(self, doc: OpenLibrarySearchDoc) -> dict:
        """
        Извлечь нужные поля из ответа Open Library.

        Args:
            doc: Документ из массива docs

        Returns:
            dict: Обработанные данные
        """
        result = {}

        if doc.cover_i:
            result["cover_url"] = self._get_cover_url(doc.cover_i)

        if doc.subject:
            result["subjects"] = doc.subject[:10]

        if doc.publisher:
            result["publisher"] = doc.publisher[0]

        if doc.language:
            result["language"] = doc.language[0]

        if doc.ratings_average:
            result["rating"] = doc.ratings_average

        return result
