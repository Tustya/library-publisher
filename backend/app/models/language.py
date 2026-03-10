"""Модель языка издания."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Language(Base):
    """Язык: уникальное название."""

    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    books: Mapped[list["Book"]] = relationship(
        "Book",
        back_populates="language_rel",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"Language(id={self.id}, name={self.name!r})"
