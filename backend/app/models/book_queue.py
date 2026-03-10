"""Модель очереди на книгу: пользователь занимает место, когда все экземпляры выданы."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BookQueue(Base):
    """Очередь на книгу: book_id + user_id, порядок по created_at."""

    __tablename__ = "book_queue"
    __table_args__ = (UniqueConstraint("book_id", "user_id", name="uq_book_queue_book_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return f"BookQueue(id={self.id}, book_id={self.book_id}, user_id={self.user_id})"
