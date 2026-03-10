"""Модели доставки и бронирования."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.book import BookCopy

if TYPE_CHECKING:
    from app.models.user import User

# Типы статусов
DELIVERY_STATUS_ORDERED = "ordered"
DELIVERY_STATUS_IN_TRANSIT = "in_transit"
DELIVERY_STATUS_DELIVERED = "delivered"
DELIVERY_STATUS_RETURNING = "returning"

RESERVATION_STATUS_CREATED = "created"
RESERVATION_STATUS_ISSUED = "issued"
RESERVATION_STATUS_RETURNED = "returned"
RESERVATION_STATUS_CANCELLED = "cancelled"


class Delivery(Base):
    """Заказ доставки: адрес, дата пятницы, статус."""

    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation",
        back_populates="delivery",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        return f"Delivery(id={self.id}, user_id={self.user_id}, date={self.delivery_date})"


class Reservation(Base):
    """Бронь одной книги в заказе: экземпляр, статус, даты выдачи/возврата."""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_copy_id: Mapped[int] = mapped_column(
        ForeignKey("book_copies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    delivery: Mapped["Delivery"] = relationship(
        "Delivery", back_populates="reservations"
    )
    book_copy: Mapped["BookCopy"] = relationship("BookCopy", lazy="selectin")

    def __repr__(self) -> str:
        return f"Reservation(id={self.id}, delivery_id={self.delivery_id}, copy_id={self.book_copy_id})"
