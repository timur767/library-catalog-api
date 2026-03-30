# 📚 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Library Catalog API

## Полное руководство по разработке REST API на FastAPI с правильной архитектурой


---

## 📋 СОДЕРЖАНИЕ

1. [Введение](#введение)
2. [Архитектура приложения](#архитектура-приложения)
3. [Структура проекта](#структура-проекта)
4. [Задание 1: Начальная настройка](#задание-1)
5. [Задание 2: Работа с PostgreSQL](#задание-2)
6. [Задание 3: Бизнес-логика](#задание-3)
7. [Задание 4: Внешние API](#задание-4)
8. [Задание 5: API Layer и эндпоинты](#задание-5)
9. [Критерии приемки](#критерии-приемки)
10. [Типичные ошибки](#типичные-ошибки)

---

## 🎯 ВВЕДЕНИЕ

### Что вы будете разрабатывать

REST API для управления библиотечным каталогом с функциями:
- ✅ CRUD операции с книгами
- ✅ Поиск и фильтрация
- ✅ Автоматическое обогащение данных из Open Library
- ✅ Хранение в PostgreSQL
- ✅ Пагинация результатов
- ✅ Правильная обработка ошибок

### Технологии

| Компонент     | Технология | Версия           | Зачем                                                                        |
|---------------|------------|------------------|------------------------------------------------------------------------------|
| Web Framework | FastAPI    | 0.109+           | Быстрый async framework с автодокументацией                                  |
| ASGI Server   | Uvicorn    | 0.27+            | Запуск async приложения                                                      |
| Database      | PostgreSQL | 16+              | Production-ready СУБД                                                        |
| ORM           | SQLAlchemy | 2.0+             | Async работа с БД                                                            |
| Migrations    | Alembic    | 1.13+            | Версионирование схемы БД                                                     |
| Validation    | Pydantic   | 2.5+             | Валидация через типы                                                         |
| HTTP Client   | httpx      | 0.26+            | Async HTTP запросы                                                           |
| Зависимости   | Poetry     | Последняя версия | Управление зависимости и виртуальным окружением на работе и больших проектах |

### Цели обучения

После выполнения заданий вы будете уметь:
1. ✅ Проектировать многослойную архитектуру
2. ✅ Работать с async/await в Python
3. ✅ Использовать PostgreSQL и SQLAlchemy 2.0
4. ✅ Применять паттерны: Repository, Service Layer, DI
5. ✅ Интегрироваться с внешними API
6. ✅ Писать чистый, поддерживаемый код
7. ✅ Создавать миграции базы данных
8. ✅ Тестировать API

---

## 🏗️ АРХИТЕКТУРА ПРИЛОЖЕНИЯ

### Принципы многослойной архитектуры

Ваше приложение должно состоять из **четырех независимых слоев**:

```
┌──────────────────────────────────────────────────────┐
│              1. API LAYER (api/)                     │
│  HTTP endpoints, валидация запросов/ответов          │
│  ❌ НЕТ бизнес-логики, НЕТ работы с БД              │
└────────────────────┬─────────────────────────────────┘
                     │ вызывает
                     ▼
┌──────────────────────────────────────────────────────┐
│            2. DOMAIN LAYER (domain/)                 │
│  Бизнес-логика, правила, координация                │
│  ✅ Вся логика приложения здесь                     │
└──────────────┬───────────────┬───────────────────────┘
               │               │
               │ использует    │ использует
               ▼               ▼
┌──────────────────────┐  ┌──────────────────────┐
│  3. DATA LAYER       │  │  4. EXTERNAL LAYER   │
│  (data/)             │  │  (external/)         │
│  Работа с БД         │  │  Внешние API         │
│  CRUD, запросы       │  │  HTTP клиенты        │
└──────────────────────┘  └──────────────────────┘
```

### Подробное описание слоев

#### Слой 1: API Layer (`api/`)

**Ответственность:**
- Принимать HTTP запросы
- Валидировать входные данные (Pydantic schemas)
- Вызывать сервисы для выполнения операций
- Форматировать HTTP ответы
- Обрабатывать HTTP исключения

**Что НЕ делает:**
- ❌ Бизнес-логику (валидацию правил, вычисления)
- ❌ Напрямую работает с БД
- ❌ Создает репозитории или клиенты внутри роутеров
- ❌ Содержит сложную логику

**Пример правильного роутера:**
```python
# ✅ ПРАВИЛЬНО: Тонкий роутер
@router.post("/", response_model=ShowBook, status_code=201)
async def create_book(
    book_data: BookCreate,
    service: Annotated[BookService, Depends(get_book_service)],
):
    """Создать новую книгу."""
    return await service.create_book(book_data)
```

**Пример НЕПРАВИЛЬНОГО роутера:**
```python
# ❌ НЕПРАВИЛЬНО: Логика в роутере
@router.post("/")
async def create_book(book_data: BookCreate, db: Session = Depends(get_db)):
    # ❌ Создание клиента внутри роутера
    ol_client = OpenLibraryClient()
    
    # ❌ Бизнес-логика в роутере
    if book_data.year > 2024:
        raise HTTPException(400, "Year cannot be in future")
    
    # ❌ Обогащение данных в роутере
    extra = ol_client.search(book_data.title)
    
    # ❌ Прямая работа с БД в роутере
    book = Book(**book_data.dict(), extra=extra)
    db.add(book)
    db.commit()
    return book
```

---

#### Слой 2: Domain Layer (`domain/`)

**Ответственность:**
- Содержит ВСЮ бизнес-логику приложения
- Валидирует бизнес-правила
- Координирует работу репозиториев и внешних клиентов
- Выполняет сложные операции (обогащение данных, расчеты)

**Что делает:**
- ✅ Проверяет бизнес-правила (год не в будущем, страницы > 0)
- ✅ Координирует несколько репозиториев
- ✅ Вызывает внешние API для обогащения данных
- ✅ Выполняет трансформации данных

**Пример правильного сервиса:**
```python
# ✅ ПРАВИЛЬНО: Бизнес-логика в сервисе
class BookService:
    def __init__(
        self,
        book_repo: BookRepository,
        ol_client: OpenLibraryClient,
    ):
        self.book_repo = book_repo
        self.ol_client = ol_client
    
    async def create_book(self, book_data: BookCreate) -> ShowBook:
        # Валидация бизнес-правил
        self._validate_book_data(book_data)
        
        # Обогащение из внешнего API
        extra = await self.ol_client.enrich(
            title=book_data.title,
            author=book_data.author,
            isbn=book_data.isbn
        )
        
        # Работа с БД через репозиторий
        book = await self.book_repo.create(
            **book_data.dict(),
            extra=extra
        )
        
        # Маппинг в DTO
        return BookMapper.to_show_book(book)
    
    def _validate_book_data(self, data: BookCreate) -> None:
        from datetime import datetime
        
        if data.year > datetime.now().year:
            raise InvalidYearException(data.year)
        
        if data.pages <= 0:
            raise InvalidPagesException(data.pages)
```

---

#### Слой 3: Data Layer (`data/`)

**Ответственность:**
- CRUD операции с базой данных
- Построение SQL запросов
- Фильтрация, сортировка, пагинация

**Что НЕ делает:**
- ❌ Бизнес-логику
- ❌ HTTP обработку
- ❌ Вызовы внешних API

**Пример правильного репозитория:**
```python
# ✅ ПРАВИЛЬНО: Только работа с БД
class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, **kwargs) -> Book:
        book = Book(**kwargs)
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book
    
    async def get_by_id(self, book_id: UUID) -> Book | None:
        result = await self.session.get(Book, book_id)
        return result
    
    async def find_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Book]:
        stmt = select(Book)
        
        if title:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))
        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))
        if genre:
            stmt = stmt.where(Book.genre == genre)
        if available is not None:
            stmt = stmt.where(Book.available == available)
        
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

---

#### Слой 4: External Layer (`external/`)

**Ответственность:**
- HTTP запросы к внешним API
- Обработка ответов от внешних сервисов
- Retry логика и обработка ошибок
- Кэширование (опционально)

**Пример правильного клиента:**
```python
# ✅ ПРАВИЛЬНО: Изолированная логика внешнего API
class OpenLibraryClient(BaseApiClient):
    async def search_by_isbn(self, isbn: str) -> dict:
        try:
            data = await self._get(
                "/search.json",
                params={"isbn": isbn, "limit": 1}
            )
            docs = data.get("docs", [])
            if not docs:
                return {}
            
            return self._extract_book_data(docs[0])
        
        except httpx.TimeoutException:
            raise OpenLibraryTimeoutException(timeout=self.timeout)
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e))
    
    def _extract_book_data(self, doc: dict) -> dict:
        return {
            "cover_url": self._get_cover_url(doc.get("cover_i")),
            "subjects": doc.get("subject", []),
            "publisher": doc.get("publisher"),
        }
```

---

## 📁 СТРУКТУРА ПРОЕКТА

### Полная структура файлов (что нужно создать)

```
library_catalog/
│
├── README.md                         # ← Создать: описание проекта
├── pyproject.toml                    # ← Создать: зависимости Poetry
├── .env.example                      # ← Создать: пример конфигурации
├── .gitignore                        # ← Создать для игнора добавления в GIT
├── docker-compose.yml                # ← Создать: PostgreSQL в Docker
├── alembic.ini                       # ← Создать: конфиг Alembic
│
├── src/
│   └── library_catalog/
│       ├── __init__.py
│       ├── main.py                   # ← Создать: точка входа
│       │
│       ├── api/                      # API LAYER
│       │   ├── __init__.py
│       │   ├── dependencies.py       # ← Создать: DI контейнер
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── routers/
│       │       │   ├── __init__.py
│       │       │   ├── books.py      # ← Создать: CRUD эндпоинты
│       │       │   └── health.py     # ← Создать: health check
│       │       └── schemas/
│       │           ├── __init__.py
│       │           ├── book.py       # ← Создать: Pydantic схемы
│       │           └── common.py     # ← Создать: пагинация
│       │
│       ├── core/                     # CORE
│       │   ├── __init__.py
│       │   ├── config.py             # ← Создать: Settings
│       │   ├── database.py           # ← Создать: async engine
│       │   ├── logging_config.py     # ← Создать: логирование
│       │   └── exceptions.py         # ← Создать: базовые исключения
│       │
│       ├── data/                     # DATA LAYER
│       │   ├── __init__.py
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   └── book.py           # ← Создать: SQLAlchemy модель
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── base_repository.py # ← Создать: базовый класс
│       │       └── book_repository.py # ← Создать: CRUD для книг
│       │
│       ├── domain/                   # DOMAIN LAYER
│       │   ├── __init__.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   └── book_service.py   # ← Создать: бизнес-логика
│       │   ├── exceptions.py         # ← Создать: доменные ошибки
│       │   └── mappers/
│       │       ├── __init__.py
│       │       └── book_mapper.py    # ← Создать: Entity ↔ DTO
│       │
│       ├── external/                 # EXTERNAL LAYER
│       │   ├── __init__.py
│       │   ├── base/
│       │   │   ├── __init__.py
│       │   │   └── base_client.py    # ← Создать: HTTP базовый клиент
│       │   ├── openlibrary/
│       │   │   ├── __init__.py
│       │   │   ├── client.py         # ← Создать: Open Library API
│       │   │   └── schemas.py        # ← Создать: схемы ответов
│       │   └── jsonbin/              # Опционально
│       │       ├── __init__.py
│       │       └── client.py
│       │
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
│
├── alembic/
│   ├── versions/                     # ← Миграции создаются автоматически
│   ├── env.py                        # ← Настроить для async
│   └── script.py.mako
│
└── tests/
    ├── __init__.py
    ├── conftest.py                   # ← Создать: фикстуры pytest
    ├── unit/
    │   ├── test_services/
    │   │   └── test_book_service.py  # ← Создать: тесты сервиса
    │   └── test_repositories/
    │       └── test_book_repository.py
    └── integration/
        └── test_api/
            └── test_books_api.py     # ← Создать: тесты API
```

### Важные правила

1. **Один файл = Одна ответственность**
2. **Имена файлов = snake_case**
3. **Имена классов = PascalCase**
4. **Имена функций/переменных = snake_case**
5. **Константы = UPPER_CASE**

---

## 📝 ЗАДАНИЕ 1: Начальная настройка проекта

### Цель
Создать минимальное работающее FastAPI приложение с правильной структурой.

### Шаги выполнения

#### Шаг 1.1: Инициализировать Poetry проект

**⚠️ ВАЖНО: Выполняйте команды в правильном порядке и из правильной директории!**

```bash
# Шаг 1: Создать корневую директорию проекта
mkdir library_catalog
cd library_catalog

# Шаг 2: Инициализировать Poetry (ОБЯЗАТЕЛЬНО из корневой директории library_catalog/)
poetry init --no-interaction --name library_catalog --python "^3.11"

# Шаг 3: Создать виртуальное окружение
poetry env use python3.11
```

#### Шаг 1.2: Установить зависимости через Poetry

**⚠️ ВАЖНО: Убедитесь что вы находитесь в директории `library_catalog/`**

```bash
# Установить основные зависимости
poetry add fastapi uvicorn[standard] sqlalchemy alembic asyncpg pydantic pydantic-settings httpx python-dotenv

# Установить dev зависимости
poetry add --group dev pytest pytest-asyncio black ruff mypy
```

#### Шаг 1.3: Создать структуру директорий

**⚠️ ВАЖНО: Все команды ниже выполняются из корневой директории `library_catalog/`**

```bash
# Создать структуру проекта
mkdir -p src/library_catalog/{api/v1/{routers,schemas},core,data/{models,repositories},domain/{services,mappers},external/{base,openlibrary},utils}
mkdir -p tests/{unit,integration}
mkdir -p alembic/versions

# Создать __init__.py файлы
touch src/library_catalog/__init__.py
touch src/library_catalog/api/__init__.py
touch src/library_catalog/api/v1/__init__.py
touch src/library_catalog/api/v1/routers/__init__.py
touch src/library_catalog/api/v1/schemas/__init__.py
touch src/library_catalog/core/__init__.py
touch src/library_catalog/data/__init__.py
touch src/library_catalog/data/models/__init__.py
touch src/library_catalog/data/repositories/__init__.py
touch src/library_catalog/domain/__init__.py
touch src/library_catalog/domain/services/__init__.py
touch src/library_catalog/domain/mappers/__init__.py
touch src/library_catalog/external/__init__.py
touch src/library_catalog/external/base/__init__.py
touch src/library_catalog/external/openlibrary/__init__.py
touch src/library_catalog/utils/__init__.py
touch tests/__init__.py
```

#### Шаг 1.4: Создать `.env.example`

```bash
# .env.example
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/library_catalog
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO
```

Скопировать в `.env`:
```bash
cp .env.example .env
```

#### Шаг 1.5: Создать `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: library_catalog_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: library_catalog
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Запустить PostgreSQL:
```bash
docker-compose up -d postgres
```

#### Шаг 1.6: Создать минимальный `main.py`

```python
# src/library_catalog/main.py
"""
Точка входа FastAPI приложения Library Catalog.
"""

from fastapi import FastAPI

# Создать приложение
app = FastAPI(
    title="Library Catalog API",
    description="REST API для управления библиотечным каталогом",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Welcome to Library Catalog API"}


@app.get("/health")
async def health_check():
    """Health check эндпоинт."""
    return {"status": "healthy"}


# Для запуска через python -m
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Шаг 1.7: Запустить и проверить

```bash
# Запустить сервер
uvicorn src.library_catalog.main:app --reload

# Открыть в браузере
# http://127.0.0.1:8000/docs    - Swagger UI
# http://127.0.0.1:8000/redoc   - ReDoc
# http://127.0.0.1:8000/health  - Health check
```

### Критерии успешности Задания 1

- [x] Создана структура директорий
- [x] Установлены все зависимости
- [x] PostgreSQL запущен в Docker
- [x] FastAPI приложение запускается
- [x] Swagger доступен по /docs
- [x] Health check работает

---

## 💾 ЗАДАНИЕ 2: Работа с PostgreSQL и SQLAlchemy

### Цель
Настроить подключение к БД, создать ORM модели, реализовать Repository Pattern.

### Часть 2.1: Настройка конфигурации

#### Создать `src/library_catalog/core/config.py`

**Требования:**
- Использовать `pydantic-settings` для загрузки из .env
- Валидировать DATABASE_URL (только PostgreSQL)
- Типизировать все настройки
- Создать метод `get_settings()` с `@lru_cache`

**Обязательные поля:**
- `app_name: str = "Library Catalog API"`
- `environment: Literal["development", "staging", "production"]`
- `debug: bool`
- `database_url: PostgresDsn`
- `database_pool_size: int = 20`
- `api_v1_prefix: str = "/api/v1"`
- `log_level: str = "INFO"`
- `docs_url: str = "/docs"`
- `redoc_url: str = "/redoc"`
- `cors_origins: list[str] = ["*"]`
- `openlibrary_base_url: str = "https://openlibrary.org"`
- `openlibrary_timeout: float = 10.0`

**📝 Примечание:** Эти атрибуты будут постепенно добавляться по ходу выполнения заданий. Не все из них нужны сразу - начните с базовых (app_name, environment, debug, database_url), а остальные добавите когда они понадобятся в коде.

**Пример структуры:**
```python
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Добавить все поля
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Часть 2.2: Настройка базы данных

#### Создать `src/library_catalog/core/database.py`

**Требования:**
- Использовать `AsyncEngine` и `AsyncSession`
- Создать `Base` класс для моделей
- Реализовать `get_db()` dependency
- Добавить вспомогательные функции (опционально):
  - `init_db()` - для инициализации подключения к БД при старте приложения
  - `check_db_connection()` - для проверки доступности БД
  - `dispose_engine()` - для корректного закрытия соединений при остановке приложения

**📝 Примечание:** Функции `init_db()`, `check_db_connection()` и `dispose_engine()` будут использоваться в основном файле приложения (`main.py`) для управления lifecycle. Их реализация - на ваше усмотрение. Пример будет показан в Задании 5.

**Обязательная структура:**
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Создать engine
engine = create_async_engine(
    settings.database_url_str,
    pool_size=settings.database_pool_size,
    echo=settings.debug,
)

# Создать session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency для FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Часть 2.3: Создание ORM модели

#### Создать `src/library_catalog/data/models/book.py`

**Требования к модели Book:**

**Обязательные поля:**
- `book_id: UUID` - Primary Key, автогенерация
- `title: str` - максимум 500 символов, индекс
- `author: str` - максимум 300 символов, индекс
- `year: int` - индекс
- `genre: str` - максимум 100 символов, индекс
- `pages: int`
- `available: bool` - по умолчанию True, индекс

**Опциональные поля:**
- `isbn: str | None` - UNIQUE, максимум 20 символов
- `description: str | None` - Text без ограничения
- `extra: dict | None` - JSON для доп. данных

**Timestamps:**
- `created_at: datetime` - автоматически при создании
- `updated_at: datetime` - автоматически при обновлении

**Пример структуры:**
```python
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base

class Book(Base):
    __tablename__ = "books"
    
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    
    # ... остальные поля
    
    def __repr__(self) -> str:
        return f"<Book(id={self.book_id}, title='{self.title}')>"
```

**⚠️ ВАЖНО:**
- Используйте `Mapped` и `mapped_column` (SQLAlchemy 2.0 синтаксис)
- UUID хранится как нативный тип PostgreSQL
- Добавьте индексы на часто используемые поля
- Добавьте docstring с описанием модели

### Часть 2.4: Repository Pattern

#### Создать `src/library_catalog/data/repositories/base_repository.py`

**Требования:**
- Generic базовый класс для CRUD операций
- Использовать TypeVar для типизации
- Асинхронные методы

**Обязательные методы:**
```python
from typing import Generic, TypeVar, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> T:
        """Создать запись."""
        pass
    
    async def get_by_id(self, id: UUID) -> T | None:
        """
        Получить по ID.
        
        📝 Примечание: session.get() автоматически работает с primary key модели,
        независимо от его названия (id, book_id, user_id и т.д.)
        """
        pass
    
    async def update(self, id: UUID, **kwargs) -> T | None:
        """Обновить запись."""
        pass
    
    async def delete(self, id: UUID) -> bool:
        """Удалить запись."""
        pass
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[T]:
        """Получить все записи с пагинацией."""
        pass
```

#### Создать `src/library_catalog/data/repositories/book_repository.py`

**Требования:**
- Наследоваться от `BaseRepository[Book]`
- Добавить специфичные методы для книг

**Обязательные дополнительные методы:**
```python
class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)
    
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
        pass
    
    async def find_by_isbn(self, isbn: str) -> Book | None:
        """Найти книгу по ISBN."""
        pass
    
    async def count_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        # ... остальные фильтры
    ) -> int:
        """Подсчитать количество книг по фильтрам."""
        pass
```

**⚠️ ВАЖНО:**
- Используйте `select()` для построения запросов
- Для поиска по подстроке используйте `.ilike(f"%{value}%")`
- Всегда используйте `await` для async операций
- Добавьте обработку `None` значений в фильтрах

### Часть 2.5: Миграции Alembic

#### Настроить Alembic

**⚠️ ВАЖНО: Команда должна выполняться из корневой директории `library_catalog/`**

```bash
# Инициализировать Alembic
alembic init alembic
```

#### Изменить `alembic.ini`

Закомментировать строку с `sqlalchemy.url` в секции `[alembic]`:

```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
# ☝️ Закомментируйте эту строку - мы будем использовать URL из settings
```

#### Изменить `alembic/env.py` для async mode

**⚠️ КРИТИЧЕСКИ ВАЖНО: Для работы с async SQLAlchemy нужна специальная настройка!**

**Требования:**
- Импортировать Base из database
- Импортировать все модели (чтобы Alembic их видел)
- Настроить async режим работы
- Использовать `asyncio.run()` для запуска миграций

**Полный код для `alembic/env.py`:**

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импортировать config и Base
from src.library_catalog.core.config import settings
from src.library_catalog.core.database import Base

# Импортировать все модели (ОБЯЗАТЕЛЬНО!)
from src.library_catalog.data.models import book  # noqa

# this is the Alembic Config object
config = context.config

# Установить database_url из settings
# ⚠️ ВАЖНО: Убираем +asyncpg для alembic, используем postgresql:// вместо postgresql+asyncpg://
config.set_main_option(
    "sqlalchemy.url",
    str(settings.database_url).replace("+asyncpg", "")
)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Установить target_metadata из Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    # Создать async engine из конфигурации
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Ключевые моменты:**
1. ✅ Используется `async_engine_from_config` вместо обычного `engine_from_config`
2. ✅ Миграции запускаются через `asyncio.run()`
3. ✅ URL автоматически модифицируется (убирается `+asyncpg` для alembic)
4. ✅ Импортированы все модели (иначе alembic не увидит таблицы)

#### Создать первую миграцию

```bash
# Создать миграцию автоматически
alembic revision --autogenerate -m "Create books table"

# Применить миграцию
alembic upgrade head

# Проверить текущую версию
alembic current
```

### Критерии успешности Задания 2

- [x] `config.py` создан с валидацией
- [x] `database.py` настроен с async engine
- [x] ORM модель `Book` создана с индексами
- [x] `BaseRepository` реализован
- [x] `BookRepository` с фильтрацией создан
- [x] Alembic настроен и миграция применена
- [x] Таблица `books` создана в PostgreSQL
- [x] Все методы типизированы и async

**Проверка:**
```bash
# Подключиться к PostgreSQL
docker-compose exec postgres psql -U postgres -d library_catalog

# Проверить таблицу
\d books
\q
```

---

## 🧠 ЗАДАНИЕ 3: Domain Layer и бизнес-логика

### Цель
Создать сервисный слой с бизнес-логикой, исключениями и маппингом данных.

### Часть 3.1: Доменные исключения

#### Создать `src/library_catalog/domain/exceptions.py`

**Требования:**
- Наследоваться от базовых исключений из `core.exceptions`
- Содержать специфичную информацию об ошибке

**Обязательные исключения:**
```python
from uuid import UUID
from ..core.exceptions import AppException, NotFoundException

class BookNotFoundException(NotFoundException):
    """Книга не найдена."""
    def __init__(self, book_id: UUID):
        super().__init__(resource="Book", identifier=book_id)

class BookAlreadyExistsException(AppException):
    """Книга с таким ISBN уже существует."""
    def __init__(self, isbn: str):
        super().__init__(
            message=f"Book with ISBN '{isbn}' already exists",
            status_code=409,
        )

class InvalidYearException(AppException):
    """Невалидный год издания."""
    def __init__(self, year: int):
        from datetime import datetime
        current_year = datetime.now().year
        super().__init__(
            message=f"Year {year} is invalid (must be 1000-{current_year})",
            status_code=400,
        )

class InvalidPagesException(AppException):
    """Невалидное количество страниц."""
    def __init__(self, pages: int):
        super().__init__(
            message=f"Pages count must be positive, got {pages}",
            status_code=400,
        )

class OpenLibraryException(AppException):
    """Ошибка Open Library API."""
    def __init__(self, message: str):
        super().__init__(
            message=f"Open Library API error: {message}",
            status_code=503,
        )

class OpenLibraryTimeoutException(AppException):
    """Таймаут при обращении к Open Library API."""
    def __init__(self, timeout: float):
        super().__init__(
            message=f"Open Library API timeout after {timeout}s",
            status_code=504,
        )
```

### Часть 3.2: Mapper для преобразования данных

#### Создать `src/library_catalog/domain/mappers/book_mapper.py`

**Требования:**
- Статические методы для преобразования
- Entity (Book) → DTO (ShowBook)
- Повторное использование логики

**Обязательные методы:**
```python
from ...data.models.book import Book
from ...api.v1.schemas.book import ShowBook

class BookMapper:
    """Маппер для преобразования Book entity в DTO."""
    
    @staticmethod
    def to_show_book(book: Book) -> ShowBook:
        """
        Преобразовать Book ORM модель в ShowBook DTO.
        
        Args:
            book: ORM модель из БД
            
        Returns:
            ShowBook: Pydantic модель для API
        """
        return ShowBook(
            book_id=book.book_id,
            title=book.title,
            author=book.author,
            year=book.year,
            genre=book.genre,
            pages=book.pages,
            available=book.available,
            isbn=book.isbn,
            description=book.description,
            extra=book.extra,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
    
    @staticmethod
    def to_show_books(books: list[Book]) -> list[ShowBook]:
        """Преобразовать список книг."""
        return [BookMapper.to_show_book(book) for book in books]
```

### Часть 3.3: Book Service

**📝 ВАЖНОЕ ПРИМЕЧАНИЕ О КОДЕ НИЖЕ:**

Ниже представлен **полный рабочий код** `BookService` для справки и понимания общей структуры. 

**Вы можете:**
- ✅ Использовать его как есть для быстрого прогресса
- ✅ Реализовать самостоятельно для лучшего понимания
- ✅ Модифицировать под свои нужды

**Рекомендация:** Даже если вы копируете код, убедитесь что понимаете каждую его часть и можете объяснить логику работы.

---

#### Создать `src/library_catalog/domain/services/book_service.py`

**Требования:**
- Содержит ВСЮ бизнес-логику
- Использует репозитории через DI
- Использует external clients через DI
- Валидирует бизнес-правила

**Обязательные методы:**
```python
from uuid import UUID
from ...api.v1.schemas.book import BookCreate, BookUpdate, ShowBook
from ...data.repositories.book_repository import BookRepository
from ...external.openlibrary.client import OpenLibraryClient
from ..exceptions import *
from ..mappers.book_mapper import BookMapper

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
        - Год не в будущем
        - Страницы > 0
        - ISBN уникален (если указан)
        
        Args:
            book_data: Данные для создания
            
        Returns:
            ShowBook: Созданная книга
            
        Raises:
            InvalidYearException: Если год невалиден
            InvalidPagesException: Если страницы <= 0
            BookAlreadyExistsException: Если ISBN уже существует
        """
        # 1. Валидация бизнес-правил
        self._validate_book_data(book_data)
        
        # 2. Проверка уникальности ISBN
        if book_data.isbn:
            existing = await self.book_repo.find_by_isbn(book_data.isbn)
            if existing:
                raise BookAlreadyExistsException(book_data.isbn)
        
        # 3. Обогащение данных из Open Library
        extra = await self._enrich_book_data(book_data)
        
        # 4. Создание в БД
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
        
        # 5. Маппинг в DTO
        return BookMapper.to_show_book(book)
    
    async def get_book(self, book_id: UUID) -> ShowBook:
        """
        Получить книгу по ID.
        
        Raises:
            BookNotFoundException: Если книга не найдена
        """
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFoundException(book_id)
        
        return BookMapper.to_show_book(book)
    
    async def update_book(
        self,
        book_id: UUID,
        book_data: BookUpdate,
    ) -> ShowBook:
        """
        Обновить книгу.
        
        Обновляются только переданные поля.
        """
        # Проверить существование
        existing = await self.book_repo.get_by_id(book_id)
        if existing is None:
            raise BookNotFoundException(book_id)
        
        # Валидация если обновляется год/страницы
        if book_data.year is not None:
            self._validate_year(book_data.year)
        if book_data.pages is not None:
            self._validate_pages(book_data.pages)
        
        # Обновить
        updated = await self.book_repo.update(
            book_id,
            **book_data.dict(exclude_unset=True)
        )
        
        return BookMapper.to_show_book(updated)
    
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
        # Получить книги
        books = await self.book_repo.find_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
            limit=limit,
            offset=offset,
        )
        
        # Подсчитать общее количество
        total = await self.book_repo.count_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )
        
        return BookMapper.to_show_books(books), total
    
    # ========== ПРИВАТНЫЕ МЕТОДЫ ==========
    
    def _validate_book_data(self, data: BookCreate) -> None:
        """Валидация бизнес-правил для новой книги."""
        self._validate_year(data.year)
        self._validate_pages(data.pages)
    
    def _validate_year(self, year: int) -> None:
        """Проверить что год валиден."""
        from datetime import datetime
        
        current_year = datetime.now().year
        if year < 1000 or year > current_year:
            raise InvalidYearException(year)
    
    def _validate_pages(self, pages: int) -> None:
        """Проверить что количество страниц валидно."""
        if pages <= 0:
            raise InvalidPagesException(pages)
    
    async def _enrich_book_data(
        self,
        book_data: BookCreate
    ) -> dict | None:
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
            # Логируем но не прерываем создание книги
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Failed to enrich book data from Open Library",
                extra={"title": book_data.title, "author": book_data.author}
            )
            return None
```

**⚠️ ВАЖНО:**
- Все валидации в сервисе, НЕ в роутере
- Обогащение данных не должно прерывать создание книги
- Используйте маппер для преобразований
- Все методы async

### Критерии успешности Задания 3

- [x] Доменные исключения созданы
- [x] `BookMapper` реализован
- [x] `BookService` содержит всю логику
- [x] Валидация бизнес-правил в сервисе
- [x] Обогащение через external client
- [x] Все методы типизированы и задокументированы

---

## 🌐 ЗАДАНИЕ 4: External API и интеграция

### Цель
Создать клиент для Open Library API с правильной обработкой ошибок и retry логикой.

### Часть 4.1: Базовый HTTP клиент

#### Создать `src/library_catalog/external/base/base_client.py`

**Требования:**
- Абстрактный базовый класс
- Retry логика с exponential backoff
- Единая обработка ошибок
- Timeout management
- Логирование

**Обязательная структура:**
```python
from abc import ABC, abstractmethod
import httpx
import logging
import time

class BaseApiClient(ABC):
    """
    Базовый класс для HTTP клиентов внешних API.
    
    Включает:
    - Retry логику
    - Обработку ошибок
    - Логирование
    - Timeout management
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        retries: int = 3,
        backoff: float = 0.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self.logger = logging.getLogger(self.client_name())
    
    @abstractmethod
    def client_name(self) -> str:
        """Имя клиента для логирования."""
        pass
    
    def _build_url(self, path: str) -> str:
        """Построить полный URL."""
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path
    
    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """
        Выполнить HTTP запрос с retry логикой.
        
        Raises:
            httpx.TimeoutException: При таймауте
            httpx.HTTPError: При HTTP ошибке
        """
        url = self._build_url(path)
        
        for attempt in range(self.retries):
            try:
                self.logger.debug(f"{method} {url} params={params}")
                
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                )
                
                response.raise_for_status()
                return response.json()
            
            except httpx.TimeoutException:
                if attempt == self.retries - 1:
                    self.logger.error(f"Timeout after {self.retries} attempts")
                    raise
                
                wait_time = self.backoff * (2 ** attempt)
                self.logger.warning(f"Timeout, retrying in {wait_time}s...")
                time.sleep(wait_time)
            
            except httpx.HTTPStatusError as e:
                # 5xx ошибки - retry
                if e.response.status_code >= 500 and attempt < self.retries - 1:
                    wait_time = self.backoff * (2 ** attempt)
                    self.logger.warning(f"Server error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"HTTP error: {e}")
                    raise
    
    async def _get(self, path: str, **kwargs) -> dict:
        """GET запрос."""
        return await self._request("GET", path, **kwargs)
    
    async def close(self) -> None:
        """Закрыть HTTP клиент."""
        await self._client.aclose()
```

### Часть 4.2: Open Library Client

#### Создать `src/library_catalog/external/openlibrary/client.py`

**Требования:**
- Наследоваться от `BaseApiClient`
- Поиск по ISBN
- Поиск по title + author
- Извлечение cover URL, subjects, description

**Обязательные методы:**
```python
from ..base.base_client import BaseApiClient
from ...domain.exceptions import OpenLibraryException, OpenLibraryTimeoutException

class OpenLibraryClient(BaseApiClient):
    """Клиент для Open Library API."""
    
    def __init__(
        self,
        base_url: str = "https://openlibrary.org",
        timeout: float = 10.0,
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
        """
        try:
            data = await self._get(
                "/search.json",
                params={"isbn": isbn, "limit": 1}
            )
            
            docs = data.get("docs", [])
            if not docs:
                return {}
            
            return self._extract_book_data(docs[0])
        
        except httpx.TimeoutException:
            raise OpenLibraryTimeoutException(self.timeout)
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e))
    
    async def search_by_title_author(
        self,
        title: str,
        author: str
    ) -> dict:
        """Поиск по названию и автору."""
        try:
            data = await self._get(
                "/search.json",
                params={
                    "title": title,
                    "author": author,
                    "limit": 1
                }
            )
            
            docs = data.get("docs", [])
            if not docs:
                return {}
            
            return self._extract_book_data(docs[0])
        
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
        # Попытка 1: По ISBN
        if isbn:
            data = await self.search_by_isbn(isbn)
            if data:
                return data
        
        # Попытка 2: По title + author
        return await self.search_by_title_author(title, author)
    
    def _extract_book_data(self, doc: dict) -> dict:
        """
        Извлечь нужные поля из ответа Open Library.
        
        Args:
            doc: Документ из массива docs
            
        Returns:
            dict: Обработанные данные
        """
        result = {}
        
        # Cover URL
        if cover_id := doc.get("cover_i"):
            result["cover_url"] = (
                f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            )
        
        # Subjects (темы)
        if subjects := doc.get("subject"):
            result["subjects"] = subjects[:10]  # Первые 10
        
        # Publisher
        if publisher := doc.get("publisher"):
            result["publisher"] = publisher[0] if publisher else None
        
        # Language
        if language := doc.get("language"):
            result["language"] = language[0] if language else None
        
        # Ratings
        if ratings := doc.get("ratings_average"):
            result["rating"] = ratings
        
        return result
    
    def _get_cover_url(self, cover_id: int | None) -> str | None:
        """Получить URL обложки."""
        if not cover_id:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
```

#### Создать `src/library_catalog/external/openlibrary/schemas.py`

**Требования:**
- Pydantic модели для ответов Open Library
- Валидация данных

```python
from pydantic import BaseModel, Field

class OpenLibrarySearchDoc(BaseModel):
    """Документ из поиска Open Library."""
    
    title: str
    author_name: list[str] | None = Field(None, alias="author_name")
    cover_i: int | None = Field(None, alias="cover_i")
    subject: list[str] | None = None
    publisher: list[str] | None = None
    language: list[str] | None = None
    ratings_average: float | None = Field(None, alias="ratings_average")
    
    class Config:
        populate_by_name = True


class OpenLibrarySearchResponse(BaseModel):
    """Ответ от /search.json"""
    
    numFound: int
    docs: list[OpenLibrarySearchDoc]
```

### Критерии успешности Задания 4

- [x] `BaseApiClient` создан с retry логикой
- [x] `OpenLibraryClient` наследуется от base
- [x] Поиск по ISBN реализован
- [x] Поиск по title+author реализован
- [x] Метод `enrich()` работает
- [x] Обработка ошибок (timeout, HTTP errors)
- [x] Логирование запросов

**Тест:**
```python
# Проверить работу клиента
import asyncio

async def test():
    client = OpenLibraryClient()
    
    # Тест по ISBN
    data = await client.search_by_isbn("9780132350884")
    print(f"Found: {data}")
    
    # Тест по title+author
    data = await client.search_by_title_author(
        "Clean Code",
        "Robert Martin"
    )
    print(f"Found: {data}")
    
    await client.close()

asyncio.run(test())
```

---

## 📡 ЗАДАНИЕ 5: API Layer и эндпоинты

### Цель
Создать HTTP endpoints с правильной структурой, валидацией и Dependency Injection.

### Часть 5.1: Pydantic схемы

#### Создать `src/library_catalog/api/v1/schemas/book.py`

**Требования:**
- Разные схемы для разных операций
- Валидация полей
- Примеры в схемах (для документации)

**Обязательные схемы:**

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class BookBase(BaseModel):
    """Базовая схема с общими полями."""
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=300)
    year: int = Field(..., ge=1000, le=2100)
    genre: str = Field(..., min_length=1, max_length=100)
    pages: int = Field(..., gt=0)


class BookCreate(BookBase):
    """Схема для создания книги."""
    isbn: str | None = Field(None, min_length=10, max_length=20)
    description: str | None = Field(None, max_length=5000)
    
    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        """Валидация формата ISBN."""
        if v is None:
            return v
        
        # Удалить дефисы
        clean = v.replace("-", "").replace(" ", "")
        
        # Проверить что только цифры (и X для ISBN-10)
        if not clean.replace("X", "").isdigit():
            raise ValueError("ISBN must contain only digits")
        
        # Проверить длину
        if len(clean) not in (10, 13):
            raise ValueError("ISBN must be 10 or 13 digits")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "isbn": "978-0132350884",
                    "description": "A Handbook of Agile Software Craftsmanship"
                }
            ]
        }
    }


class BookUpdate(BaseModel):
    """Схема для обновления книги (все поля опциональны)."""
    title: str | None = Field(None, min_length=1, max_length=500)
    author: str | None = Field(None, min_length=1, max_length=300)
    year: int | None = Field(None, ge=1000, le=2100)
    genre: str | None = Field(None, min_length=1, max_length=100)
    pages: int | None = Field(None, gt=0)
    available: bool | None = None
    isbn: str | None = None
    description: str | None = None


class ShowBook(BookBase):
    """Схема для отображения книги (response)."""
    book_id: UUID
    available: bool
    isbn: str | None
    description: str | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,  # Для ORM моделей
        "json_schema_extra": {
            "examples": [
                {
                    "book_id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "available": True,
                    "isbn": "978-0132350884",
                    "description": "A Handbook of Agile Software Craftsmanship",
                    "extra": {
                        "cover_url": "https://covers.openlibrary.org/b/id/123-L.jpg",
                        "subjects": ["Computer Science", "Software Engineering"]
                    },
                    "created_at": "2024-01-01T12:00:00",
                    "updated_at": "2024-01-01T12:00:00"
                }
            ]
        }
    }


class BookFilters(BaseModel):
    """Фильтры для поиска книг."""
    title: str | None = Field(None, description="Поиск по названию (частичное совпадение)")
    author: str | None = Field(None, description="Поиск по автору (частичное совпадение)")
    genre: str | None = Field(None, description="Точное совпадение жанра")
    year: int | None = Field(None, description="Точное совпадение года")
    available: bool | None = Field(None, description="Фильтр по доступности")
```

#### Создать `src/library_catalog/api/v1/schemas/common.py`

**Требования:**
- Схемы для пагинации
- Generic response models

```python
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Параметры пагинации."""
    page: int = Field(1, ge=1, description="Номер страницы")
    page_size: int = Field(20, ge=1, le=100, description="Размер страницы")
    
    @property
    def offset(self) -> int:
        """Вычислить offset для SQL."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Limit для SQL."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic схема для пагинированных ответов."""
    items: list[T]
    total: int = Field(..., description="Всего элементов")
    page: int = Field(..., description="Текущая страница")
    page_size: int = Field(..., description="Размер страницы")
    pages: int = Field(..., description="Всего страниц")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        pagination: PaginationParams,
    ):
        """Создать пагинированный ответ."""
        pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )


class HealthCheckResponse(BaseModel):
    """Схема для health check."""
    status: str = "healthy"
    database: str = "connected"
```

### Часть 5.2: Dependency Injection Container

#### Создать `src/library_catalog/api/dependencies.py`

**Требования:**
- Фабрики для создания сервисов
- Singleton для клиентов
- Правильное управление lifecycle

```python
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..data.repositories.book_repository import BookRepository
from ..domain.services.book_service import BookService
from ..external.openlibrary.client import OpenLibraryClient
from ..core.config import settings


# ========== EXTERNAL CLIENTS (Singletons) ==========

@lru_cache
def get_openlibrary_client() -> OpenLibraryClient:
    """
    Получить singleton OpenLibraryClient.
    
    lru_cache создает клиент один раз и переиспользует.
    """
    return OpenLibraryClient(
        base_url=settings.openlibrary_base_url,
        timeout=settings.openlibrary_timeout,
    )


# ========== REPOSITORIES ==========

async def get_book_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> BookRepository:
    """
    Создать BookRepository для текущей сессии БД.
    
    Создается новый экземпляр для каждого запроса.
    """
    return BookRepository(db)


# ========== SERVICES ==========

async def get_book_service(
    book_repo: Annotated[BookRepository, Depends(get_book_repository)],
    ol_client: Annotated[OpenLibraryClient, Depends(get_openlibrary_client)],
) -> BookService:
    """
    Создать BookService с внедренными зависимостями.
    
    FastAPI автоматически разрешит все зависимости:
    1. get_db() создаст AsyncSession
    2. get_book_repository() создаст BookRepository с session
    3. get_openlibrary_client() вернет singleton клиент
    4. Все внедрится в BookService
    """
    return BookService(
        book_repository=book_repo,
        openlibrary_client=ol_client,
    )


# ========== TYPE ALIASES ДЛЯ УДОБСТВА ==========

# Можно использовать в роутерах так:
# async def my_route(service: BookServiceDep):
BookServiceDep = Annotated[BookService, Depends(get_book_service)]
BookRepoDep = Annotated[BookRepository, Depends(get_book_repository)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db)]
```

### Часть 5.3: Роутеры (Endpoints)

#### Создать `src/library_catalog/api/v1/routers/books.py`

**Требования:**
- Тонкие роутеры (только HTTP логика)
- Правильные HTTP статус коды
- Подробная документация (docstrings)
- Все операции async

**Обязательные эндпоинты:**

```python
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ..schemas.book import (
    BookCreate,
    BookUpdate,
    ShowBook,
    BookFilters,
)
from ..schemas.common import PaginatedResponse, PaginationParams
from ...dependencies import BookServiceDep

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(
    "/",
    response_model=ShowBook,
    status_code=status.HTTP_201_CREATED,
    summary="Создать книгу",
    description="Создать новую книгу в каталоге с автоматическим обогащением из Open Library",
)
async def create_book(
    book_data: BookCreate,
    service: BookServiceDep,
):
    """
    Создать новую книгу.
    
    Автоматически обогащает данные из Open Library API:
    - Обложка книги
    - Темы/subjects
    - Издатель
    - Рейтинг
    
    Если Open Library недоступен, книга все равно будет создана.
    """
    return await service.create_book(book_data)


@router.get(
    "/",
    response_model=PaginatedResponse[ShowBook],
    summary="Получить список книг",
    description="Получить список книг с фильтрацией и пагинацией",
)
async def get_books(
    service: BookServiceDep,
    pagination: Annotated[PaginationParams, Depends()],
    title: str | None = Query(None, description="Поиск по названию"),
    author: str | None = Query(None, description="Поиск по автору"),
    genre: str | None = Query(None, description="Фильтр по жанру"),
    year: int | None = Query(None, description="Фильтр по году"),
    available: bool | None = Query(None, description="Фильтр по доступности"),
):
    """
    Получить список книг с фильтрацией.
    
    Поддерживаемые фильтры:
    - title: частичное совпадение (регистронезависимо)
    - author: частичное совпадение (регистронезависимо)
    - genre: точное совпадение
    - year: точное совпадение
    - available: True/False
    
    Пагинация:
    - page: номер страницы (начиная с 1)
    - page_size: размер страницы (1-100, по умолчанию 20)
    """
    books, total = await service.search_books(
        title=title,
        author=author,
        genre=genre,
        year=year,
        available=available,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    
    return PaginatedResponse.create(books, total, pagination)


@router.get(
    "/{book_id}",
    response_model=ShowBook,
    summary="Получить книгу",
    description="Получить информацию о конкретной книге по ID",
)
async def get_book(
    book_id: UUID,
    service: BookServiceDep,
):
    """
    Получить книгу по ID.
    
    Returns:
        ShowBook: Полная информация о книге
        
    Raises:
        404: Книга не найдена
    """
    return await service.get_book(book_id)


@router.patch(
    "/{book_id}",
    response_model=ShowBook,
    summary="Обновить книгу",
    description="Частичное обновление книги (передаются только изменяемые поля)",
)
async def update_book(
    book_id: UUID,
    book_data: BookUpdate,
    service: BookServiceDep,
):
    """
    Обновить книгу.
    
    Передаются только те поля, которые нужно изменить.
    Остальные поля остаются без изменений.
    
    Returns:
        ShowBook: Обновленная книга
        
    Raises:
        404: Книга не найдена
        400: Невалидные данные
    """
    return await service.update_book(book_id, book_data)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу",
    description="Удалить книгу из каталога",
)
async def delete_book(
    book_id: UUID,
    service: BookServiceDep,
):
    """
    Удалить книгу.
    
    Raises:
        404: Книга не найдена
    """
    await service.delete_book(book_id)
```

#### Создать `src/library_catalog/api/v1/routers/health.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.common import HealthCheckResponse
from ...dependencies import DbSessionDep

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Проверить состояние сервиса и подключение к БД",
)
async def health_check(db: DbSessionDep):
    """
    Проверить здоровье сервиса.
    
    Проверяет:
    - Сервис запущен
    - Подключение к БД работает
    """
    # Простой запрос к БД
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return HealthCheckResponse(
        status="healthy",
        database=db_status,
    )
```

### Часть 5.4: Главный файл приложения

#### Обновить `src/library_catalog/main.py`

**📝 ВАЖНОЕ ПРИМЕЧАНИЕ:**

В коде ниже используются функции, которые вам нужно реализовать самостоятельно:
- `dispose_engine()` - в файле `core/database.py` (для закрытия соединений с БД)
- `register_exception_handlers()` - в файле `core/exceptions.py` (для регистрации обработчиков ошибок)
- `setup_logging()` - в файле `core/logging_config.py` (для настройки логирования)

**Что нужно сделать:**

1. **`core/database.py`** - добавить функцию:
```python
async def dispose_engine() -> None:
    """Закрыть все соединения с БД."""
    await engine.dispose()
```

2. **`core/exceptions.py`** - создать файл с базовыми исключениями и функцией:
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    """Базовое исключение приложения."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundException(AppException):
    """Ресурс не найден."""
    def __init__(self, resource: str, identifier: any):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=404,
        )

def register_exception_handlers(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений."""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
```

3. **`core/logging_config.py`** - создать файл:
```python
import logging
import sys

def setup_logging() -> None:
    """Настроить логирование приложения."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
```

---

**Код `main.py`:**

```python
"""
Library Catalog API - Точка входа приложения.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import dispose_engine
from .core.exceptions import register_exception_handlers
from .core.logging_config import setup_logging
from .api.v1.routers import books, health


# ========== LIFECYCLE EVENTS ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager для FastAPI.
    
    Выполняется при:
    - startup: настройка логирования
    - shutdown: закрытие подключений к БД
    """
    # Startup
    setup_logging()
    print("🚀 Application started")
    
    yield
    
    # Shutdown
    await dispose_engine()
    print("👋 Application stopped")


# ========== CREATE APP ==========

app = FastAPI(
    title=settings.app_name,
    description="REST API для управления библиотечным каталогом",
    version="1.0.0",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)

# ========== MIDDLEWARE ==========

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== EXCEPTION HANDLERS ==========

register_exception_handlers(app)

# ========== ROUTERS ==========

# Версия 1 API
app.include_router(
    books.router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    health.router,
    prefix=settings.api_v1_prefix,
)

# ========== ROOT ENDPOINT ==========

@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "Welcome to Library Catalog API",
        "docs": settings.docs_url,
        "version": "1.0.0",
    }


# ========== RUN ==========

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
```

### Критерии приемки Задания 5

- [x] Pydantic схемы созданы с валидацией
- [x] Dependency Injection настроен
- [x] Все CRUD эндпоинты реализованы
- [x] Пагинация работает
- [x] Health check эндпоинт
- [x] Роутеры тонкие (делегируют сервису)
- [x] Swagger документация полная
- [x] Все методы async

**Проверка:**
```bash
# Запустить приложение
uvicorn src.library_catalog.main:app --reload

# Открыть Swagger
http://localhost:8000/docs

# Создать книгу через Swagger UI
# Проверить что обогащение работает
```

---

## ✅ КРИТЕРИИ УСПЕШНОСТИ ВСЕГО ПРОЕКТА

### Функциональные требования

- [ ] **CRUD операции** работают для книг
- [ ] **Поиск** работает по всем фильтрам
- [ ] **Пагинация** корректная
- [ ] **Обогащение** из Open Library работает
- [ ] **Валидация** бизнес-правил работает
- [ ] **Обработка ошибок** корректная (404, 400, 500)

### Технические требования

- [ ] **Архитектура:** 4 слоя (API, Domain, Data, External)
- [ ] **Async/await:** Используется везде
- [ ] **Dependency Injection:** Сервисы инжектятся через Depends
- [ ] **PostgreSQL:** Работает через async SQLAlchemy
- [ ] **Миграции:** Alembic настроен, миграции применены
- [ ] **Типизация:** Все функции типизированы
- [ ] **Документация:** Docstrings везде, Swagger полный
- [ ] **Логирование:** Структурированное, с уровнями
- [ ] **Конфигурация:** Через .env и Pydantic Settings

### Code Quality

- [ ] **Нет дублирования кода**
- [ ] **Правильные имена** (snake_case, PascalCase)
- [ ] **Короткие функции** (<50 строк)
- [ ] **Один файл = одна ответственность**
- [ ] **Нет бизнес-логики в роутерах**
- [ ] **Нет SQL в сервисах**

### Тестирование

- [ ] **Health check работает**
- [ ] **Ручное тестирование** через Swagger
- [ ] **БД подключение** проверяется
- [ ] **Open Library** клиент протестирован

---

## ⚠️ ТИПИЧНЫЕ ОШИБКИ И КАК ИХ ИЗБЕЖАТЬ

### Ошибка 1: Бизнес-логика в роутере

❌ **НЕПРАВИЛЬНО:**
```python
@router.post("/books")
async def create_book(book: BookCreate, db: AsyncSession = Depends(get_db)):
    # ❌ Валидация в роутере
    if book.year > 2024:
        raise HTTPException(400, "Invalid year")
    
    # ❌ Создание клиента в роутере
    ol_client = OpenLibraryClient()
    
    # ❌ Работа с БД напрямую
    db_book = Book(**book.dict())
    db.add(db_book)
    await db.commit()
```

✅ **ПРАВИЛЬНО:**
```python
@router.post("/books")
async def create_book(
    book: BookCreate,
    service: Annotated[BookService, Depends(get_book_service)],
):
    # ✅ Просто делегируем сервису
    return await service.create_book(book)
```

---

### Ошибка 2: Синхронный код вместо async

❌ **НЕПРАВИЛЬНО:**
```python
# Синхронная сессия
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Синхронный репозиторий
def get_book(self, book_id: UUID):
    return self.session.query(Book).filter(Book.book_id == book_id).first()
```

✅ **ПРАВИЛЬНО:**
```python
# Async сессия
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Async репозиторий
async def get_book(self, book_id: UUID):
    result = await self.session.get(Book, book_id)
    return result
```

---

### Ошибка 3: Hardcoded зависимости

❌ **НЕПРАВИЛЬНО:**
```python
def _create_book(data: BookCreate):
    # ❌ Создается внутри функции
    ol_client = OpenLibraryClient()
    repo = BookRepository(db)
    # ...
```

✅ **ПРАВИЛЬНО:**
```python
class BookService:
    def __init__(
        self,
        book_repo: BookRepository,  # ✅ Инжектится через DI
        ol_client: OpenLibraryClient,  # ✅ Инжектится через DI
    ):
        self.book_repo = book_repo
        self.ol_client = ol_client
```

---

### Ошибка 4: Дублирование маппинга

❌ **НЕПРАВИЛЬНО:**
```python
# В каждом методе одно и то же
return ShowBook(
    book_id=book.book_id,
    title=book.title,
    author=book.author,
    # ... 10 строк повторяются везде
)
```

✅ **ПРАВИЛЬНО:**
```python
# Один раз в маппере
class BookMapper:
    @staticmethod
    def to_show_book(book: Book) -> ShowBook:
        return ShowBook(...)

# Используем везде
return BookMapper.to_show_book(book)
```

---

### Ошибка 5: Плохая обработка ошибок

❌ **НЕПРАВИЛЬНО:**
```python
try:
    book = await repo.get(book_id)
except Exception:
    raise HTTPException(500, "Error")  # ❌ Неинформативно
```

✅ **ПРАВИЛЬНО:**
```python
book = await repo.get(book_id)
if book is None:
    raise BookNotFoundException(book_id)  # ✅ Специфичное исключение
```

---

### Ошибка 6: Нет типизации

❌ **НЕПРАВИЛЬНО:**
```python
def create_book(data):  # ❌ Нет типов
    return repo.create(data)
```

✅ **ПРАВИЛЬНО:**
```python
async def create_book(self, data: BookCreate) -> ShowBook:  # ✅ Типы везде
    book = await self.repo.create(**data.dict())
    return BookMapper.to_show_book(book)
```

---

### Ошибка 7: SQLAlchemy 1.x синтаксис

❌ **НЕПРАВИЛЬНО:**
```python
# Старый синтаксис SQLAlchemy 1.x
book_id = Column(String, primary_key=True)
```

✅ **ПРАВИЛЬНО:**
```python
# Новый синтаксис SQLAlchemy 2.0
book_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
)
```

---

### Ошибка 8: Забыли await

❌ **НЕПРАВИЛЬНО:**
```python
async def get_book(book_id):
    book = self.session.get(Book, book_id)  # ❌ Забыли await
    return book
