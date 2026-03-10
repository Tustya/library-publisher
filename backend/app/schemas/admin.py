"""Схемы для админ-API."""

from datetime import date, datetime

from pydantic import BaseModel


class AdminReservationItem(BaseModel):
    """Бронь для админ-списка."""

    id: int
    delivery_id: int
    book_id: int
    book_title: str
    book_author: str
    book_cover_url: str | None = None
    book_copy_id: int
    book_copy_number: str
    user_id: int
    user_phone: str
    user_name: str | None
    delivery_address: str
    delivery_date: date
    due_return_date: date
    status: str
    delivery_status: str
    created_at: datetime
    issued_at: datetime | None
    returned_at: datetime | None
    is_overdue: bool


class AdminOverdueItem(BaseModel):
    """Просроченный возврат."""

    reservation_id: int
    user_id: int
    user_phone: str
    user_name: str | None
    book_id: int
    book_title: str
    book_author: str
    book_copy_number: str
    due_return_date: date
    days_overdue: int


class AdminReaderItem(BaseModel):
    """Читатель для списка."""

    id: int
    phone: str
    first_name: str | None
    last_name: str | None
    patronymic: str | None
    delivery_address: str | None
    is_active: bool
    role: str

    model_config = {"from_attributes": True}
