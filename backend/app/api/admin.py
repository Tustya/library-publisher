"""API административной панели."""

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.library_rules import get_due_return_date, get_next_delivery_friday
from app.helpers import format_authors_display
from app.models.age_rating import AgeRating
from app.models.author import Author
from app.models.book import Book, BookCopy
from app.models.book_queue import BookQueue
from app.models.delivery import (
    DELIVERY_STATUS_ORDERED,
    DELIVERY_STATUS_DELIVERED,
    RESERVATION_STATUS_CREATED,
    RESERVATION_STATUS_ISSUED,
    RESERVATION_STATUS_RETURNED,
    Delivery,
    Reservation,
)
from app.models.genre import Genre
from app.models.language import Language
from app.models.tag import Tag
from app.models.user import User
from app.schemas.admin import (
    AdminOverdueItem,
    AdminReaderItem,
    AdminReservationItem,
)
from app.schemas.book import (
    BookCopyCreate,
    BookCopyDetail,
    BookCopyUpdate,
    BookCreate,
    BookDetailWithCopies,
    BookUpdate,
    RefItem,
    TagCreate,
)

router = APIRouter(prefix="/admin", tags=["admin"])

ACTIVE_RESERVATION_STATUSES = (RESERVATION_STATUS_CREATED, RESERVATION_STATUS_ISSUED)


