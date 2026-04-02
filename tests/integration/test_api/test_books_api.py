import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health check должен вернуть 200 при работающей БД."""
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_create_book(client: AsyncClient):
    """Создание книги должно вернуть 201 с данными книги."""
    payload = {
        "title": "Clean Code",
        "author": "Robert Martin",
        "year": 2008,
        "genre": "Programming",
        "pages": 464,
        "isbn": "9780132350884",
    }
    response = await client.post("/api/v1/books/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Clean Code"
    assert data["author"] == "Robert Martin"
    assert "book_id" in data


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn(client: AsyncClient):
    """Создание книги с дублирующим ISBN должно вернуть 409."""
    payload = {
        "title": "Test Book",
        "author": "Author",
        "year": 2020,
        "genre": "Fiction",
        "pages": 100,
        "isbn": "9780132350884",
    }
    await client.post("/api/v1/books/", json=payload)
    response = await client.post("/api/v1/books/", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_book_not_found(client: AsyncClient):
    """Запрос несуществующей книги должен вернуть 404."""
    import uuid
    response = await client.get(f"/api/v1/books/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_books_list(client: AsyncClient):
    """Список книг должен вернуть пагинированный ответ."""
    response = await client.get("/api/v1/books/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_create_book_future_year(client: AsyncClient):
    """Год в будущем должен вернуть 422."""
    payload = {
        "title": "Future Book",
        "author": "Author",
        "year": 2099,
        "genre": "Fiction",
        "pages": 100,
    }
    response = await client.post("/api/v1/books/", json=payload)
    assert response.status_code == 422
