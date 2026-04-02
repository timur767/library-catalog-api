"""SQLAlchemy модель книги."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...core.database import Base


class Book(Base):
    """Модель книги в библиотечном каталоге."""

    __tablename__ = "books"

    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    author: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    genre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    pages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    isbn: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    extra: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Book(id={self.book_id}, title='{self.title}')>"
