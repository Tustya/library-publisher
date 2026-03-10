"""Модель автора книги."""

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Author(Base):
    """Автор: имя (для отображения), ФИО, псевдоним, даты, фото, инфо и биография."""

    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)

    first_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    middle_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pseudonym: Mapped[str | None] = mapped_column(String(500), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    short_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)

    books: Mapped[list["Book"]] = relationship(
        "Book",
        secondary="book_authors",
        back_populates="author_rels",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"Author(id={self.id}, name={self.name!r})"
