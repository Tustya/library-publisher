"""API очереди на книгу: встать в очередь, выйти из очереди."""

from datetime import UTC, datetime

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.book import Book, BookCopy
from app.models.book_queue import BookQueue
from app.models.delivery import (
    RESERVATION_STATUS_CREATED,
    RESERVATION_STATUS_ISSUED,
    Delivery,
    Reservation,
)
from app.models.user import User

router = APIRouter(prefix="/queue", tags=["queue"])

ACTIVE_RESERVATION_STATUSES = (RESERVATION_STATUS_CREATED, RESERVATION_STATUS_ISSUED)


async def _user_has_book(
    db: AsyncSession, user_id: int, book_id: int
) -> bool:
    copy_ids_stmt = select(BookCopy.id).where(BookCopy.book_id == book_id)
    copy_result = await db.execute(copy_ids_stmt)
    copy_ids = list(copy_result.scalars().all())
    if not copy_ids:
        return False
    stmt = (
        select(Reservation.id)
        .join(Delivery, Reservation.delivery_id == Delivery.id)
        .where(
            Delivery.user_id == user_id,
            Reservation.book_copy_id.in_(copy_ids),
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _book_has_available_copy(
    db: AsyncSession, book_id: int, reserved_copy_ids: set[int]
) -> bool:
    stmt = (
        select(BookCopy)
        .where(BookCopy.book_id == book_id)
        .where(
            BookCopy.status.isnot(None),
            BookCopy.status.ilike("%доступно%"),
        )
    )
    result = await db.execute(stmt)
    for copy in result.scalars().all():
        if copy.id not in reserved_copy_ids:
            return True
    return False


@router.post("/books/{book_id}")
async def join_queue(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Встать в очередь на книгу. Книга должна быть вся на руках, пользователь не в очереди и не с книгой."""
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    if await _user_has_book(db, current_user.id, book_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже держите эту книгу на руках",
        )
    existing = await db.execute(
        select(BookQueue).where(
            BookQueue.book_id == book_id,
            BookQueue.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже в очереди на эту книгу",
        )
    reserved_stmt = select(Reservation.book_copy_id).where(
        Reservation.status.in_(ACTIVE_RESERVATION_STATUSES)
    )
    reserved_result = await db.execute(reserved_stmt)
    reserved_ids = set(reserved_result.scalars().all())
    if await _book_has_available_copy(db, book_id, reserved_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Есть свободный экземпляр — оформите бронь",
        )
    now = datetime.now(UTC)
    entry = BookQueue(
        book_id=book_id,
        user_id=current_user.id,
        created_at=now,
    )
    db.add(entry)
    await db.flush()
    return {"ok": True, "message": "Вы встали в очередь на книгу"}


@router.delete("/books/{book_id}")
async def leave_queue(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Выйти из очереди на книгу."""
    stmt = select(BookQueue).where(
        BookQueue.book_id == book_id,
        BookQueue.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вы не в очереди на эту книгу",
        )
    await db.delete(entry)
    await db.flush()
    return {"ok": True, "message": "Вы вышли из очереди"}
