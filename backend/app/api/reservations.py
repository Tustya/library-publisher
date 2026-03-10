"""API бронирования: создание заказа, список, отмена."""

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.helpers import format_authors_display
from app.core.library_rules import (
    MAX_ACTIVE_RESERVATIONS_PER_USER,
    can_order_for_next_friday,
    get_due_return_date,
    get_next_delivery_friday,
)
from app.models.book import Book, BookCopy
from app.models.delivery import (
    DELIVERY_STATUS_ORDERED,
    RESERVATION_STATUS_CANCELLED,
    RESERVATION_STATUS_CREATED,
    RESERVATION_STATUS_ISSUED,
    Delivery,
    Reservation,
)
from app.models.user import User
from app.schemas.reservation import (
    ReservationCreate,
    ReservationCreateResponse,
    ReservationItem,
    ReservationListResponse,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])

# Активные статусы брони (книга "на руках" или ожидает доставки)
ACTIVE_RESERVATION_STATUSES = (RESERVATION_STATUS_CREATED, RESERVATION_STATUS_ISSUED)


def _utc_now() -> datetime:
    return datetime.now(UTC)


@router.post("", response_model=ReservationCreateResponse)
async def create_reservation(
    payload: ReservationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReservationCreateResponse:
    """
    Оформить заказ на одну книгу.
    Адрес доставки берётся из профиля. Заказ принимается до 12:00 пятницы.
    """
    if not current_user.delivery_address or not current_user.delivery_address.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите адрес доставки в профиле",
        )
    can_order, msg = can_order_for_next_friday()
    if not can_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    # Количество активных броней пользователя
    active_count_stmt = (
        select(func.count(Reservation.id))
        .join(Delivery)
        .where(Delivery.user_id == current_user.id)
        .where(Reservation.status.in_(ACTIVE_RESERVATION_STATUSES))
    )
    active_result = await db.execute(active_count_stmt)
    active_count = active_result.scalar() or 0
    if active_count >= MAX_ACTIVE_RESERVATIONS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не более {MAX_ACTIVE_RESERVATIONS_PER_USER} активных броней. Верните или отмените текущие.",
        )

    # Найти книгу и один свободный экземпляр
    book_result = await db.execute(
        select(Book)
        .options(selectinload(Book.copies))
        .where(Book.id == payload.book_id)
    )
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )

    # ID экземпляров, уже забронированных (created/issued)
    reserved_copy_ids_stmt = (
        select(Reservation.book_copy_id).where(
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES)
        )
    )
    reserved_result = await db.execute(reserved_copy_ids_stmt)
    reserved_ids = set(reserved_result.scalars().all())

    available_copy = None
    for copy in book.copies:
        if copy.id in reserved_ids:
            continue
        if copy.status and "доступно" in copy.status.lower():
            available_copy = copy
            break
    if not available_copy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет доступных экземпляров этой книги",
        )

    delivery_date = get_next_delivery_friday()
    due_return = get_due_return_date(delivery_date)
    now = _utc_now()

    delivery = Delivery(
        user_id=current_user.id,
        address=current_user.delivery_address.strip(),
        delivery_date=delivery_date,
        status=DELIVERY_STATUS_ORDERED,
        created_at=now,
        updated_at=now,
    )
    db.add(delivery)
    await db.flush()

    reservation = Reservation(
        delivery_id=delivery.id,
        book_copy_id=available_copy.id,
        status=RESERVATION_STATUS_CREATED,
        created_at=now,
    )
    db.add(reservation)
    await db.flush()

    return ReservationCreateResponse(
        delivery_id=delivery.id,
        delivery_date=delivery_date,
        due_return_date=due_return,
        address=delivery.address,
        reservation_ids=[reservation.id],
        message="Заказ оформлен. Доставка в пятницу 17:00–18:00.",
    )


@router.get("", response_model=ReservationListResponse)
async def list_my_reservations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReservationListResponse:
    """Список броней текущего пользователя (активные и история)."""
    stmt = (
        select(Reservation)
        .join(Delivery)
        .where(Delivery.user_id == current_user.id)
        .options(
            selectinload(Reservation.delivery),
            selectinload(Reservation.book_copy)
            .selectinload(BookCopy.book)
            .selectinload(Book.author_rels),
        )
        .order_by(Reservation.created_at.desc())
    )
    result = await db.execute(stmt)
    reservations = list(result.scalars().unique().all())
    today = date.today()
    items = []
    for r in reservations:
        book = r.book_copy.book
        due = get_due_return_date(r.delivery.delivery_date)
        is_overdue = r.status == RESERVATION_STATUS_ISSUED and due < today
        items.append(
            ReservationItem(
                id=r.id,
                book_id=book.id,
                book_title=book.title,
                book_author=format_authors_display(book.author_rels),
                book_cover_url=book.cover_url,
                book_copy_id=r.book_copy_id,
                status=r.status,
                delivery_date=r.delivery.delivery_date,
                due_return_date=due,
                delivery_address=r.delivery.address,
                delivery_status=r.delivery.status,
                created_at=r.created_at,
                issued_at=r.issued_at,
                returned_at=r.returned_at,
                is_overdue=is_overdue,
            )
        )
    return ReservationListResponse(items=items, total=len(items))


@router.patch("/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Отменить бронь (только в статусе created)."""
    stmt = (
        select(Reservation)
        .join(Delivery)
        .where(
            Reservation.id == reservation_id,
            Delivery.user_id == current_user.id,
        )
    )
    result = await db.execute(stmt)
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронь не найдена",
        )
    if reservation.status != RESERVATION_STATUS_CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Можно отменить только оформленную бронь до выдачи",
        )
    reservation.status = RESERVATION_STATUS_CANCELLED
    await db.flush()
    return {"ok": True, "message": "Бронь отменена"}
