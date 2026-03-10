"""Модель возрастного рейтинга."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AgeRating(Base):
    """Возрастной рейтинг: код (0+, 6+, 12+, 16+, 18+)."""

    __tablename__ = "age_ratings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    books: Mapped[list["Book"]] = relationship(
        "Book",
        back_populates="age_rating_rel",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"AgeRating(id={self.id}, code={self.code!r})"
