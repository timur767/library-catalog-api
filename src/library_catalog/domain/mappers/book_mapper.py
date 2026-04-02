from ...api.v1.schemas.book import ShowBook
from ...data.models.book import Book


def to_show_book(book: Book) -> ShowBook:
    """Преобразовать Book ORM модель в ShowBook DTO."""
    return ShowBook.model_validate(book)


def to_show_books(books: list[Book]) -> list[ShowBook]:
    """Преобразовать список книг."""
    return [to_show_book(b) for b in books]
