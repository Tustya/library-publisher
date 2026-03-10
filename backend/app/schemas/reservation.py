"""Схемы бронирования и доставки."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    """Создание брони: одна книга по book_id."""

    book_id: int = Field(..., gt=0, description="ID книги для брони")


class ReservationItem(BaseModel):
    """Одна бронь в списке: книга, статус, даты."""

    id: int
    book_id: int
    book_title: str
    book_author: str
    book_cover_url: str | None = None
    book_copy_id: int
    status: str
    delivery_date: date
    due_return_date: date
    delivery_address: str
    delivery_status: str
    created_at: datetime
    issued_at: datetime | None
    returned_at: datetime | None
    is_overdue: bool = False


class ReservationListResponse(BaseModel):
    """Список броней пользователя (активные и история)."""

    items: list[ReservationItem]
    total: int


class ReservationCreateResponse(BaseModel):
    """Ответ после создания заказа: доставка + брони."""

    delivery_id: int
    delivery_date: date
    due_return_date: date
    address: str
    reservation_ids: list[int]
    message: str