```

✅ **ПРАВИЛЬНО:**
```python
async def get_book(book_id):
    book = await self.session.get(Book, book_id)  # ✅ С await
    return book
```

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ ЗАДАНИЯ (ПО ЖЕЛАНИЮ)


### Задание 7: Кэширование

Добавить кэширование для:
- Open Library запросов (Redis/in-memory)
- Результатов поиска книг

### Задание 8: Аутентификация

Добавить JWT аутентификацию:
- Регистрация/логин пользователей
- Защита эндпоинтов
- Роли (admin, user)

### Задание 9: Docker

Контейнеризация приложения:
- Dockerfile для API
- docker-compose для всего стека
- Multi-stage build

---

## 📖 ПОЛЕЗНЫЕ РЕСУРСЫ

### Официальная документация

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [httpx](https://www.python-httpx.org/)

### Статьи и туториалы

- Clean Architecture in Python
- Repository Pattern explained
- Dependency Injection in FastAPI
- Async SQLAlchemy best practices

### Open Library API

- [API Documentation](https://openlibrary.org/developers/api)
- [Search API](https://openlibrary.org/dev/docs/api/search)

---

## 🎓 ЧЕК-ЛИСТ ПЕРЕД СДАЧЕЙ

Пройдитесь по этому чек-листу перед сдачей проекта:

### Структура
- [ ] Все файлы на своих местах согласно структуре
- [ ] `__init__.py` во всех пакетах
- [ ] README.md заполнен

### Код
- [ ] Все функции async
- [ ] Везде type hints
- [ ] Docstrings в публичных методах
- [ ] Нет закомментированного кода
- [ ] Нет print() (используется logging)

### Архитектура
- [ ] 4 слоя разделены
- [ ] Нет циклических зависимостей
- [ ] DI используется правильно
- [ ] Repository Pattern применен

### База данных
- [ ] PostgreSQL запущен
- [ ] Миграции применены
- [ ] Индексы на нужных полях
- [ ] UUID как primary key

### API
- [ ] Все эндпоинты работают
- [ ] Swagger документация полная
- [ ] Правильные HTTP коды
- [ ] Валидация работает

### Тестирование
- [ ] Health check работает
- [ ] Вручную протестированы все операции
- [ ] Open Library интеграция работает

---

---

## 💡 СОВЕТЫ ПО ВЫПОЛНЕНИЮ

1. **Выполняйте поэтапно** - не пытайтесь сделать все сразу
2. **Тестируйте после каждого шага** - убедитесь что работает
3. **Коммитьте часто** - каждое задание = commit
4. **Читайте ошибки** - они многое говорят
5. **Используйте Swagger** - для тестирования API
6. **Логируйте** - добавляйте логи для отладки
7. **Спрашивайте** - если что-то непонятно

---

## 📞 ПОДДЕРЖКА

Если возникли вопросы:

1. **Перечитайте раздел** в ТЗ
2. **Посмотрите примеры** кода в ТЗ
3. **Проверьте логи** приложения
4. **Погуглите** ошибку
5. **Спросите ЧАТИК нашего сообщества**

**Частые вопросы:**

Q: Как запустить PostgreSQL?
A: `docker-compose up -d postgres`

Q: Как применить миграции?
A: `alembic upgrade head`

Q: Как посмотреть логи?
A: Они выводятся в консоль при запуске uvicorn

Q: Где Swagger?
A: http://localhost:8000/docs

Q: Как протестировать Open Library?
A: Через Python скрипт или Swagger UI

---

## 🎉 ЗАКЛЮЧЕНИЕ

Этот проект научит вас разрабатывать **правильные, масштабируемые, поддерживаемые** API приложения на FastAPI.

Вы освоите:
- ✅ Правильную архитектуру
- ✅ Работу с PostgreSQL
- ✅ Async программирование
- ✅ Интеграцию с внешними API
- ✅ Best practices Python разработки

**Успехов! 🚀**

---
