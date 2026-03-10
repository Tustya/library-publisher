"""Модель жанра книги."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Genre(Base):
    """Жанр: уникальное название."""

    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    books: Mapped[list["Book"]] = relationship(
        "Book",
        back_populates="genre_rel",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"Genre(id={self.id}, name={self.name!r})"
