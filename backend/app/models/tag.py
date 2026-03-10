"""Модель тега книги."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tag(Base):
    """Тег: уникальное название."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    books: Mapped[list["Book"]] = relationship(
        "Book",
        secondary="book_tags",
        back_populates="tag_rels",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"Tag(id={self.id}, name={self.name!r})"