def _book_to_detail(book: Book) -> BookDetailWithCopies:
    """Собрать ответ книги из модели с загруженными связями."""
    return BookDetailWithCopies(
        id=book.id,
        author=format_authors_display(book.author_rels),
        title=book.title,
        description=book.description,
        cover_url=book.cover_url,
        genre=book.genre_rel.name if book.genre_rel else None,
        age_rating=book.age_rating_rel.code,
        language=book.language_rel.name,
        tags=[t.name for t in book.tag_rels] if book.tag_rels else None,
        author_ids=[a.id for a in book.author_rels] if book.author_rels else [],
        genre_id=book.genre_id,
        age_rating_id=book.age_rating_id,
        language_id=book.language_id,
        tag_ids=[t.id for t in book.tag_rels] if book.tag_rels else [],
        copies=[BookCopyDetail.model_validate(c) for c in book.copies],
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _user_display_name(u: User) -> str:
    parts = filter(None, [u.last_name, u.first_name, u.patronymic])
    return " ".join(parts) if parts else u.phone


# --- Books CRUD ---


@router.post("/books", response_model=BookDetailWithCopies)
async def create_book(
    payload: BookCreate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookDetailWithCopies:
    """Добавить книгу."""
    book = Book(
        title=payload.title,
        description=payload.description,
        cover_url=payload.cover_url,
        genre_id=payload.genre_id,
        age_rating_id=payload.age_rating_id,
        language_id=payload.language_id,
    )
    db.add(book)
    await db.flush()
    if payload.author_ids:
        result = await db.execute(
            select(Author).where(Author.id.in_(payload.author_ids))
        )
        book.author_rels = list(result.scalars().all())
    if payload.tag_ids:
        result = await db.execute(
            select(Tag).where(Tag.id.in_(payload.tag_ids))
        )
        book.tag_rels = list(result.scalars().all())
    await db.flush()
    await db.refresh(
        book,
        [
            "author_rels",
            "genre_rel",
            "age_rating_rel",
            "language_rel",
            "tag_rels",
            "copies",
        ],
    )
    return _book_to_detail(book)


@router.get("/books/{book_id}", response_model=BookDetailWithCopies)
async def get_admin_book(
    book_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookDetailWithCopies:
    """Карточка книги с экземплярами."""
    result = await db.execute(
        select(Book)
        .options(
            selectinload(Book.author_rels),
            selectinload(Book.genre_rel),
            selectinload(Book.age_rating_rel),
            selectinload(Book.language_rel),
            selectinload(Book.tag_rels),
            selectinload(Book.copies),
        )
        .where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    return _book_to_detail(book)


@router.patch("/books/{book_id}", response_model=BookDetailWithCopies)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookDetailWithCopies:
    """Редактировать книгу."""
    result = await db.execute(
        select(Book)
        .options(
            selectinload(Book.author_rels),
            selectinload(Book.genre_rel),
            selectinload(Book.age_rating_rel),
            selectinload(Book.language_rel),
            selectinload(Book.tag_rels),
            selectinload(Book.copies),
        )
        .where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    data = payload.model_dump(exclude_unset=True)
    author_ids = data.pop("author_ids", None)
    tag_ids = data.pop("tag_ids", None)
    for key, val in data.items():
        setattr(book, key, val)
    if author_ids is not None:
        result = await db.execute(
            select(Author).where(Author.id.in_(author_ids))
        )
        book.author_rels = list(result.scalars().all())
    if tag_ids is not None:
        result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        book.tag_rels = list(result.scalars().all())
    await db.flush()
    await db.refresh(
        book,
        [
            "author_rels",
            "genre_rel",
            "age_rating_rel",
            "language_rel",
            "tag_rels",
            "copies",
        ],
    )
    return _book_to_detail(book)


@router.post("/tags", response_model=RefItem)
async def create_tag(
    payload: TagCreate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RefItem:
    """Создать тег по имени или вернуть существующий (get-or-create)."""
    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Название тега не может быть пустым",
        )
    result = await db.execute(select(Tag).where(Tag.name == name))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
        await db.flush()
    return RefItem(id=tag.id, name=tag.name)


@router.delete("/books/{book_id}")
async def delete_book(
    book_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Удалить книгу (каскадно удалит экземпляры и связанные брони)."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    await db.delete(book)
    await db.flush()
    return {"ok": True, "message": "Книга удалена"}


# --- Copies (вложены в книгу) ---


@router.post("/books/{book_id}/copies", response_model=BookCopyDetail)
async def create_copy(
    book_id: int,
    payload: BookCopyCreate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookCopyDetail:
    """Добавить экземпляр к книге."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    existing = await db.execute(
        select(BookCopy).where(BookCopy.unique_number == payload.unique_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Экземпляр с таким номером уже существует",
        )
    copy = BookCopy(
        book_id=book_id,
        unique_number=payload.unique_number,
        status=payload.status,
        cover_url=payload.cover_url,
    )
    db.add(copy)
    await db.flush()
    await db.refresh(copy)
    return BookCopyDetail.model_validate(copy)


@router.patch("/copies/{copy_id}", response_model=BookCopyDetail)
async def update_copy(
    copy_id: int,
    payload: BookCopyUpdate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookCopyDetail:
    """Изменить статус или данные экземпляра."""
    result = await db.execute(select(BookCopy).where(BookCopy.id == copy_id))
    copy = result.scalar_one_or_none()
    if not copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Экземпляр не найден",
        )
    for key, val in payload.model_dump(exclude_unset=True).items():
        if key == "unique_number" and val is not None:
            existing = await db.execute(
                select(BookCopy).where(
                    BookCopy.unique_number == val, BookCopy.id != copy_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Экземпляр с таким номером уже существует",
                )
        setattr(copy, key, val)
    await db.flush()
    await db.refresh(copy)
    return BookCopyDetail.model_validate(copy)


@router.delete("/copies/{copy_id}")
async def delete_copy(
    copy_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Удалить экземпляр."""
    result = await db.execute(select(BookCopy).where(BookCopy.id == copy_id))
    copy = result.scalar_one_or_none()
    if not copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Экземпляр не найден",
        )
    await db.delete(copy)
    await db.flush()
    return {"ok": True, "message": "Экземпляр удалён"}


# --- Reservations & deliveries ---


@router.get("/reservations", response_model=list[AdminReservationItem])
async def list_admin_reservations(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AdminReservationItem]:
    """Список всех броней (для подтверждения выдачи/возврата)."""
    stmt = (
        select(Reservation)
        .options(
            selectinload(Reservation.delivery).selectinload(Delivery.user),
            selectinload(Reservation.book_copy)
            .selectinload(BookCopy.book)
            .selectinload(Book.author_rels),
        )
        .order_by(Reservation.created_at.desc())
    )
    result = await db.execute(stmt)
    reservations = list(result.unique().scalars().all())
    today = date.today()
    items = []
    for r in reservations:
        book = r.book_copy.book
        due = get_due_return_date(r.delivery.delivery_date)
        is_overdue = r.status == RESERVATION_STATUS_ISSUED and due < today
        items.append(
            AdminReservationItem(
                id=r.id,
                delivery_id=r.delivery_id,
                book_id=book.id,
                book_title=book.title,
                book_author=format_authors_display(book.author_rels),
                book_cover_url=book.cover_url,
                book_copy_id=r.book_copy_id,
                book_copy_number=r.book_copy.unique_number,
                user_id=r.delivery.user_id,
                user_phone=r.delivery.user.phone,
                user_name=_user_display_name(r.delivery.user),
                delivery_address=r.delivery.address,
                delivery_date=r.delivery.delivery_date,
                due_return_date=due,
                status=r.status,
                delivery_status=r.delivery.status,
                created_at=r.created_at,
                issued_at=r.issued_at,
                returned_at=r.returned_at,
                is_overdue=is_overdue,
            )
        )
    return items


@router.patch("/reservations/{reservation_id}/issue")
async def confirm_issue(
    reservation_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Подтвердить выдачу/доставку книги."""
    result = await db.execute(
        select(Reservation)
        .options(selectinload(Reservation.delivery))
        .where(Reservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронь не найдена",
        )
    if reservation.status != RESERVATION_STATUS_CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Выдача возможна только для брони в статусе «оформлена»",
        )
    now = _utc_now()
    reservation.status = RESERVATION_STATUS_ISSUED
    reservation.issued_at = now
    reservation.delivery.status = DELIVERY_STATUS_DELIVERED
    reservation.delivery.updated_at = now
    await db.flush()
    return {"ok": True, "message": "Выдача подтверждена"}


@router.patch("/reservations/{reservation_id}/return")
async def confirm_return(
    reservation_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Отметить возврат книги. Если есть очередь — первому в очереди создаётся бронь."""
    result = await db.execute(
        select(Reservation)
        .options(selectinload(Reservation.book_copy))
        .where(Reservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронь не найдена",
        )
    if reservation.status != RESERVATION_STATUS_ISSUED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Возврат возможен только для выданной книги",
        )
    now = _utc_now()
    reservation.status = RESERVATION_STATUS_RETURNED
    reservation.returned_at = now
    await db.flush()

    book_id = reservation.book_copy.book_id
    book_copy_id = reservation.book_copy_id
    assigned_message = "Возврат зафиксирован."
    while True:
        first_in_queue = await db.execute(
            select(BookQueue)
            .where(BookQueue.book_id == book_id)
            .order_by(BookQueue.created_at.asc())
            .limit(1)
        )
        queue_entry = first_in_queue.scalar_one_or_none()
        if not queue_entry:
            break
        next_user_result = await db.execute(
            select(User).where(User.id == queue_entry.user_id)
        )
        next_user = next_user_result.scalar_one_or_none()
        if next_user and next_user.delivery_address and next_user.delivery_address.strip():
            delivery_date = get_next_delivery_friday()
            delivery = Delivery(
                user_id=next_user.id,
                address=next_user.delivery_address.strip(),
                delivery_date=delivery_date,
                status=DELIVERY_STATUS_ORDERED,
                created_at=now,
                updated_at=now,
            )
            db.add(delivery)
            await db.flush()
            new_reservation = Reservation(
                delivery_id=delivery.id,
                book_copy_id=book_copy_id,
                status=RESERVATION_STATUS_CREATED,
                created_at=now,
            )
            db.add(new_reservation)
            await db.delete(queue_entry)
            await db.flush()
            assigned_message = (
                "Возврат зафиксирован. Книга оформлена на первого в очереди."
            )
            break
        await db.delete(queue_entry)
        await db.flush()

    return {"ok": True, "message": assigned_message}


# --- Overdue ---


@router.get("/overdue", response_model=list[AdminOverdueItem])
async def list_overdue(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AdminOverdueItem]:
    """Список просроченных возвратов: кто, книга, сколько дней."""
    today = date.today()
    stmt = (
        select(Reservation)
        .options(
            selectinload(Reservation.delivery).selectinload(Delivery.user),
            selectinload(Reservation.book_copy)
            .selectinload(BookCopy.book)
            .selectinload(Book.author_rels),
        )
        .where(Reservation.status == RESERVATION_STATUS_ISSUED)
    )
    result = await db.execute(stmt)
    reservations = list(result.unique().scalars().all())
    items = []
    for r in reservations:
        due = get_due_return_date(r.delivery.delivery_date)
        if due < today:
            days_overdue = (today - due).days
            user = r.delivery.user
            items.append(
                AdminOverdueItem(
                    reservation_id=r.id,
                    user_id=r.delivery.user_id,
                    user_phone=user.phone,
                    user_name=_user_display_name(user),
                    book_id=r.book_copy.book.id,
                    book_title=r.book_copy.book.title,
                    book_author=format_authors_display(r.book_copy.book.author_rels),
                    book_copy_number=r.book_copy.unique_number,
                    due_return_date=due,
                    days_overdue=days_overdue,
                )
            )
    items.sort(key=lambda x: x.days_overdue, reverse=True)
    return items


# --- Readers ---


@router.get("/readers", response_model=list[AdminReaderItem])
async def list_readers(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AdminReaderItem]:
    """Базовый список читателей."""
    stmt = select(User).order_by(User.id)
    result = await db.execute(stmt)
    users = list(result.scalars().all())
    return [AdminReaderItem.model_validate(u) for u in users]
